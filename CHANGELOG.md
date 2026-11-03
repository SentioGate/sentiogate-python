# Changelog: sentiogate-python

> Renamed from `ai-auto-router-client`.

## 1.3.0 (2026-11-03)

Breaking:
- Removed `get_cluster_health()` and `broadcast_cluster_breaker()`. Cluster coordination is not part of the hosted
  gateway (these always answered `accepted: false`).
- Removed `get_edge_status()` and `verify_turnstile()`. They served the SentioGate web app's sign-in page, not API users.
- Removed `evaluate_decision()`, `get_evaluations()` and `fork_evaluation()` (internal tooling; the hosted gateway
  stored nothing).
- `clear_cache()` no longer takes `user_id`; it always flushes the signed-in account's own cache (the server already
  ignored the parameter).

Changed:
- `User-Agent` is now `sentiogate-python/<version> (<OS>)`. Override with `user_agent=` as before.
- Docs: Quickstart now uses the real `chat()` / `stream_chat()` methods, `model="auto"` and `route_preference`
  (the `auto:fastest` / `auto:cost-efficient` aliases shown before never existed). Removed unverified claims.

## 1.2.1

Changed:
- Honest `User-Agent` with the real version and OS. 1.2.0 sent a fixed `Platform=Darwin` string whatever the OS.

## 1.2.0 (2026-10-20)

Fixed:
- **Requests to https://api.sentiogate.dev were refused (HTTP 403)** because urllib's default
  `User-Agent: Python-urllib/3.x` is refused by the gateway's bot check. The client now sends its own
  `User-Agent` (override with `user_agent=`).
- `__version__` reported 1.0.0; it now matches the package version.
- `stream_chat` errors now parse the JSON body (was a raw string) and carry the code / Retry-After.
- `enqueue_batch` / `poll_batch` errors now include `status_code` and `code`.

Changed:
- Default `timeout` raised from 30 s to 130 s (`DEFAULT_TIMEOUT`), so long-running requests no longer time out
  on the client.
- Apache-2.0 `LICENSE` now ships in the sdist and wheel.

Added (backwards compatible):
- `RouterClientError.code`, `.error_type`, `.retry_after` and `.retryable`.
- Opt-in retries: `AutoRouterClient(max_retries=..., max_retry_wait=60.0)`. Default `max_retries=0`
  (unchanged behaviour). Only transient 429s with a Retry-After are retried, after at least 1 s, never longer
  than `max_retry_wait`.
- `parse_retry_after`, `VERSION`, `USER_AGENT`, `RETRYABLE_CODES` exports.

Docs: free community pool (BYOK exclusivity, Retry-After behaviour).

## 1.1.0

- Batch helpers (`enqueue_batch`, `poll_batch`); default base URL `https://api.sentiogate.dev`.
