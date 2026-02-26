from repobrain.topocore_lite import TopoCoreLite
from repobrain.tky_engine import EngineCandidate, EngineQuery, EngineRequest


def test_topocore_lite_selection_always_keeps_top1() -> None:
    req = EngineRequest(
        task_type="ask",
        query=EngineQuery(text="provider", signature=[1]),
        candidates=[
            EngineCandidate(chunk_id="top", score_local=0.001, signature=[1]),
            EngineCandidate(chunk_id="low2", score_local=0.0, signature=[2]),
        ],
        limits={"max_sources": 1, "min_score_keep": 0.5},
        policy={"corelocked": True},
    )

    decision = TopoCoreLite().decide(req)
    assert decision.selected_chunk_ids == ["top"]


def test_topocore_lite_selection_filters_low_score_background() -> None:
    engine = TopoCoreLite(min_sources=1)
    req = EngineRequest(
        task_type="ask",
        query=EngineQuery(text="provider", signature=[1]),
        candidates=[
            EngineCandidate(chunk_id="c1", score_local=0.12, signature=[1]),
            EngineCandidate(chunk_id="c2", score_local=0.05, signature=[2]),
            EngineCandidate(chunk_id="c3", score_local=0.03, signature=[3]),
            EngineCandidate(chunk_id="c4", score_local=0.01, signature=[4]),
            EngineCandidate(chunk_id="c5", score_local=0.0, signature=[5]),
        ],
        limits={"max_sources": 5, "min_score_keep": 0.02},
        policy={"corelocked": True},
    )

    decision = engine.decide(req)

    # keep_threshold=max(0.02, 0.12*0.30)=0.036, so c3/c4/c5 should be excluded
    assert decision.selected_chunk_ids == ["c1", "c2"]
