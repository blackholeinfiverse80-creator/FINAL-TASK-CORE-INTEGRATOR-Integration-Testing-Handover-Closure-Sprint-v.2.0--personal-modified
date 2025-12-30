import asyncio
from main import system_diagnostics, system_health


def test_system_diagnostics_contains_fields():
    data = asyncio.run(system_diagnostics())
    assert 'integration_ready' in data
    assert 'readiness_reason' in data
    assert 'failing_components' in data
    assert 'integration_score' in data
    assert 'timestamp' in data
    assert 'signature' in data


def test_system_health_contains_timestamp():
    data = asyncio.run(system_health())
    assert 'status' in data
    assert 'components' in data
    assert 'timestamp' in data