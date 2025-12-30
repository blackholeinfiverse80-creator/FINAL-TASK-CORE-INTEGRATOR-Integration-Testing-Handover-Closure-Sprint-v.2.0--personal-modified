from unittest.mock import Mock
from creator_routing import CreatorRouter


def test_prewarm_and_prepare_sets_generation_metadata(monkeypatch):
    router = CreatorRouter()
    router.bridge = Mock()
    # Simulate generate returning generated_text and generation_id
    router.bridge.generate.return_value = {"generated_text": "Hello", "generation_id": 555, "related_context": ["a"]}

    input_data = {"topic": "t1", "goal": "g1"}
    out = router.prewarm_and_prepare("request", "user1", input_data)
    assert "generation_metadata" in out
    assert out["generation_metadata"]["generation_id"] == 555
    assert out["generation_metadata"]["can_provide_feedback"] is True


def test_forward_feedback_forwards_to_bridge(monkeypatch):
    router = CreatorRouter()
    router.bridge = Mock()
    router.bridge.feedback.return_value = {"status": "received"}

    resp = router.forward_feedback({"generation_id": 123, "command": "+1"})
    assert resp["status"] == "received"
    router.bridge.feedback.assert_called_once()
