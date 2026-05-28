from __future__ import annotations
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

logger = logging.getLogger("golden_bot.lineage")

@dataclass
class LineageNode:
    step_id: str
    input_ids: List[str]
    output_ids: List[str]
    parameters: Dict[str, Any]
    code_hash: str
    timestamp: float

@dataclass
class LineagePath:
    nodes: List[LineageNode]
    root_to_leaf_hash: str

class DataLineageTracker:
    def __init__(self, storage_backend: Literal["json"] = "json", path: str = "data/lineage"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.graph: Dict[str, LineageNode] = {}

    def record_step(self, step_id: str, input_ids: List[str], output_ids: List[str], parameters: dict, code_hash: str) -> None:
        node = LineageNode(step_id, input_ids, output_ids, parameters, code_hash, time.time())
        self.graph[step_id] = node
        self._persist()

    def query_lineage(self, output_id: str) -> LineagePath:
        path_nodes = []
        current = output_id
        while current in self.graph:
            node = self.graph[current]
            path_nodes.append(node)
            current = node.input_ids[0] if node.input_ids else None
        return LineagePath(path_nodes, self._hash_chain(path_nodes))

    def detect_lineage_break(self, expected: LineagePath, actual: LineagePath) -> bool:
        return expected.root_to_leaf_hash != actual.root_to_leaf_hash

    def _persist(self) -> None:
        (self.path / "graph.json").write_text(json.dumps({k: asdict(v) for k,v in self.graph.items()}, indent=2))

    def _hash_chain(self, nodes: List[LineageNode]) -> str:
        h = "ROOT"
        for n in reversed(nodes):
            h = hashlib.sha256(f"{h}|{n.step_id}|{n.code_hash}".encode()).hexdigest()
        return h
