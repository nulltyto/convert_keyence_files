from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class KeyenceFile:
    """Parsed Keyence microscope file data."""
    height: List[List[float]]
    optical: Optional[List[List[Tuple[int, int, int]]]]
    laser: Optional[List[List[int]]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_format: str = ""
