from types import SimpleNamespace

from app.core import rate_limit
from app.core.rate_limit import client_ip


def request(forwarded=None, host="10.0.0.1"):
    headers = {"X-Forwarded-For": forwarded} if forwarded else {}
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


def test_ignores_forwarded_header_without_trusted_proxy(monkeypatch):
    monkeypatch.setattr(rate_limit.settings, "trusted_proxy_hops", 0)
    assert client_ip(request("6.6.6.6, 1.2.3.4")) == "10.0.0.1"


def test_uses_address_appended_by_trusted_proxy(monkeypatch):
    monkeypatch.setattr(rate_limit.settings, "trusted_proxy_hops", 1)
    assert client_ip(request("6.6.6.6, 1.2.3.4")) == "1.2.3.4"


def test_falls_back_when_chain_is_shorter_than_hops(monkeypatch):
    monkeypatch.setattr(rate_limit.settings, "trusted_proxy_hops", 2)
    assert client_ip(request("1.2.3.4")) == "10.0.0.1"
