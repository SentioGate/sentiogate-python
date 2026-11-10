"""Stdlib-only unit tests: python -m unittest discover -s tests"""

import json
import unittest
import urllib.request
from unittest import mock

import sentiogate
from sentiogate import AutoRouterClient, VERSION


class _Resp:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ClientTests(unittest.TestCase):
    def test_version_and_user_agent(self):
        self.assertEqual(sentiogate.__version__, VERSION)
        self.assertTrue(sentiogate.USER_AGENT.startswith(f"sentiogate-python/{VERSION} ("))

    def test_default_base_url(self):
        self.assertEqual(AutoRouterClient().base_url, "https://api.sentiogate.dev")

    def test_validate_base_url_scheme(self):
        with self.assertRaises(ValueError):
            AutoRouterClient(base_url="file:///etc/passwd")
        with self.assertRaises(ValueError):
            AutoRouterClient(base_url="ftp://evil.com")
        with self.assertRaises(ValueError):
            AutoRouterClient(base_url="not-a-url")

    def test_internal_methods_removed(self):
        client = AutoRouterClient()
        for name in (
            "get_cluster_health",
            "broadcast_cluster_breaker",
            "get_edge_status",
            "verify_turnstile",
            "evaluate_decision",
            "get_evaluations",
            "fork_evaluation",
        ):
            self.assertFalse(hasattr(client, name), name)

    def test_clear_cache_is_caller_scoped(self):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append((req.full_url, req.get_method()))
            return _Resp({"status": "cleared"})

        with mock.patch.object(urllib.request, "urlopen", fake_urlopen):
            AutoRouterClient(base_url="https://api.test.com").clear_cache()
        self.assertEqual(seen, [("https://api.test.com/v1/cache", "DELETE")])
        with self.assertRaises(TypeError):
            AutoRouterClient().clear_cache("someone_else")

    def test_chat_sends_auto_and_route_preference(self):
        sent = {}

        def fake_urlopen(req, timeout=None):
            sent.update(json.loads(req.data.decode("utf-8")))
            sent["_ua"] = req.get_header("User-agent")
            return _Resp({"choices": [{"message": {"content": "hi"}}]})

        with mock.patch.object(urllib.request, "urlopen", fake_urlopen):
            out = AutoRouterClient(base_url="https://api.test.com").chat(
                messages=[{"role": "user", "content": "x"}], extra_body={"route_preference": "latency"}
            )
        self.assertEqual(out["choices"][0]["message"]["content"], "hi")
        self.assertEqual(sent["model"], "auto")
        self.assertEqual(sent["route_preference"], "latency")
        self.assertTrue(sent["_ua"].startswith("sentiogate-python/"))


if __name__ == "__main__":
    unittest.main()
