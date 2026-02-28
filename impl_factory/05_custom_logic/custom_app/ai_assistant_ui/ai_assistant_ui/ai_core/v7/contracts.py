from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BusinessRequestSpec:
    intent: str = "READ"
    task_type: str = "detail"
    task_class: str = "analytical_read"
    domain: str = "unknown"
    subject: str = ""
    metric: str = ""
    dimensions: List[str] = field(default_factory=list)
    aggregation: str = "none"
    group_by: List[str] = field(default_factory=list)
    time_scope: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    top_n: int = 0
    output_contract: Dict[str, Any] = field(default_factory=dict)
    ambiguities: List[str] = field(default_factory=list)
    needs_clarification: bool = False
    confidence: float = 0.0


@dataclass
class ExecutionContext:
    session_name: str = ""
    user: str = ""
    message: str = ""
