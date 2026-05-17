#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "impl_factory" / "05_custom_logic" / "custom_app" / "ai_assistant_ui"
if str(APP_PATH) not in sys.path:
	sys.path.insert(0, str(APP_PATH))

from ai_assistant_ui.qwen_chat.manual_uat_operator_evidence_cli import main  # noqa: E402


if __name__ == "__main__":
	raise SystemExit(main())
