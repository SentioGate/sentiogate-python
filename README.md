# SentioGate Python SDK (`sentiogate`)

[![PyPI version](https://img.shields.io/pypi/v/sentiogate?style=for-the-badge&color=3775a9&logo=pypi&logoColor=white)](https://pypi.org/project/sentiogate/)
[![Python versions](https://img.shields.io/pypi/pyversions/sentiogate?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/sentiogate/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Website](https://img.shields.io/badge/Website-sentiogate.app-2563eb?style=for-the-badge&logo=google-chrome&logoColor=white)](https://sentiogate.app)
[![Live Benchmarks](https://img.shields.io/badge/Benchmarks-Live_Latency-7c3aed?style=for-the-badge&logo=speedtest&logoColor=white)](https://sentiogate.app/benchmarks)

Thin, zero-dependency Python client for [SentioGate](https://sentiogate.app) — the zero-markup AI LLM router offering intelligent latency-based routing, instant failover, and strict BYOK privacy.

* 🐍 **PyPI Package**: [`https://pypi.org/project/sentiogate/`](https://pypi.org/project/sentiogate/)
* 📦 **TypeScript SDK (NPM)**: [`https://www.npmjs.com/package/@sentiogate/sdk`](https://www.npmjs.com/package/@sentiogate/sdk)
* 🌐 **Developer Hub & Simulator**: [`https://sentiogate.github.io`](https://sentiogate.github.io)

---

## ⚡ Installation

```bash
pip install sentiogate
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

response = client.create_chat_completion(
    model="auto:fastest",  # Intelligently selects lowest TTFT model replica
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

for chunk in client.stream_chat_completion(
    model="auto:cost-efficient",
    messages=[{"role": "user", "content": "Write a binary search in Python."}],
):
    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
    print(delta, end="", flush=True)
print()
```

---

## 🔗 Useful Links

* 🏠 [SentioGate Official Site](https://sentiogate.app)
* 📖 [API Documentation & Guides](https://sentiogate.app/docs)
* 📊 [Live Latency Benchmarks](https://sentiogate.app/benchmarks)
* ⚖️ [Comparison: SentioGate vs OpenRouter & LiteLLM](https://sentiogate.app/compare)
* 📦 [NPM Package (@sentiogate/sdk)](https://www.npmjs.com/package/@sentiogate/sdk)
* 🌐 [Developer Hub](https://sentiogate.github.io)
