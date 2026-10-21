from dataclasses import asdict, dataclass, field
from src.contracts import COST_MODEL
from .schema import validate_payload

@dataclass

class SolverMetrics:
    search_time_s: float = 0.0
    peak_memory_bytes: int = 0
    expanded_nodes: int = 0
    solution_length: int | None = None
    solution_cost: int | None = None

@dataclass
class SolverResult:
    map_id: str | None
    algorithm: str
    status: str
    start_state: dict | None
    actions: list[str] | None
    metrics: SolverMetrics
    timeout_s: float | None
    heuristic: str | None = None
    error: str | None = None
    schema_version: int = field(default=1, init=False)
    cost_model: str = field(
      default=COST_MODEL, init=False
    )


    def to_dict(self) -> dict:
        payload = asdict(self)
        validate_payload(payload)
        return payload

from src.engine.serialization import snapshot_to_dict
