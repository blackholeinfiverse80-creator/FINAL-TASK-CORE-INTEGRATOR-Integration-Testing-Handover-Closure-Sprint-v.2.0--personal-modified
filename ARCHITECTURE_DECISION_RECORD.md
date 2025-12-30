# ARCHITECTURE_DECISION_RECORD

Decision: OPTION A — Make BridgeClient a First-Class Integration Surface

Date: 2025-12-30

Summary
-------
We will stabilize and formalize the BridgeClient as the canonical integration surface to CreatorCore. BridgeClient will be versioned, schema-driven, and the official pipeline entry for Creator flows. All internal routing and gateway logic will depend on this single surface to eliminate dual-path confusion.

Rationale
---------
- The repository and test artifacts (coverage HTML, docs, and checklists) repeatedly reference a BridgeClient and demo scripts expect a `BridgeClient` API. Reinstating and stabilizing it preserves intended workflows and existing tests.
- A single, well-documented integration surface (BridgeClient) reduces ambiguity and enforces clear contracts for CreatorCore interactions, easing hand-off to Noopur and InsightFlow.
- Option B (removing the concept) risks breaking expected external flows and requires broader refactors across gateway, tests, and documentation.

Implementation Plan (High-level)
--------------------------------
1. Reintroduce `src/utils/bridge_client.py` as a stable, well-tested client (versioned, schema-enforcing, contract documented).
2. Update `creator_routing.py` to depend exclusively on BridgeClient for generate/feedback/context flows and ensure deterministic generation_id lifecycle persistent mapping.
3. Add deterministic mapping layer at Gateway (generation -> generation_id -> feedback -> retrieval) and unit tests (`test_feedback_flow_v2.py`).
4. Implement InsightFlow telemetry generator (structured JSON events) and add `/reports/insightflow_event_samples.json`.
5. Enhance `/system/diagnostics` and `/system/health` to include `readiness_reason`, `failing_components[]`, `timestamp`, and a numeric integration score; expose `/reports/final_readiness_matrix.json` and `/reports/final_ci_readiness.json`.
6. Final cleanup and handover docs for integrator and stakeholders.

Risks & Mitigation
------------------
- Risk: Hidden behavior in existing `creator_routing.py` expecting non-deterministic payloads. Mitigation: Add strict schema validation and backward compatibility adapter.
- Risk: Tests rely on mocked Bridge behavior. Mitigation: Add CI-safe mocks and a small real flow using `tests/mocks/creatorcore_mock.py`.

Acceptance Criteria
-------------------
- Single canonical BridgeClient implemented and documented.
- No remaining references to ambiguous dual-path behavior in code or docs.
- Deterministic generation_id lifecycle guaranteed and tested (`test_feedback_flow_v2.py`).
- InsightFlow-friendly telemetry samples available in `/reports`.
- `/system/diagnostics` and `/system/health` emit machine-consumable readiness fields.

Next steps
----------
- Add a working `src/utils/bridge_client.py` implementation and tests, wire it into `creator_routing.py`, and produce the required reports and docs.

Author: GitHub Copilot (acting per stakeholder instructions)
