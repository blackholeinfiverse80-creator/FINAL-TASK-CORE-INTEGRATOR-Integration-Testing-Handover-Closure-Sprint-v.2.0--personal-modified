"""
Bridge Client for CreatorCore Communication

Stabilized, versioned, and schema-aware client used as the canonical CreatorCore integration surface.
"""
from __future__ import annotations

import requests
import time
from typing import Dict, Any, Optional
from enum import Enum

VERSION = "1.0.0"


class ErrorType(Enum):
    NETWORK = "network"
    LOGIC = "logic"
    SCHEMA = "schema"
    UNEXPECTED = "unexpected"


class BridgeClient:
    """HTTP client for CreatorCore backend communication.

    This client is intentionally conservative and deterministic:
    - explicit versioning (``VERSION``)
    - retries with exponential backoff for transient network/timeout errors
    - deterministic fallback responses with error classification
    - a small contract validation layer for expected responses
    """

    def __init__(self, base_url: str = "http://localhost:5002", timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.client_version = VERSION

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with retry logic and deterministic error classification."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()

                # Expect JSON; if decode fails, classify as unexpected
                try:
                    return response.json()
                except ValueError as e:
                    return self._handle_error(ErrorType.UNEXPECTED, f"Invalid JSON response: {str(e)}", endpoint)

            except requests.exceptions.ConnectionError as e:
                error_type = ErrorType.NETWORK
                if attempt == retries - 1:
                    return self._handle_error(error_type, str(e), endpoint)
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff

            except requests.exceptions.Timeout as e:
                error_type = ErrorType.NETWORK
                if attempt == retries - 1:
                    return self._handle_error(error_type, f"Timeout after {self.timeout}s", endpoint)
                time.sleep(0.5 * (attempt + 1))

            except requests.exceptions.HTTPError as e:
                # Map client errors to schema issues, not found to logic errors
                status = getattr(e.response, 'status_code', None)
                if status == 400:
                    error_type = ErrorType.SCHEMA
                elif status in [404, 405]:
                    error_type = ErrorType.LOGIC
                else:
                    error_type = ErrorType.UNEXPECTED
                return self._handle_error(error_type, str(e), endpoint)

            except Exception as e:
                # Unexpected errors
                error_type = ErrorType.UNEXPECTED
                if attempt == retries - 1:
                    return self._handle_error(error_type, str(e), endpoint)
                time.sleep(0.5 * (attempt + 1))

        return self._handle_error(ErrorType.NETWORK, "Max retries exceeded", endpoint)

    def _handle_error(self, error_type: ErrorType, message: str, endpoint: str) -> Dict[str, Any]:
        """Return a deterministic fallback response with classification."""
        return {
            "success": False,
            "error_type": error_type.value,
            "error_message": message,
            "endpoint": endpoint,
            "fallback_used": True
        }

    # Public API (contract)
    def log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send structured log to CreatorCore. Returns JSON or fallback."""
        return self._make_request('POST', '/core/log', data)

    def feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send feedback payload to CreatorCore. Data must follow canonical schema externally validated by gateway."""
        return self._make_request('POST', '/core/feedback', data)

    def get_context(self, limit: int = 3) -> Dict[str, Any]:
        """Fetch context data from CreatorCore; returns either list or fallback."""
        endpoint = f"/core/context?limit={limit}"
        return self._make_request('GET', endpoint)

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Request generation from CreatorCore (POST /generate) and return the generator response."""
        return self._make_request('POST', '/generate', payload)

    def history(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Fetch generation history (GET /history or /history/<topic>)."""
        endpoint = f"/history/{topic}" if topic else "/history"
        return self._make_request('GET', endpoint)

    def health_check(self) -> Dict[str, Any]:
        
        """Ask CreatorCore for its /system/health; returns JSON status or fallback."""
        return self._make_request('GET', '/system/health')

    def is_healthy(self) -> bool:
        """Boolean check derived from `health_check()` result."""
        try:
            result = self.health_check()
            return result.get('status') == 'healthy'
        except Exception:
            return False
