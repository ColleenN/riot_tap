"""Offline tests for rate-limit tracking and Retry-After handling."""

from datetime import datetime, timedelta, timezone

import pytest
import requests

from tap_riotapi.client import generate_wait
from tap_riotapi.rate_limiting import RateLimitBucket, RateLimitState, _RateLimitRecord


def now():
    return datetime.now(timezone.utc).astimezone()


# --- RateLimitBucket -------------------------------------------------------


def test_bucket_has_room_until_cap():
    bucket = RateLimitBucket(duration=1, cap=2)
    bucket.log_request()

    assert bucket.remaining() == 1
    assert bucket.wait() == 0


def test_full_bucket_waits_until_oldest_request_expires():
    bucket = RateLimitBucket(duration=10, cap=2)
    bucket.log_request(now() - timedelta(seconds=4))
    bucket.log_request(now())

    assert bucket.remaining() == 0
    assert 5 < bucket.wait() <= 6


def test_full_bucket_frees_up_once_requests_expire():
    bucket = RateLimitBucket(duration=10, cap=2)
    bucket.log_request(now() - timedelta(seconds=30))
    bucket.log_request(now() - timedelta(seconds=20))

    assert bucket.wait() == 0
    assert bucket.remaining() == 2


def test_prune_drops_only_expired_requests():
    bucket = RateLimitBucket(duration=10, cap=5)
    bucket.log_request(now() - timedelta(seconds=30))
    bucket.log_request(now())

    bucket.prune()

    assert bucket.remaining() == 4


# --- RateLimitState --------------------------------------------------------


def test_log_response_creates_a_bucket_per_window():
    state = RateLimitState()
    state.log_response("americas", _RateLimitRecord(now(), "20:1,100:120", "1:1,1:120"))

    buckets = state._rate_limits["americas"]["app"]
    assert set(buckets) == {"1", "120"}
    assert buckets["1"].remaining() == 19
    assert buckets["120"].remaining() == 99


def test_log_response_uses_the_reported_count():
    state = RateLimitState()
    state.log_response("americas", _RateLimitRecord(now(), "20:1,100:120", "1:1,100:120"))

    # Riot reports the 120s window as full, so the next request has to wait.
    assert state.request_wait("americas", "/some/endpoint") > 0


def test_request_wait_is_zero_with_room_left():
    state = RateLimitState()
    state.log_response("asia", _RateLimitRecord(now(), "20:1", "1:1"))
    state.log_response("asia", _RateLimitRecord(now(), "500:10", "1:10"), endpoint="/tft/x")

    assert state.request_wait("asia", "/tft/x") == 0


def test_request_wait_for_unseen_routing_values_and_endpoints():
    state = RateLimitState()

    assert state.request_wait("na1", "/never/called") == 0


# --- Retry-After -----------------------------------------------------------


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
