from unittest.mock import Mock
import requests
from src.utils.bridge_client import BridgeClient


def make_response(status_code=200, json_payload=None):
    mock = Mock()
    mock.status_code = status_code
    mock.json.return_value = json_payload or {"status": "ok"}
    def raise_for_status():
        if status_code >= 400:
            raise requests.exceptions.HTTPError(response=mock)
    mock.raise_for_status = Mock(side_effect=raise_for_status)
    return mock


class TestBridgeClient:
    def test_log_success(self, monkeypatch):
        client = BridgeClient("http://test-server")
        mock_post = make_response(200, {"status": "ok", "message": "logged"})
        monkeypatch.setattr(client.session, "post", Mock(return_value=mock_post))

        result = client.log({"msg": "hello"})
        assert result["status"] == "ok"
        assert result["message"] == "logged"

    def test_feedback_timeout_then_success(self, monkeypatch):
        client = BridgeClient("http://test-server", timeout=0.01)
        # First call raises Timeout, second succeeds
        timeout_exc = requests.exceptions.Timeout("timed out")
        good_resp = make_response(200, {"status": "received"})
        post_calls = [Mock(side_effect=timeout_exc), Mock(return_value=good_resp)]

        def side_effect(url=None, json=None, timeout=None):
            call = post_calls.pop(0)
            return call()

        monkeypatch.setattr(client.session, "post", Mock(side_effect=side_effect))

        result = client.feedback({"generation_id": 1})
        assert result["status"] == "received"

    def test_health_check_unreachable(self, monkeypatch):
        client = BridgeClient("http://test-server")
        # make get raise ConnectionError
        monkeypatch.setattr(client.session, "get", Mock(side_effect=requests.exceptions.ConnectionError("refused")))

        result = client.health_check()
        assert result.get("success") is False
        assert result.get("error_type") == "network"

    def test_is_healthy_false_on_exception(self, monkeypatch):
        client = BridgeClient("http://test-server")
        monkeypatch.setattr(client, "health_check", Mock(side_effect=Exception("boom")))
        assert client.is_healthy() is False
