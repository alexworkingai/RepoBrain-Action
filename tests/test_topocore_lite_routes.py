from repobrain.topocore_lite import TopoCoreLite
from repobrain.tky_engine import EngineCandidate, EngineQuery, EngineRequest


def _req(scores: list[float], *, task_type: str = "ask") -> EngineRequest:
    candidates = [
        EngineCandidate(
            chunk_id=f"c{i}",
            score_local=score,
            signature=[i],
            file_path=f"repobrain/file_{i}.py",
            line_start=1,
            line_end=10,
        )
        for i, score in enumerate(scores, start=1)
    ]
    return EngineRequest(
        task_type=task_type,  # type: ignore[arg-type]
        query=EngineQuery(text="Where is TKYProvider?", signature=[1, 2, 3]),
        candidates=candidates,
        limits={"max_sources": 5, "min_score_keep": 0.02},
        policy={"corelocked": True},
    )


def test_topocore_lite_route_fast_for_strong_match() -> None:
    decision = TopoCoreLite().decide(_req([0.12, 0.03, 0.01]))
    assert decision.route == "FAST"
    assert decision.compression_stats["top_score"] > 0


def test_topocore_lite_route_deep_for_weak_match() -> None:
    decision = TopoCoreLite().decide(_req([0.01, 0.005, 0.0]))
    assert decision.route == "DEEP"
    assert decision.compression_stats["top_score"] <= 0.01
