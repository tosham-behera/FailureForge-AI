"""Tests must never send an HTTP request to a real model provider."""
import httpx
import pytest


@pytest.fixture(autouse=True)
def block_live_http(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Live HTTP is forbidden in automated tests")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked)
    monkeypatch.setenv("DEMO_MODE", "true")
