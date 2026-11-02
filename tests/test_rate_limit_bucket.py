"""Offline tests for RateLimitBucket."""

from datetime import datetime, timedelta, timezone

import time_machine

from tap_riotapi.rate_limiting import RateLimitBucket

NOW = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)


@time_machine.travel(NOW, tick=False)
def test_bucket_has_room_until_cap():
    bucket = RateLimitBucket(duration=1, cap=2)
    bucket.log_request()

    assert bucket.remaining() == 1
    assert bucket.wait() == 0


@time_machine.travel(NOW, tick=False)
def test_full_bucket_waits_until_oldest_request_expires():
    bucket = RateLimitBucket(duration=10, cap=2)
    bucket.log_request(NOW - timedelta(seconds=4))
    bucket.log_request(NOW)

    assert bucket.remaining() == 0
    assert bucket.wait() == 6


@time_machine.travel(NOW, tick=False)
def test_full_bucket_frees_up_once_requests_expire():
    bucket = RateLimitBucket(duration=10, cap=2)
    bucket.log_request(NOW - timedelta(seconds=30))
    bucket.log_request(NOW - timedelta(seconds=20))

    assert bucket.wait() == 0
    assert bucket.remaining() == 2


@time_machine.travel(NOW, tick=False)
def test_prune_drops_only_expired_requests():
    bucket = RateLimitBucket(duration=10, cap=5)
    bucket.log_request(NOW - timedelta(seconds=30))
    bucket.log_request(NOW)

    bucket.prune()

    assert bucket.remaining() == 4


@time_machine.travel(NOW, tick=False)
def test_request_exactly_at_the_window_edge_is_kept():
    bucket = RateLimitBucket(duration=10, cap=5)
    bucket.log_request(NOW - timedelta(seconds=10))

    bucket.prune()

    assert bucket.remaining() == 4
