# SentioGate Python SDK (`sentiogate-python`)

[![PyPI version](https://img.shields.io/pypi/v/sentiogate-python?style=for-the-badge&color=3775a9&logo=pypi&logoColor=white)](https://pypi.org/project/sentiogate-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/sentiogate-python?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/sentiogate-python/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Website](https://img.shields.io/badge/Website-sentiogate.app-2563eb?style=for-the-badge&logo=google-chrome&logoColor=white)](https://sentiogate.app)
[![Live Benchmarks](https://img.shields.io/badge/Benchmarks-Live_Latency-7c3aed?style=for-the-badge&logo=speedtest&logoColor=white)](https://sentiogate.app/benchmarks)

Thin, zero-dependency Python client for [SentioGate](https://sentiogate.app) — the zero-markup, OpenAI-compatible LLM router for your own provider keys (BYOK). It picks a suitable model for each request and automatically falls back to another model if one fails.

* 🐍 **PyPI Package**: [`https://pypi.org/project/sentiogate-python/`](https://pypi.org/project/sentiogate-python/)
* 📦 **TypeScript SDK (NPM)**: [`https://www.npmjs.com/package/@sentiogate/sdk`](https://www.npmjs.com/package/@sentiogate/sdk)
* 🌐 **Developer Hub & Simulator**: [`https://sentiogate.github.io`](https://sentiogate.github.io)

---

## ⚡ Installation

```bash
pip install sentiogate-python
```

*(Zero external dependencies: uses Python standard library for maximum reliability and minimal container footprint).*

---

## 🚀 Quickstart

```python
import os
from sentiogate import AutoRouterClient

client = AutoRouterClient(
    api_key=os.environ.get("SENTIOGATE_API_KEY"),
)

response = client.chat(
    model="auto",  # SentioGate picks the model; cheapest suitable by default
    messages=[
        {"role": "system", "content": "You are a helpful software architect."},
        {"role": "user", "content": "What is the difference between gRPC and REST?"}
    ]
)

print(response["choices"][0]["message"]["content"])
```

---

## 🌊 Streaming Completions

```python
import os
from sentiogate import AutoRouterClient

client = AutoRouterClient(api_key=os.environ.get("SENTIOGATE_API_KEY"))

for chunk in client.stream_chat(
    model="auto",
    messages=[{"role": "user", "content": "Write a binary search in Python."}],
    extra_body={"route_preference": "latency"},  # "cost" (default), "quality" or "latency"
):
    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
    print(delta, end="", flush=True)
print()
```

---

## 🛠️ Routing preference

Send `model="auto"` and set `route_preference` through `extra_body` to `"cost"` (default), `"quality"` or
`"latency"`. You can also request a specific `provider/model`. SentioGate automatically falls back to another
model if one fails.

Retries are off by default. Set `max_retries` to retry transient 429s after the server's Retry-After
(the server may ask you to wait); waits longer than `max_retry_wait` raise `RouterClientError` instead.

---

## 🔗 Useful Links

* 🏠 [SentioGate Official Site](https://sentiogate.app)
* 📖 [API Documentation & Guides](https://sentiogate.app/docs)
* 📊 [Live Latency Benchmarks](https://sentiogate.app/benchmarks)
* ⚖️ [Comparison: SentioGate vs OpenRouter & LiteLLM](https://sentiogate.app/compare)
* 📦 [NPM Package (@sentiogate/sdk)](https://www.npmjs.com/package/@sentiogate/sdk)
* 🌐 [Developer Hub](https://sentiogate.github.io)
