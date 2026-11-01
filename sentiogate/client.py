"""AI Auto Router Client SDK.

Zero-inference-markup client for the AI Auto Router BYOK service.
Supports sync and streaming chat completions, model listing, provider health,
and cache operations. Outcome reporting, decisions, evaluations, session compaction and cluster
helpers are kept for compatibility only: the hosted gateway answers them with
``{"accepted": false, "status": "not_implemented"}`` and stores nothing.
"""

from __future__ import annotations

import email.utils
import json
import platform
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from typing import Any

VERSION = "1.2.1"
# Sent on every request: honest, names this SDK, its real version and the OS it runs on (never a browser string,
# never Python-urllib, which Cloudflare's browser integrity check refuses with error 1010).
USER_AGENT = f"SentioGate-Python/{VERSION} ({platform.system() or 'unknown'})"

# 429 codes that are worth retrying after the server's Retry-After (community-pool cooldown, per-key rate
# limit, upstream circuit). Quota codes such as community_pool_exhausted or monthly_request_limit are not.
RETRYABLE_CODES = frozenset({"upstream_rate_limited", "rate_limited", "upstream_circuit_open"})


def parse_retry_after(value: str | None, now: float | None = None) -> float | None:
    """Retry-After header -> seconds (delta-seconds or HTTP-date), or None when absent / unparseable."""
    if value is None or not str(value).strip():
        return None
    v = str(value).strip()
    try:
        return max(0.0, float(v))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(v)
    except (TypeError, ValueError, IndexError):
        return None
    if when is None:
        return None
    return max(0.0, when.timestamp() - (time.time() if now is None else now))


