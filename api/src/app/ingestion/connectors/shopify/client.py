import asyncio
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.errors import AppError
from app.ingestion.connectors.shopify import queries

API_VERSION = "2026-07"
REQUIRED_SCOPES = {"read_orders", "read_products", "read_inventory", "read_locations"}
DOMAIN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.myshopify\.com")


def shop_domain(value: str) -> str:
    domain = value.strip().lower()
    if not DOMAIN.fullmatch(domain):
        raise ValueError("Use the store's name.myshopify.com domain, without https or a path.")
    return domain


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ShopifyClient:
    def __init__(self, domain: str, credentials: dict, version: str = API_VERSION):
        self.domain = shop_domain(domain)
        if version != API_VERSION:
            raise AppError(422, "API_VERSION_UNVERIFIED", "This API version is not verified.")
        self.version, self.credentials = version, credentials
        self.token = None
        self.expires_at = 0
        self.wait_until = 0

    def _request(self, path: str, body: bytes, headers: dict):
        request = Request(f"https://{self.domain}{path}", data=body, headers=headers, method="POST")
        try:
            with build_opener(NoRedirect()).open(request, timeout=15) as response:
                if path.endswith("graphql.json"):
                    if response.headers.get("X-Shopify-API-Version") != self.version:
                        raise AppError(
                            502, "API_VERSION_CHANGED", "Shopify used a different API version."
                        )
                content = response.read(8 * 1024 * 1024 + 1)
                if len(content) > 8 * 1024 * 1024:
                    raise AppError(
                        502, "SHOPIFY_RESPONSE_TOO_LARGE", "Shopify response exceeded the limit."
                    )
                return json.loads(content)
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise AppError(
                    403,
                    "CONNECTOR_REVOKED",
                    "Shopify rejected access. Check installation and permissions.",
                ) from None
            if exc.code == 429:
                error = AppError(
                    429, "SHOPIFY_THROTTLED", "Shopify is throttling requests. Retry later."
                )
                try:
                    error.retry_after = min(60, max(1, int(exc.headers.get("Retry-After", "2"))))
                except (TypeError, ValueError):
                    error.retry_after = 2
                raise error from None
            raise AppError(
                502, "SHOPIFY_UNAVAILABLE", "Shopify request failed. Retry later."
            ) from None
        except (URLError, TimeoutError, ValueError, OSError):
            raise AppError(
                502,
                "SHOPIFY_UNAVAILABLE",
                "Shopify could not be reached or returned an invalid response.",
            ) from None

    async def access_token(self):
        if self.credentials["auth_mode"] == "offline_token":
            return self.credentials["access_token"]
        if self.token and time.monotonic() < self.expires_at:
            return self.token
        result = await asyncio.to_thread(
            self._request,
            "/admin/oauth/access_token",
            urlencode(
                {
                    "grant_type": "client_credentials",
                    "client_id": self.credentials["client_id"],
                    "client_secret": self.credentials["client_secret"],
                }
            ).encode(),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not isinstance(result.get("access_token"), str) or not isinstance(
            result.get("expires_in"), int
        ):
            raise AppError(
                502, "SHOPIFY_AUTH_INVALID", "Shopify returned an invalid token response."
            )
        self.token = result["access_token"]
        self.expires_at = time.monotonic() + max(0, result["expires_in"] - 60)
        return self.token

    async def query(self, operation: str, variables: dict | None = None):
        for attempt in range(4):
            await asyncio.sleep(max(0, self.wait_until - time.monotonic()))
            try:
                token = await self.access_token()
                result = await asyncio.to_thread(
                    self._request,
                    f"/admin/api/{self.version}/graphql.json",
                    json.dumps({"query": operation, "variables": variables or {}}).encode(),
                    {"Content-Type": "application/json", "X-Shopify-Access-Token": token},
                )
            except AppError as exc:
                if exc.code == "SHOPIFY_THROTTLED" and attempt < 3:
                    await asyncio.sleep(max(2 ** (attempt + 1), getattr(exc, "retry_after", 0)))
                    continue
                raise
            errors = result.get("errors", [])
            if errors:
                codes = {e.get("extensions", {}).get("code") for e in errors}
                if codes == {"THROTTLED"} and attempt < 3:
                    await asyncio.sleep(2 ** (attempt + 1))
                    continue
                if "ACCESS_DENIED" in codes:
                    raise AppError(
                        403,
                        "SHOPIFY_SCOPE_MISSING",
                        "Shopify denied a field. Review the app's read permissions.",
                    )
                raise AppError(
                    502, "SHOPIFY_QUERY_FAILED", "Shopify could not complete the read query."
                )
            throttle = result.get("extensions", {}).get("cost", {}).get("throttleStatus", {})
            # These numbers are API quota units/time, never money.
            available, rate = throttle.get("currentlyAvailable", 0), throttle.get("restoreRate", 0)
            if rate:
                self.wait_until = time.monotonic() + min(30, max(0, (250 - available) / rate))
            if not isinstance(result.get("data"), dict):
                raise AppError(502, "SHOPIFY_RESPONSE_INVALID", "Shopify returned no data.")
            return result["data"]
        raise AppError(429, "SHOPIFY_THROTTLED", "Shopify is throttling requests. Retry later.")

    async def probe(self):
        result = await self.query(queries.PROBE)
        scopes = {s["handle"] for s in result["currentAppInstallation"]["accessScopes"]}
        if any(s.startswith("write_") for s in scopes):
            raise AppError(
                403, "SHOPIFY_WRITE_SCOPE_REJECTED", "Use a dedicated app with read-only scopes."
            )
        if not REQUIRED_SCOPES <= scopes:
            raise AppError(
                403,
                "SHOPIFY_SCOPE_MISSING",
                "Required scopes: read_orders, read_products, read_inventory, read_locations.",
            )
        shop = result["shop"]
        if shop["myshopifyDomain"].lower() != self.domain:
            raise AppError(403, "SHOPIFY_STORE_MISMATCH", "Shopify returned a different store.")
        return shop, sorted(scopes)
