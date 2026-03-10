from repobrain.rd_blockchain import InMemoryChainAdapter


def test_chain_append_is_idempotent_by_event_id() -> None:
    chain = InMemoryChainAdapter(chain_id="test")
    r1 = chain.append_event(
        event_id="evt-1",
        payload_hash="abc",
        signature="sig",
        timestamp=100,
    )
    r2 = chain.append_event(
        event_id="evt-1",
        payload_hash="abc",
        signature="sig",
        timestamp=200,
    )
    assert r1.chain_hash == r2.chain_hash
    assert chain.export_summary()["length"] == 1


def test_chain_summary_has_stable_shape() -> None:
    chain = InMemoryChainAdapter()
    chain.append_event(event_id="evt-1", payload_hash="h1", signature="s1", timestamp=1)
    chain.append_event(event_id="evt-2", payload_hash="h2", signature="s2", timestamp=2)
    summary = chain.export_summary()
    assert summary["length"] == 2
    assert isinstance(summary["head_hash"], str)
    assert isinstance(summary["event_ids_hash"], str)