class RouterClientError(Exception):
    """Raised when the router returns an error or fails communication.

    ``code`` / ``error_type`` come from the JSON error body (e.g. ``upstream_rate_limited`` /
    ``rate_limit_error``); ``retry_after`` is the server's Retry-After in seconds, when sent.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
        code: str | None = None,
        error_type: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.code = code
        self.error_type = error_type
        self.retry_after = retry_after

    @property
    def retryable(self) -> bool:
        """True for a 429 the server asked us to retry later (Retry-After present, transient code)."""
        return self.status_code == 429 and self.retry_after is not None and (self.code in RETRYABLE_CODES)


def _http_error(exc: urllib.error.HTTPError, prefix: str) -> RouterClientError:
    try:
        body_str = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body_str = ""
    try:
        parsed: Any = json.loads(body_str)
    except Exception:
        parsed = body_str
    err = parsed.get("error") if isinstance(parsed, dict) else None
    err = err if isinstance(err, dict) else {}
    server_msg = err.get("message") or (parsed.get("detail") if isinstance(parsed, dict) else None)
    message = f"{prefix} {exc.code}: {exc.reason}" + (f" - {server_msg}" if isinstance(server_msg, str) else "")
    headers = getattr(exc, "headers", None)
    return RouterClientError(
        message,
        status_code=exc.code,
        response_body=parsed,
        code=err.get("code"),
        error_type=err.get("type"),
        retry_after=parse_retry_after(headers.get("Retry-After") if headers is not None else None),
    )


# Production SentioGate API (DEC-043). Host only: the client appends /v1/... itself.
DEFAULT_BASE_URL = "https://api.sentiogate.dev"
# Default request timeout (seconds): above the server's 120 s single-attempt deadline for community-pool calls.
DEFAULT_TIMEOUT = 130.0


class AutoRouterClient:
    """Thin, zero-leak client SDK for connecting applications to AI Auto Router.

    Retries are off by default (``max_retries=0``): a 429 raises ``RouterClientError`` with ``code`` and
    ``retry_after`` set. With ``max_retries > 0`` the client waits the server's Retry-After and tries again,
    only for transient 429 codes, never without a Retry-After, and never when the wait is longer than
    ``max_retry_wait`` seconds (the community pool can ask for up to 15 minutes).

    Example:
        >>> client = AutoRouterClient(api_key="sg_live_...")  # https://api.sentiogate.dev
        >>> resp = client.chat(
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     provider_keys={"openai": "sk-..."}
        ... )
        >>> print(resp["choices"][0]["message"]["content"])
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 0,
        max_retry_wait: float = 60.0,
        user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self.max_retry_wait = float(max_retry_wait)
        self.user_agent = user_agent or USER_AGENT
        self._sleep: Callable[[float], None] = time.sleep

    def _headers(self, custom: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if custom:
            headers.update(custom)
        return headers

    def _should_retry(self, err: RouterClientError, attempt: int) -> bool:
        if not err.retryable or attempt >= self.max_retries:
            return False
        wait = float(err.retry_after or 0)
        if wait > self.max_retry_wait:
            return False
        self._sleep(max(1.0, wait))  # never a hot loop: at least 1 s, and only what the server asked for
        return True

    def chat(
        self,
        messages: list[dict[str, Any]],
        model: str = "auto",
        provider_keys: dict[str, str] | None = None,
        user_id: str = "default_user",
        difficulty: float | None = None,
        mode: str | None = None,
        constraints: dict[str, Any] | None = None,
        plugins: list[dict[str, Any]] | None = None,
        router_metadata: bool = True,
        tier: str = "free",
        hedging_mode: str | None = None,  # deprecated no-op: ignored by the gateway
        hedge_delay_ms: int | None = None,  # deprecated no-op: ignored by the gateway
        cache: bool = False,
        cache_bypass: bool = False,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request to the router.

        ``hedging_mode`` and ``hedge_delay_ms`` are deprecated and ignored: providers are tried one at a
        time with fallback. They are still forwarded so existing callers keep working.
        """
        url = f"{self.base_url}/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "user_id": user_id,
            "provider_keys": provider_keys or {},
            "tier": tier,
            "cache": cache,
        }
        if hedging_mode is not None:
            payload["hedging_mode"] = hedging_mode
        if hedge_delay_ms is not None:
            payload["hedge_delay_ms"] = hedge_delay_ms
        if difficulty is not None:
            payload["difficulty"] = difficulty
        if mode is not None:
            payload["mode"] = mode
        if constraints is not None:
            payload["constraints"] = constraints
        if plugins is not None:
            payload["plugins"] = plugins
        if router_metadata:
            payload["router_metadata"] = True
        if extra_body:
            payload.update(extra_body)

        extra_headers: dict[str, str] = {}
        if router_metadata:
            extra_headers["X-Router-Metadata"] = "enabled"
        if cache_bypass:
            extra_headers["X-Cache-Bypass"] = "true"
        if extra_body and (extra_body.get("allow_queue") or extra_body.get("allowQueue")):
            extra_headers["X-SentioGate-Allow-Queue"] = "true"

        data = json.dumps(payload).encode("utf-8")
        req_headers = self._headers(extra_headers if extra_headers else None)
        req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")

        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_bytes = resp.read()
                    return json.loads(resp_bytes.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                err = _http_error(exc, "Router HTTP")
                if exc.code == 202 and isinstance(err.response_body, dict):
                    return err.response_body
                if self._should_retry(err, attempt):
                    attempt += 1
                    continue
                raise err from None
            except Exception as exc:
                raise RouterClientError(f"Router request failed: {exc}") from exc

    def enqueue_batch(
        self,
        messages: list[dict[str, Any]] | None = None,
        item_text: str | None = None,
        model: str = "sentiogate-community",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Enqueue an asynchronous batch inference task."""
        url = f"{self.base_url}/v1/batch/enqueue"
        payload: dict[str, Any] = {"model": model}
        if messages is not None:
            payload["messages"] = messages
        if item_text is not None:
            payload["item_text"] = item_text
        if extra:
            payload.update(extra)

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err = _http_error(exc, "Enqueue batch HTTP")
            if exc.code == 202 and isinstance(err.response_body, dict):
                return err.response_body
            err.args = (f"Enqueue batch failed ({exc.code}): {err.response_body}",)
            raise err from None

    def poll_batch(self, job_id: str) -> dict[str, Any]:
        """Poll status and output of an enqueued batch job."""
        clean_id = job_id.replace("/api/batch/poll/", "").replace("/v1/batch/poll/", "")
        url = f"{self.base_url}/v1/batch/poll/{clean_id}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err = _http_error(exc, "Poll batch HTTP")
            err.args = (f"Poll batch failed ({exc.code}): {err.response_body}",)
            raise err from None

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model: str = "auto",
        provider_keys: dict[str, str] | None = None,
        user_id: str = "default_user",
        difficulty: float | None = None,
        mode: str | None = None,
        constraints: dict[str, Any] | None = None,
        plugins: list[dict[str, Any]] | None = None,
        tier: str = "free",
        extra_body: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Stream chat completion chunks (SSE) from the router.

        Errors (429 ``upstream_rate_limited`` with Retry-After, 403 ``community_pool_disabled_with_byok``, ...)
        arrive as an HTTP status before the first chunk and raise ``RouterClientError`` with ``code`` and
        ``retry_after``; ``max_retries`` applies only before any chunk has been yielded.
        """
        url = f"{self.base_url}/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "user_id": user_id,
            "provider_keys": provider_keys or {},
            "stream": True,
            "tier": tier,
        }
        if difficulty is not None:
            payload["difficulty"] = difficulty
        if mode is not None:
            payload["mode"] = mode
        if constraints is not None:
            payload["constraints"] = constraints
        if plugins is not None:
            payload["plugins"] = plugins
        if extra_body:
            payload.update(extra_body)

        data = json.dumps(payload).encode("utf-8")
        req_headers = self._headers({"Accept": "text/event-stream"})
        req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")

        attempt = 0
        while True:
            try:
                resp_cm = urllib.request.urlopen(req, timeout=self.timeout)
            except urllib.error.HTTPError as exc:
                err = _http_error(exc, "Router stream HTTP")
                if self._should_retry(err, attempt):
                    attempt += 1
                    continue
                raise err from None
            except Exception as exc:
                raise RouterClientError(f"Router stream failed: {exc}") from exc
            break
        try:
            with resp_cm as resp:
                for line in resp:
                    decoded = line.decode("utf-8").strip()
                    if decoded.startswith("data: "):
                        raw_data = decoded[6:].strip()
                        if raw_data == "[DONE]":
                            break
                        try:
                            yield json.loads(raw_data)
                        except json.JSONDecodeError:
                            continue
        except RouterClientError:
            raise
        except Exception as exc:
            raise RouterClientError(f"Router stream failed: {exc}") from exc

    def report_outcome(
        self,
        request_id: str,
        signals: dict[str, bool],
        provider: str | None = None,
        task_class: str | None = None,
    ) -> dict[str, Any]:
        """Compatibility only: the hosted gateway answers ``accepted: false``; nothing is stored or used for routing."""
        url = f"{self.base_url}/v1/outcomes"
        payload = {
            "request_id": request_id,
            "signals": signals,
            "provider": provider,
            "task_class": task_class,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to report outcome: {exc}") from exc

    def evaluate_decision(
        self,
        state: dict[str, Any],
        questions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compatibility only: decisions are not available on the hosted gateway (answers ``accepted: false``)."""
        url = f"{self.base_url}/v1/decisions"
        payload = {"state": state, "questions": questions}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to evaluate decision: {exc}") from exc

    def list_models(self) -> list[dict[str, Any]]:
        """List available models and meta-routers from the registry."""
        url = f"{self.base_url}/v1/models"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("data", [])
        except Exception as exc:
            raise RouterClientError(f"Failed to list models: {exc}") from exc

    def get_benchmarks(self) -> list[dict[str, Any]]:
        """Fetch open public provider benchmarks dataset."""
        url = f"{self.base_url}/v1/benchmarks"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("benchmarks", [])
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch benchmarks: {exc}") from exc

    def get_session_handoff(self, session_id: str) -> dict[str, Any]:
        """Fetch active session handoff summary and state."""
        url = f"{self.base_url}/v1/sessions/{session_id}/handoff"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch session handoff: {exc}") from exc

    def compact_session(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        """Compatibility only: nothing is compacted or stored (answers ``accepted: false, compacted: false``)."""
        url = f"{self.base_url}/v1/sessions/{session_id}/compact"
        payload = {"messages": messages, "user_id": user_id}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to compact session: {exc}") from exc

    def list_custom_providers(self, user_id: str = "default_user") -> list[dict[str, Any]]:
        """List registered custom OpenAI-compatible providers."""
        url = f"{self.base_url}/v1/custom-providers?user_id={urllib.parse.quote(user_id)}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("data", [])
        except Exception as exc:
            raise RouterClientError(f"Failed to list custom providers: {exc}") from exc

    def register_custom_provider(
        self,
        provider_id: str,
        display_name: str,
        base_url: str,
        api_key: str | None = None,
        api_type: str = "openai_compatible",
        models: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        """Register or update a custom OpenAI-compatible provider."""
        url = f"{self.base_url}/v1/custom-providers"
        payload = {
            "provider_id": provider_id,
            "display_name": display_name,
            "base_url": base_url,
            "api_key": api_key,
            "api_type": api_type,
            "models": models or [],
            "headers": headers or {},
            "user_id": user_id,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to register custom provider: {exc}") from exc

    def delete_custom_provider(self, provider_id: str, user_id: str = "default_user") -> dict[str, Any]:
        """Delete a registered custom provider."""
        enc_id = urllib.parse.quote(provider_id)
        enc_user = urllib.parse.quote(user_id)
        url = f"{self.base_url}/v1/custom-providers/{enc_id}?user_id={enc_user}"
        req = urllib.request.Request(url, headers=self._headers(), method="DELETE")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to delete custom provider: {exc}") from exc

    def get_cache_stats(self) -> dict[str, Any]:
        """Fetch router cache hit/miss statistics and entry counts."""
        url = f"{self.base_url}/v1/cache/stats"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch cache stats: {exc}") from exc

    def clear_cache(self, user_id: str | None = None) -> dict[str, Any]:
        """Flush cache entries."""
        url = f"{self.base_url}/v1/cache"
        if user_id:
            url += f"?user_id={urllib.parse.quote(user_id)}"
        req = urllib.request.Request(url, headers=self._headers(), method="DELETE")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to clear cache: {exc}") from exc

    def get_evaluations(self, limit: int = 50, task_class: str | None = None) -> list[dict[str, Any]]:
        """Compatibility only: shadow evaluations are not available on the hosted gateway; returns an empty list."""
        url = f"{self.base_url}/v1/evaluations?limit={limit}"
        if task_class:
            url += f"&task_class={urllib.parse.quote(task_class)}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("evaluations", [])
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch evaluations: {exc}") from exc

    def fork_evaluation(
        self,
        primary: dict[str, Any],
        shadow: dict[str, Any],
        task_class: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Compatibility only: shadow evaluations are not available on the hosted gateway (answers ``accepted: false``)."""
        url = f"{self.base_url}/v1/evaluations/fork"
        payload = {
            "primary": primary,
            "shadow": shadow,
            "task_class": task_class,
            "request_id": request_id,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fork evaluation: {exc}") from exc

    def get_cluster_health(self) -> dict[str, Any]:
        """Compatibility only: cluster status is not available on the hosted gateway; use GET /health for liveness."""
        url = f"{self.base_url}/v1/cluster/health"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch cluster health: {exc}") from exc

    def broadcast_cluster_breaker(
        self, provider: str, reason: str = "manual_override", error_rate: float = 1.0, ttl_seconds: float = 60.0
    ) -> dict[str, Any]:
        """Compatibility only: manual breaker control is not available on the hosted gateway (answers ``accepted: false``)."""
        url = f"{self.base_url}/v1/cluster/breakers"
        payload = {
            "provider": provider,
            "reason": reason,
            "error_rate": error_rate,
            "ttl_seconds": ttl_seconds,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to broadcast cluster breaker: {exc}") from exc

    def get_capacity_pool(self) -> dict[str, Any]:
        """Fetch real-time dynamic free capacity pool status and scarcity metrics."""
        url = f"{self.base_url}/v1/capacity"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch capacity pool: {exc}") from exc

    def redeem_license(self, code: str, user_id: str = "local") -> dict[str, Any]:
        """Redeem AppSumo / lifetime deal license voucher code."""
        url = f"{self.base_url}/v1/licenses/redeem"
        data = json.dumps({"code": code, "user_id": user_id}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to redeem license: {exc}") from exc

    def get_user_license(self, user_id: str = "local") -> dict[str, Any]:
        """Fetch active license voucher details for a user."""
        url = f"{self.base_url}/v1/licenses/user/{urllib.parse.quote(user_id)}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch user license: {exc}") from exc

    def get_edge_status(self) -> dict[str, Any]:
        """Fetch Cloudflare Edge proxy and Turnstile configuration status."""
        url = f"{self.base_url}/v1/edge/status"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to fetch edge status: {exc}") from exc

    def verify_turnstile(self, token: str) -> dict[str, Any]:
        """Verify Cloudflare Turnstile token via backend edge verification."""
        url = f"{self.base_url}/v1/edge/turnstile/verify"
        data = json.dumps({"token": token}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise RouterClientError(f"Failed to verify turnstile token: {exc}") from exc
