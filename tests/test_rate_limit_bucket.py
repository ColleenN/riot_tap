"""Offline tests for RateLimitBucket."""

from datetime import datetime, timedelta, timezone

from tap_riotapi.rate_limiting import RateLimitBucket


def now():
    return datetime.now(timezone.utc).astimezone()


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
