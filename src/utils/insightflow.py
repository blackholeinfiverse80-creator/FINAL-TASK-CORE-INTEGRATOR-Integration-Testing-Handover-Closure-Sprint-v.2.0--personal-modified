"""InsightFlow telemetry payload generator

Produces deterministic, structured events suitable for InsightFlow ingestion and offline testing.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

INSIGHTFLOW_VERSION = "1.0.0"


def timestamp_iso(ts: Optional[datetime] = None) -> str:
    return (ts or datetime.now(timezone.utc)).isoformat()


def make_event(event_type: str, component: str, status: str, details: Dict[str, Any] = None,
               integration_score: Optional[float] = None, failing_components: Optional[List[str]] = None,
               timestamp: Optional[datetime] = None) -> Dict[str, Any]:
    payload = {
        "insightflow_version": INSIGHTFLOW_VERSION,
        "event_type": event_type,
        "component": component,
        "status": status,
        "details": details or {},
        "timestamp": timestamp_iso(timestamp)
    }
    if integration_score is not None:
        payload["integration_score"] = float(integration_score)
    if failing_components is not None:
        payload["failing_components"] = list(failing_components)
    return payload
