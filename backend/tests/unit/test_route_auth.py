from fastapi.routing import APIRoute

from app.main import app


def _dependency_names(route: APIRoute) -> set[str]:
    names: set[str] = set()

    def visit(dependant) -> None:
        for child in dependant.dependencies:
            names.add(getattr(child.call, "__name__", type(child.call).__name__))
            visit(child)

    visit(route.dependant)
    return names


def test_every_non_login_api_route_requires_authentication() -> None:
    exceptions = {("POST", "/api/v1/auth/login")}
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/v1/"):
            continue
        dependency_names = _dependency_names(route)
        for method in route.methods:
            if (method, route.path) in exceptions:
                continue
            assert dependency_names & {"get_current_user", "require_admin"}, (
                f"{method} {route.path} has no authentication dependency"
            )
