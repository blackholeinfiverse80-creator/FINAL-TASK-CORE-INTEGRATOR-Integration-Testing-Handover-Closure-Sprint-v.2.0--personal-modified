from typing import Dict, Any, List
from src.utils.bridge_client import BridgeClient
from config.config import INTEGRATOR_USE_NOOPUR


class CreatorRouter:
    """Routing helpers for CreatorCore flows (pre-prompt warming, feedback forwarding)."""

    def __init__(self, memory_adapter=None):
        self.memory = memory_adapter
        # BridgeClient is the canonical surface for CreatorCore communication
        self.bridge = BridgeClient() if INTEGRATOR_USE_NOOPUR else None

    def prewarm_and_prepare(self, request: str, user_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch related context and history, attach to input_data."""
        try:
            topic = input_data.get("topic") or input_data.get("data", {}).get("topic")
            goal = input_data.get("goal") or input_data.get("data", {}).get("goal")
            gen_type = input_data.get("type") or input_data.get("data", {}).get("type", "story")

            # Get history from external service for better context
            if self.bridge:
                try:
                    history_resp = self.bridge.history()
                    if isinstance(history_resp, list):
                        # Use recent history as additional context
                        recent_history = history_resp[:5]  # Last 5 generations
                        input_data.setdefault("recent_history", recent_history)
                except Exception:
                    pass

            # Generate with enhanced context
            if self.bridge and topic and goal:
                payload = {"topic": topic, "goal": goal, "type": gen_type}
                resp = self.bridge.generate(payload)
                related = resp.get("related_context", [])
                input_data.setdefault("related_context", related)
                
                # Store generation metadata to be deterministic at gateway level
                if "generated_text" in resp or "generation_id" in resp:
                    input_data.setdefault("generation_metadata", {
                        "source": "external",
                        "can_provide_feedback": True,
                        "generation_id": resp.get("generation_id")
                    })
                return input_data

            # Fallback: use local memory adapter
            if self.memory and user_id:
                ctx = self.memory.get_context(user_id, limit=3)
                input_data.setdefault("related_context", ctx)

        except Exception:
            return input_data

        return input_data

    def forward_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize and forward to Noopur feedback endpoint
        if not self.bridge:
            return {"status": "disabled"}
        # Try multiple payload shapes
        body = {}
        if "id" in payload and "feedback" in payload:
            body = {"id": payload["id"], "feedback": payload["feedback"]}
        elif "generation_id" in payload and "command" in payload:
            body = {"generation_id": payload["generation_id"], "command": payload["command"]}
        else:
            body = payload

        return self.bridge.feedback(body)
