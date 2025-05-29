from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from cpr_langgraph_agent.models import Customer, ConsumptionPoint, Contract, Payment

__all__ = ["AsyncCrmClient", "APIError"]


class APIError(Exception):
    """Raised when the API returns an unsuccessful HTTP status code."""

class AsyncCrmClient:
    """Asynchronous client for the Mock REST server REST API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float | httpx.Timeout = 10,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Create a new client instance.

        Parameters
        ----------
        base_url:
            The root URL of the REST service, e.g. ``"https://api.example.com"``.
        timeout:
            Request timeout passed directly to ``httpx.AsyncClient``.
        headers:
            Optional default headers added to every outgoing request (for
            example authentication tokens).
        """
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url, timeout=timeout, headers=headers
        )

    # ---------------------------------------------------------------------
    # Async context management helpers
    # ---------------------------------------------------------------------
    async def __aenter__(self) -> "AsyncMockRestClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying ``httpx.AsyncClient`` instance."""
        await self._client.aclose()

    # ---------------------------------------------------------------------
    # Internal routine
    # ---------------------------------------------------------------------
    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Perform an HTTP request and return parsed response data."""
        response = await self._client.request(method, url, params=params)
        if response.is_error:
            raise APIError(f"{response.status_code} {response.text}")

        # Attempt to parse JSON automatically; otherwise return raw text.
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return response.text

    # ---------------------------------------------------------------------
    # Auto‑generated endpoint helpers (all GET in this spec)
    # ---------------------------------------------------------------------

    async def get_customer_by_email(self, email: str) -> Customer:
        """GET ``/customers/by_email``.

        Parameters
        ----------
        email: str
            Customer e‑mail address (required).
        """
        response = await self._request("GET", "/customers/by_email", params={"email": email})
        return Customer(**response)

    async def get_customer_consumption_points(
        self,
        customer_id: int,
        *,
        product_family: Optional[str] = None,
    ) -> List[ConsumptionPoint]:
        """GET ``/customers/{customer_id}/consumption_points``.

        Parameters
        ----------
        customer_id: int
            Numeric customer identifier.
        product_family: str | None
            Optional product family filter.
        """
        params: Dict[str, Any] = {}
        if product_family is not None:
            params["product_family"] = product_family

        response = await self._request(
            "GET",
            f"/customers/{customer_id}/consumption_points",
            params=params or None,
        )
        return [ConsumptionPoint(**item) for item in response]

    async def get_customer_contracts(
        self,
        customer_id: str
    ) -> List[Contract]:
        """GET ``/customers/{customer_id}/contracts``."""
        response = await self._request(
            "GET",
            f"/customers/{customer_id}/contracts",
        )
        return [Contract(**item) for item in response]

    async def get_contract_payments(
        self,
        customer_id: str,
        contract_id: str,
    ) -> List[Payment]:
        """GET ``/customers/customer/{customer_id}/contracts/{contract_id}/payments``."""
        response = await self._request(
            "GET",
            f"/customers/customer/{customer_id}/contracts/{contract_id}/payments",
        )
        return [Payment(**item) for item in response]