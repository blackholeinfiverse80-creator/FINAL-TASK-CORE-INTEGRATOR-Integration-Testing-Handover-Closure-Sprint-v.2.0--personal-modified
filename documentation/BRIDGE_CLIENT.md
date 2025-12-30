# BridgeClient — Contract & Usage

Version: 1.0.0

Purpose
-------
BridgeClient is the canonical integration surface for CreatorCore operations (generate, feedback, history, log, health). It is the only supported pattern for CreatorCore interaction from the Gateway and routing layers.

Public methods
--------------
- `generate(payload: dict) -> dict` — calls POST `/generate` on CreatorCore and returns generator response. Should include `generation_id` where available.
- `feedback(payload: dict) -> dict` — calls POST `/feedback` with canonical feedback shape.
- `history(topic: Optional[str] = None) -> dict` — calls GET `/history`.
- `get_context(limit: int = 3) -> dict` — calls GET `/core/context`.
- `log(data: dict) -> dict` — calls POST `/core/log`.
- `health_check() -> dict` — calls GET `/system/health`.
- `is_healthy() -> bool` — boolean convenience wrapper.

Error handling
--------------
- All public APIs return either a JSON dict or a deterministic fallback dict with keys: `success`, `error_type`, `error_message`, `endpoint`, `fallback_used`.
- Error types are one of: `network`, `logic`, `schema`, `unexpected`.

Contract guarantees
-------------------
- The Gateway should treat `BridgeClient` responses as authoritative and must extract `generation_id` from the `generate` response when present. Generation metadata should be recorded persistently in the Gateway's mapping layer.

Notes
-----
This file documents the interface for BridgeClient v1.0.0; updates that change semantics must bump the version and record the change in `ARCHITECTURE_DECISION_RECORD.md`.