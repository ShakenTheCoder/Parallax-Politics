"""NVIDIA NIM client wrapper.

Responsibilities:
- single async client (process-wide).
- pre-call cost reservation via TokenBudgetManager, post-call reconciliation.
- persists per-call telemetry to `llm_calls` table.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import structlog
from openai import AsyncOpenAI
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.db import session_scope
from app.llm.budget import TokenBudgetManager
from app.llm.router import (
    ModelSpec,
    ModelTier,
    estimate_cost_usd,
    model_by_id,
    pick_model,
)
from app.models.llm_call import LLMCall
from app.redis import get_redis

log = structlog.get_logger(__name__)


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float
    latency_ms: int
    raw: dict[str, Any] = field(default_factory=dict)
    json_payload: dict[str, Any] | None = None


_client: AsyncOpenAI | None = None


def _get_provider_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        s = get_settings()
        if s.llm_provider == "nvidia" and not s.nvidia_api_key:
            raise RuntimeError("NVIDIA_API_KEY is not set")
        api_key = s.nvidia_api_key if s.llm_provider == "nvidia" else s.ollama_api_key
        base_url = s.nvidia_base_url if s.llm_provider == "nvidia" else s.ollama_base_url
        _client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=s.llm_request_timeout_seconds,
        )
    return _client


def _build_system_message(
    system_prompt: str | list[dict[str, Any]],
) -> str:
    """Convert a string or pre-formed blocks into a system message string.
    NVIDIA NIM uses the standard OpenAI message format with system as a string.
    """
    if isinstance(system_prompt, str):
        return system_prompt
    # already structured -> concatenate text blocks
    parts: list[str] = []
    for b in system_prompt:
        if isinstance(b, dict) and "text" in b:
            parts.append(b["text"])
        elif isinstance(b, str):
            parts.append(b)
    return "\n".join(parts)


def _extract_usage(resp_usage: Any) -> tuple[int, int, int, int]:
    """Pull (input, output, cache_read, cache_write) from an OpenAI Usage."""
    in_tok = getattr(resp_usage, "prompt_tokens", 0) or 0
    out_tok = getattr(resp_usage, "completion_tokens", 0) or 0
    cr = 0  # NVIDIA free endpoint doesn't have cache billing
    cw = 0  # NVIDIA free endpoint doesn't have cache billing
    return in_tok, out_tok, cr, cw


def _extract_text(resp_choice: Any) -> str:
    """Extract text from OpenAI response choice."""
    if hasattr(resp_choice, "message") and hasattr(resp_choice.message, "content"):
        return resp_choice.message.content or ""
    return ""


class NVIDIAClient:
    """High-level wrapper. Inject `agent` + optional `run_id` for traceability."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.budget = TokenBudgetManager(get_redis())

    async def complete(
        self,
        *,
        agent: str,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tier: ModelTier = ModelTier.default,
        max_tokens: int = 1500,
        temperature: float = 0.4,
        run_id: UUID | str | None = None,
        json_mode: bool = False,
        stop_sequences: list[str] | None = None,
        cache_system: bool = True,
    ) -> LLMResponse:
        """Run a single completion with budget guarding + telemetry."""
        model = pick_model(tier, provider=self.settings.llm_provider)
        run_id_str = str(run_id) if run_id else None

        # --- Pre-flight cost estimate --------------------------------------
        # Heuristic: assume worst-case (full max_tokens output) so we never
        # under-reserve. Inputs estimated from prompt length / 4 (chars→tokens).
        approx_input = sum(len(json.dumps(m)) for m in messages) // 4 + (
            len(system) // 4 if isinstance(system, str) else 1500
        )
        cost_estimate = estimate_cost_usd(
            model,
            input_tokens=approx_input,
            output_tokens=max_tokens,
        )

        await self.budget.check_and_reserve(
            cost_estimate=cost_estimate,
            family=model.family,
            run_id=run_id_str,
        )

        try:
            resp, used_model_id = await self._call(
                model=model,
                system_message=_build_system_message(system),
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stop_sequences=stop_sequences,
            )
        except Exception:
            # Refund the reservation on hard failure.
            await self.budget.reconcile(
                estimated=cost_estimate,
                actual=0.0,
                family=model.family,
                run_id=run_id_str,
            )
            await self._record_call(
                run_id=run_id_str,
                agent=agent,
                model=model.id,
                in_tok=0,
                out_tok=0,
                cr=0,
                cw=0,
                cost=0.0,
                latency_ms=0,
                status="error",
            )
            raise

        in_tok, out_tok, cr, cw = _extract_usage(resp.usage)
        actual_cost = estimate_cost_usd(
            model_by_id(used_model_id) or model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_tokens=cr,
            cache_write_tokens=cw,
        )
        await self.budget.reconcile(
            estimated=cost_estimate,
            actual=actual_cost,
            family=model.family,
            run_id=run_id_str,
        )

        text = _extract_text(resp.choices[0]) if resp.choices else ""
        json_payload: dict[str, Any] | None = None
        if json_mode:
            json_payload = _safe_parse_json(text)

        latency_ms = (
            int((time.perf_counter() - resp.__dict__.get("__t0__", 0)) * 1000)
            if "__t0__" in resp.__dict__
            else 0
        )
        await self._record_call(
            run_id=run_id_str,
            agent=agent,
            model=used_model_id,
            in_tok=in_tok,
            out_tok=out_tok,
            cr=cr,
            cw=cw,
            cost=actual_cost,
            latency_ms=latency_ms,
            status="ok",
        )

        return LLMResponse(
            text=text,
            model=used_model_id,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_tokens=cr,
            cache_write_tokens=cw,
            cost_usd=actual_cost,
            latency_ms=latency_ms,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
            json_payload=json_payload,
        )

    # --- Internals ----------------------------------------------------------

    async def _call(
        self,
        *,
        model: ModelSpec,
        system_message: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        stop_sequences: list[str] | None,
    ) -> tuple[Any, str]:
        client = _get_provider_client()
        used_id = model.id

        # Build OpenAI format messages with system message first
        openai_messages = [{"role": "system", "content": system_message}]
        openai_messages.extend(messages)

        kwargs: dict[str, Any] = {
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": used_id,
        }
        if stop_sequences:
            kwargs["stop"] = stop_sequences

        async def _call(model_id: str) -> Any:
            t0 = time.perf_counter()
            resp = await client.chat.completions.create(**kwargs)
            resp.__dict__["__t0__"] = t0
            return resp

        try:
            async for attempt in AsyncRetrying(
                reraise=True,
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=0.5, max=4),
                retry=retry_if_exception_type(Exception),
            ):
                with attempt:
                    return await _call(used_id), used_id
        except Exception as e:
            # NVIDIA's hosted endpoint does not expose model fallback here
            # Just log and re-raise
            log.warning("llm.call_failed", model=used_id, err=str(e))
            raise

        # Should not reach here; AsyncRetrying always returns or raises.
        raise RuntimeError("unreachable")

    async def _record_call(
        self,
        *,
        run_id: str | None,
        agent: str,
        model: str,
        in_tok: int,
        out_tok: int,
        cr: int,
        cw: int,
        cost: float,
        latency_ms: int,
        status: str,
    ) -> None:
        try:
            async with session_scope() as db:
                db.add(
                    LLMCall(
                        run_id=UUID(run_id) if run_id else None,
                        agent=agent,
                        model=model,
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        cache_read_tokens=cr,
                        cache_write_tokens=cw,
                        cost_usd=cost,
                        latency_ms=latency_ms,
                        status=status,
                    )
                )
        except Exception as exc:
            log.warning("llm.telemetry.failed", error=str(exc))


def _safe_parse_json(text: str) -> dict[str, Any] | None:
    """Best-effort JSON extraction.

    Ignores any markdown fences or prose wrapping — directly scans for the
    outermost JSON object.  Robust against any fence variant (```json, ```,
    etc.) and models that add preamble text.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        log.warning(
            "llm.json_extract.no_braces",
            text_len=len(text),
            preview=text[:300],
        )
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        log.warning(
            "llm.json_extract.decode_error",
            error=str(exc),
            text_len=len(text),
            candidate_len=end - start + 1,
            preview=text[:300],
            tail=text[-300:],
        )
        return None


_singleton: NVIDIAClient | None = None


def get_llm_client() -> NVIDIAClient:
    global _singleton
    if _singleton is None:
        _singleton = NVIDIAClient()
    return _singleton
