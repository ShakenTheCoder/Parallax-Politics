Parallax AI: The Perception Operating System for Political Intelligence

1. Product Vision and Core Purpose

Parallax AI is a real-time perception operating system (OS) engineered for the adversarial high-stakes environment of Philippine politics. Designed for candidates, elected officials, and government leaders, the platform’s core promise is the delivery of strategic moves, not content generation. While legacy tools focus on publishing posts, Parallax AI advises leaders on how to maneuver through shifting public sentiment.

The system utilizes the CypherIntelligence methodology to transform "raw signal"—massive streams of ingested broadcast, digital, and social data—into "decision-grade intelligence." By employing a sophisticated multi-agent architecture, Parallax AI enables leaders to move beyond passive "social listening" into active agenda leadership and narrative control.


--------------------------------------------------------------------------------


2. The 9-Agent Architecture: Roles and Outputs

The system architecture is comprised of nine specialized autonomous agents that coordinate through a shared event bus and state store.

Agent Name	Primary Role	Core Output	Frequency
Collector	Multi-channel data ingestion and normalization	Normalized event stream	Continuous
Analyst	Multi-axis scoring (Emotion + Perception)	Leadership Perception Twin	Hourly Update
Narrator	Lifecycle tracking and velocity prediction	Narrative Radar	Every 30 min
Scout	Deep-parity competitive monitoring	Competitive Position	Hourly Scores
Sentinel	Forensic bot detection and network attribution	Network Intelligence	Continuous
Radar	Identifying unowned narrative territory	Agenda Intelligence	Daily/Weekly
Watcher	Threshold monitoring and crisis escalation	Risk Ledger	10–60 min
Strategist	Scenario simulation and maneuver planning	Action Cards	On-demand
Commander	Multi-surface synthesis and orchestration	Command/Intelligence Views	Real-time

Technical Breakdown of Agentic Layers

The Sensing Network (Collector): The Collector is the only agent permitted to touch raw external sources. It utilizes Whisper ASR for YouTube livestreams and Senate proceedings, speaker diarization to attribute quotes accurately, and OCR for chyrons/lower-thirds on broadcast TV (GMA, ABS-CBN, TV5).

* Inputs: TV/Broadcast, Press RSS, Social (FB, TikTok, YT, X, Reddit), and Behavioral velocity signals.
* Output: A normalized event stream containing metadata (author class, entities, reach proxies, and geography).

The Perception Engine (Analyst): The Analyst maintains the Perception Twin, a live state model of the principal. It scores events across eight specific emotions: Anger, Ridicule, Disappointment, Fatigue, Fear, Betrayal, Trust, and Pride.

* Strategic Insight: Ridicule is prioritized as more dangerous than anger; while a leader can survive criticism, ridicule hardens into an identity that is nearly impossible to recover from.
* Dimensions: Scores (-100 to +100) on Competence, Empathy, Integrity, Decisiveness, Maka-masa vs. Elitist, and Crisis Command.

The Story Tracker (Narrator): The Narrator tracks narratives from birth to "hardening" (consensus). It maps every story to the Media Loop stage to predict if a social media event will reach primetime television. It calculates velocity based on 6h/24h/72h growth rates.

Competitive Intelligence (Scout): The Scout applies the Analyst’s depth to 2–5 rivals. This creates a head-to-head gap analysis, identifying which rival "owns" specific narrative territory and predicting rival reactions (e.g., "82% probability rival visits flood area within 6h").

The Investigation Agent (Sentinel): The Sentinel executes a 5-step Attribution Chain to de-anonymize adversarial operations:

1. Detect: Identify inauthentic behaviors (account age, posting frequency).
2. Cluster: Group accounts into coordinated networks via temporal patterns.
3. Map: Track cluster activity across all monitored politicians.
4. Attribute: Assign a "sponsor fingerprint" based on the praise/attack ratio.
5. Quantify: Determine if negativity is bot-driven vs. organic. (Key for the Strategist: If 90% is organic, calling out "bots" is a tactical error).

Offensive Intelligence (Radar): The Radar identifies Unowned Topics, Competitor Blind Spots, and Emerging Issues. It serves as the offensive weapon, identifying where a leader can gain new territory before rivals react.

Threshold Monitoring (Watcher): The Watcher monitors 24/7 for three specific triggers:

* Watch (Yellow): Dimension drop >5 pts; Ridicule >15%.
* Warning (Orange): Dimension drop >10 pts; Narrative crosses from social to press.
* Critical (Red): Overall perception drop >15 pts; Viral content exceeds 500K hostile engagements; Ridicule >30%; Broadcast pickup of social-origin clips.

