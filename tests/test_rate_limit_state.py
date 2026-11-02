"""Offline tests for RateLimitState and its parsing of Riot's rate-limit headers."""

from datetime import datetime, timezone

import time_machine

from tap_riotapi.rate_limiting import RateLimitState, _RateLimitRecord

NOW = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)


@time_machine.travel(NOW, tick=False)
def test_log_response_creates_a_bucket_per_window():
    state = RateLimitState()
    state.log_response("americas", _RateLimitRecord(NOW, "20:1,100:120", "1:1,1:120"))

    buckets = state._rate_limits["americas"]["app"]
    assert set(buckets) == {"1", "120"}
    assert buckets["1"].remaining() == 19
    assert buckets["120"].remaining() == 99


@time_machine.travel(NOW, tick=False)
def test_log_response_uses_the_reported_count():
    state = RateLimitState()
    state.log_response("americas", _RateLimitRecord(NOW, "20:1,100:120", "1:1,100:120"))

    # Riot reports the 120s window as full, so the next request waits out the window.
    assert state.request_wait("americas", "/some/endpoint") == 120


@time_machine.travel(NOW, tick=False)
def test_request_wait_is_zero_with_room_left():
    state = RateLimitState()
    state.log_response("asia", _RateLimitRecord(NOW, "20:1", "1:1"))
    state.log_response("asia", _RateLimitRecord(NOW, "500:10", "1:10"), endpoint="/tft/x")

    assert state.request_wait("asia", "/tft/x") == 0


@time_machine.travel(NOW, tick=False)
def test_request_wait_for_unseen_routing_values_and_endpoints():
    state = RateLimitState()

    assert state.request_wait("na1", "/never/called") == 0
