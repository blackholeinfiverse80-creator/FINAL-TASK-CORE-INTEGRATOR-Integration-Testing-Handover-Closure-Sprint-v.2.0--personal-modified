from src.utils.insightflow import make_event


def test_make_event_minimal():
    e = make_event('heartbeat', 'bridge', 'healthy', details={'uptime_seconds': 1})
    assert e['event_type'] == 'heartbeat'
    assert e['component'] == 'bridge'
    assert 'timestamp' in e


def test_make_event_with_optional_fields():
    e = make_event('integration_ready', 'bridge', 'ready', integration_score=0.9, failing_components=['noopur'])
    assert e['integration_score'] == 0.9
    assert e['failing_components'] == ['noopur']
