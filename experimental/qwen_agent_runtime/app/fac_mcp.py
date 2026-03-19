from __future__ import annotations

from typing import Any, Dict

from app.settings import Settings


def build_fac_mcp_descriptor(settings: Settings) -> Dict[str, Any]:
	return settings.fac_mcp_config()
