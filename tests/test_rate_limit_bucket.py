"""Offline tests for RateLimitBucket."""

from datetime import timedelta

from tap_riotapi.rate_limiting import RateLimitBucket


def test_bucket_has_room_until_cap(frozen_now):
    bucket = RateLimitBucket(duration=1, cap=2)
    bucket.log_request()

    assert bucket.remaining() == 1
    assert bucket.wait() == 0


def test_full_bucket_waits_until_oldest_request_expires(frozen_now):
    bucket = RateLimitBucket(duration=10, cap=2)
    bucket.log_request(frozen_now - timedelta(seconds=4))
    bucket.log_request(frozen_now)

    assert bucket.remaining() == 0
    assert bucket.wait() == 6


def test_full_bucket_frees_up_once_requests_expire(frozen_now):
    bucket = RateLimitBucket(duration=10, cap=2)
    bucket.log_request(frozen_now - timedelta(seconds=30))
    bucket.log_request(frozen_now - timedelta(seconds=20))

    assert bucket.wait() == 0
    assert bucket.remaining() == 2


def test_prune_drops_only_expired_requests(frozen_now):
    bucket = RateLimitBucket(duration=10, cap=5)
    bucket.log_request(frozen_now - timedelta(seconds=30))
    bucket.log_request(frozen_now)

    bucket.prune()

    assert bucket.remaining() == 4


def test_request_exactly_at_the_window_edge_is_kept(frozen_now):
    bucket = RateLimitBucket(duration=10, cap=5)
    bucket.log_request(frozen_now - timedelta(seconds=10))

    bucket.prune()

    assert bucket.remaining() == 4
