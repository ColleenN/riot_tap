"""Offline tests for Retry-After handling in generate_wait."""

import pytest
import requests

from tap_riotapi.client import generate_wait


def _error_with_response(status, headers=None):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    return requests.exceptions.HTTPError(response=response)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "generate_wait checks `if rsps and ...`, but a requests.Response is falsy "
        "for error statuses, so Retry-After is never honored"
    ),
)
def test_generate_wait_honors_retry_after_on_429():
    assert generate_wait(_error_with_response(429, {"Retry-After": "5"})) == 6


def test_generate_wait_without_retry_after():
    assert generate_wait(_error_with_response(429)) is None
    assert generate_wait(_error_with_response(500, {"Retry-After": "5"})) is None
    assert generate_wait(Exception("no response")) is None
