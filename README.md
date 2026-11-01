# SentioGate Python SDK (`sentiogate`)

[![PyPI version](https://img.shields.io/pypi/v/sentiogate?style=flat-square&color=blue)](https://pypi.org/project/sentiogate/)
[![Python versions](https://img.shields.io/pypi/pyversions/sentiogate?style=flat-square)](https://pypi.org/project/sentiogate/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat-square)](https://opensource.org/licenses/Apache-2.0)
[![Website](https://img.shields.io/badge/Website-sentiogate.app-2563eb?style=flat-square)](https://sentiogate.app)
[![Live Benchmarks](https://img.shields.io/badge/Benchmarks-Live_Latency-7c3aed?style=flat-square)](https://sentiogate.app/benchmarks)

Thin, zero-dependency Python client for [SentioGate](https://sentiogate.app) — the zero-markup AI LLM router offering intelligent latency-based routing, instant failover, and strict BYOK privacy.

---

## ⚡ Installation

```bash
pip install sentiogate
```

*(Zero external dependencies: uses Python standard library `urllib` / `http.client` for maximum reliability and minimal container footprint).*

---

## 🚀 Quickstart

```python
import os
from sentiogate import SentioGate

client = SentioGate(
    api_key=os.environ.get("SENTIOGATE_API_KEY"),
    # Optional: zero-markup Bring-Your-Own-Key provider credentials
    provider_keys={
        "openai": os.environ.get("OPENAI_API_KEY"),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
    }
)

response = client.chat.completions.create(
    model="auto:fastest",  # Intelligently selects lowest TTFT model replica
    messages=[
        {"role": "system", "content": "You are a helpful software architect."},
        {"role": "user", "content": "What is the difference between gRPC and REST?"}
    ]
)

print(response.choices[0].message.content)
```

---

## 🌊 Streaming Completions

```python
stream = client.chat.completions.create(
    model="auto:cost-efficient",
    messages=[{"role": "user", "content": "Write a binary search in Python."}],
    stream=True
)

for chunk in stream:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)
print()
```

---

## 🔗 Useful Links

* 🏠 [SentioGate Official Site](https://sentiogate.app)
* 📖 [API Documentation & Guides](https://sentiogate.app/docs)
* 📊 [Live Latency Benchmarks](https://sentiogate.app/benchmarks)
* ⚖️ [Comparison: SentioGate vs OpenRouter & LiteLLM](https://sentiogate.app/compare)
* 🌐 [TypeScript / JavaScript SDK](https://github.com/SentioGate/sentiogate-js)
