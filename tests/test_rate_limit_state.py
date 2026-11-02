"""Offline tests for RateLimitState and its parsing of Riot's rate-limit headers."""

from tap_riotapi.rate_limiting import RateLimitState, _RateLimitRecord


def test_log_response_creates_a_bucket_per_window(frozen_now):
    state = RateLimitState()
    state.log_response("americas", _RateLimitRecord(frozen_now, "20:1,100:120", "1:1,1:120"))

    buckets = state._rate_limits["americas"]["app"]
    assert set(buckets) == {"1", "120"}
    assert buckets["1"].remaining() == 19
    assert buckets["120"].remaining() == 99


def test_log_response_uses_the_reported_count(frozen_now):
    state = RateLimitState()
    state.log_response("americas", _RateLimitRecord(frozen_now, "20:1,100:120", "1:1,100:120"))

    # Riot reports the 120s window as full, so the next request waits out the window.
    assert state.request_wait("americas", "/some/endpoint") == 120


def test_request_wait_is_zero_with_room_left(frozen_now):
    state = RateLimitState()
    state.log_response("asia", _RateLimitRecord(frozen_now, "20:1", "1:1"))
    state.log_response("asia", _RateLimitRecord(frozen_now, "500:10", "1:10"), endpoint="/tft/x")

    assert state.request_wait("asia", "/tft/x") == 0


def test_request_wait_for_unseen_routing_values_and_endpoints(frozen_now):
    state = RateLimitState()

    assert state.request_wait("na1", "/never/called") == 0
