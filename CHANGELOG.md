# Changelog: ai-auto-router-client

## 1.2.1 (unreleased)

Changed:
- Honest `User-Agent`: `SentioGate-Python/<version> (<OS>)`, e.g. `SentioGate-Python/1.2.1 (Darwin)`. 1.2.0 sent a
  fixed `Platform=Darwin` string whatever the OS. Override with `user_agent=` as before.

## 1.2.0 (2026-10-20)

Fixed:
- **Requests to https://api.sentiogate.dev were refused (HTTP 403, Cloudflare error 1010)** because urllib's
  default `User-Agent: Python-urllib/3.x` is blocked at the edge. The client now sends
  `User-Agent: ai-auto-router-client/1.2.0 (python; +https://sentiogate.app)` (override with `user_agent=`).
- `__version__` reported 1.0.0; it now matches the package version.
- `stream_chat` errors now parse the JSON body (was a raw string) and carry the code / Retry-After.
- `enqueue_batch` / `poll_batch` errors now include `status_code` and `code`.

Changed:
- Default `timeout` raised from 30 s to 130 s (`DEFAULT_TIMEOUT`), above the server's 120 s deadline for
  community-pool calls, so slow community answers no longer time out on the client.
- Apache-2.0 `LICENSE` now ships in the sdist and wheel.

Added (backwards compatible):
- `RouterClientError.code`, `.error_type`, `.retry_after` and `.retryable`.
- Opt-in retries: `AutoRouterClient(max_retries=..., max_retry_wait=60.0)`. Default `max_retries=0`
  (unchanged behaviour). Only transient 429s with a Retry-After are retried, after at least 1 s, never longer
  than `max_retry_wait`.
- `parse_retry_after`, `VERSION`, `USER_AGENT`, `RETRYABLE_CODES` exports.

Docs: community pool (single fixed model, BYOK exclusivity, Retry-After behaviour).

## 1.1.0

- Batch helpers (`enqueue_batch`, `poll_batch`); default base URL `https://api.sentiogate.dev`.
