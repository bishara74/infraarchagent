"""NFR-01: demo client is bounded to loopback and accepts no credential URL."""

import pytest

from scripts.phase10_demo import local_url

pytestmark = pytest.mark.req("NFR-01")


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com",
        "http://example.com",
        "http://user:password@127.0.0.1",
        "http://127.0.0.1/path",
        "http://127.0.0.1/?key=placeholder",
    ],
)
def test_demo_refuses_nonlocal_or_credential_urls(value):
    with pytest.raises(ValueError):
        local_url(value)


def test_demo_accepts_loopback_port():
    assert local_url("http://127.0.0.1:8765/") == "http://127.0.0.1:8765"