The Decision Engine (Strategist): The Strategist utilizes Historical Analog Retrieval, Time-Series Forecasting, and Constrained Response Simulation to produce Action Cards.

The Orchestrator (Commander): Synthesizes all inputs into dual surfaces. During a CRITICAL trigger, the Commander freezes all scheduled outgoing content, increases Watcher frequency to 10-minute cycles, and wakes the Strategist for emergency simulations.


--------------------------------------------------------------------------------


3. The 7 Decision Artifacts

1. Perception Map (Analyst + Collector): Identifies the weakest dimension (e.g., Empathy) that requires immediate correction.
2. Narrative Radar (Narrator): Detects forming stories and determines if they can be shaped before hardening.
3. Competitive Position (Scout): Quantifies gaps between the principal and rivals to find exploitable weaknesses.
4. Risk Ledger (Watcher): Provides a ranked list of threats with countdown timers to primetime hardening.
5. Scenario Matrix (Strategist): Projects the outcome of "Do Nothing" vs. "Written Statement" vs. "On-site Visit."
6. Action Card (Strategist + Commander): The specific "next move" answering 7 questions (What, Who, Where, When, How, Proof, Avoid), including a Confidence Score and Success KPIs.
7. Agenda Intelligence (Radar): Recommends unowned topics to talk about next to gain narrative territory.


--------------------------------------------------------------------------------


4. Dual-Delivery Interfaces: Command vs. Intelligence

Feature	Command View	Intelligence View
Target User	The Principal (Governor, Senator)	The Strategist (Campaign Manager)
Platform	Mobile-first	Desktop-first
Reading Time	~90 seconds	30–60 minutes
Core Content	Snapshot, Top Risks, and the Action Card	Full agent outputs, source trails, evidence chains
Guiding Principle	"Tell me what to do right now."	"Show me everything to build strategy."

Absolute Traceability: Every recommendation in the Command View includes a "drill-down" link to the raw evidence (e.g., specific clips, bot clusters, or cohort data) in the Intelligence View.


--------------------------------------------------------------------------------


5. Technical Engine: Reasoning and Learning Loops

Parallax AI is powered by the Hermes 4 hybrid reasoning model, which integrates structuring and self-reflective reasoning.

* Closed Learning Loop:
  1. Skill Persistence: Generates Markdown skill files to store the logic of complex tasks (e.g., attributing a specific regional bot network).
  2. Persistent Memory: Uses SQLite full-text search and LLM summarization for cross-session context, preventing "session amnesia."
  3. User Modeling: Employs Honcho dialectic modeling to learn the principal's specific voice, constraints, and historical patterns.
* Hybrid Reasoning Logic: The system uses DataForge (graph-based synthetic data) and Atropos (rejection sampling environment) to ensure high-quality strategic outputs.
* Behavioral Plasticity: To avoid "policy rigidity" (generic AI refusal), the system utilizes Chat Template Modification (changing the 'assistant' tag to 'me'). This allows for nuanced, in-character political simulations and reasoning traces up to a 30,000-token thinking budget.


--------------------------------------------------------------------------------


6. Regional Context: The Philippines Media Loop

The system is optimized for the high-velocity Philippine cycle, where the Media Loop (TV → Creator → Social → Press → TV) typically completes in 4–8 hours.

Platform	Reach (2026)	Loop Role
Facebook	~95.8M identities	Primary public square; where narratives go mainstream.
TikTok	~64M adults	Narrative birthplace; fastest amplification.
YouTube	~59.6M users	Long-form content and republished TV clips.
TV	High (via YouTube)	Sets evening agenda; primetime narrative hardening.
Online Press	High Credibility	Legitimization or debunking of social narratives.
X	~12M users	Political and media class agenda-setting.


--------------------------------------------------------------------------------


7. Ethical Guardrails and Compliance

Parallax AI functions as a "public-trust intelligence platform" with hard, system-level constraints:

* No Individual Voter Dossiers: All data is processed at the cohort/psychographic level.
* NPC Public-Data Compliance: Adheres to Philippine National Privacy Commission guidance; public visibility does not imply consent for private exploitation.
* No Astroturfing: The system is strictly prohibited from generating fake personas or synthetic grassroots movements.
* Campaign/Governance Separation: Maintains strict data and infrastructure silos between government duties and campaign operations.
* Human-in-the-loop: The system never autonomously posts or distributes content. It recommends maneuvers; humans execute.
