import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings, read from environment variables so nothing is hard-coded."""

    database_url: str = "sqlite:///data/app.db"
    # Where the agent finds the MCP server. Empty means connect in-process, without HTTP.
    mcp_url: str = "http://127.0.0.1:8000/mcp"
    model: str = "claude-opus-5-5"
    effort: str = "medium"
    max_tokens: int = 64000
    # Agent loop safeguards.
    max_tool_rounds: int = 8
    tool_timeout_seconds: float = 20.0
    # Let the API re-run a request on another model if a safety classifier declines it.
    refusal_fallback: bool = True
    # Built frontend to serve, if it exists.
    web_dist: str = "web/dist"


def load_settings() -> Settings:
    env = os.environ
    defaults = Settings()
    return Settings(
        database_url=env.get("MTM_DATABASE_URL", defaults.database_url),
        mcp_url=env.get("MTM_MCP_URL", defaults.mcp_url),
        model=env.get("MTM_MODEL", defaults.model),
        effort=env.get("MTM_EFFORT", defaults.effort),
        max_tokens=int(env.get("MTM_MAX_TOKENS", defaults.max_tokens)),
        max_tool_rounds=int(env.get("MTM_MAX_TOOL_ROUNDS", defaults.max_tool_rounds)),
        tool_timeout_seconds=float(env.get("MTM_TOOL_TIMEOUT", defaults.tool_timeout_seconds)),
        refusal_fallback=env.get("MTM_REFUSAL_FALLBACK", "1") not in ("0", "false", ""),
        web_dist=env.get("MTM_WEB_DIST", defaults.web_dist),
    )
