from src.core.gateway import Gateway
from unittest.mock import Mock


def test_generate_to_generation_mapping(tmp_path, monkeypatch):
    gw = Gateway()
    # Use a temporary SQLite file for deterministic test
    from src.db.memory import ContextMemory
    db_path = str(tmp_path / 'test_context.db')
    gw.memory = ContextMemory(db_path)

    # Mock creator agent's bridge.generate to return generation_id
    creator = gw.agents['creator']
    creator.bridge = Mock()
    creator.bridge.generate.return_value = {
        'generation_id': 999,
        'generated_text': 'hello'
    }

    resp = gw.process_request(module='creator', intent='generate', user_id='user123', data={'prompt': 'hello'})
    # Ensure response contains generation_id
    assert resp['status'] == 'success'
    gen_id = resp['result'].get('generation_id')
    assert gen_id == 999

    # Debug: ensure interaction stored in memory
    history = gw.memory.get_user_history('user123')
    assert len(history) >= 1
    last = history[0]
    assert last['module'] == 'creator'
    assert last['response']['result']['generation_id'] == 999

    # Now check memory mapping
    mapping = gw.memory.get_generation(999)
    assert mapping is not None
    assert mapping['generation_id'] == '999'
    assert mapping['user_id'] == 'user123'
    assert mapping['interaction'] is not None
    assert mapping['interaction']['module'] == 'creator'
