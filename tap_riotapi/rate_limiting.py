from collections import deque
from datetime import datetime, timedelta, timezone
from math import remainder
from typing import NamedTuple

from sqlalchemy.event import remove

from tap_riotapi.utils import REGION_ROUTING_MAP


class RateLimitBucket:

    def __init__(self, duration: int, cap: int):

        self.duration = duration
        self.reported_request_count = 0
        self._request_log: deque[datetime] = deque(maxlen=cap)

    def log_request(self, req_timestamp: datetime | None = None):
        if req_timestamp is None:
            req_timestamp = datetime.now(timezone.utc).astimezone()
        self._request_log.append(req_timestamp)
        self.reported_request_count += 1

    def prune(self):
        mark_timestamp = datetime.now(timezone.utc).astimezone()
        while self._request_log and self._request_log[0] < mark_timestamp - timedelta(
            seconds=self.duration
        ):
            self._request_log.popleft()
            self.reported_request_count -= 1

    def remaining(self):
        return self._request_log.maxlen - self.reported_request_count

    def wait(self):
        if self.remaining() > 0:
            return 0

        ready_time = self._request_log[0] + timedelta(seconds=self.duration)
        mark_timestamp = datetime.now(timezone.utc).astimezone()
        if ready_time < mark_timestamp:
            self.prune()
            return 0

        return (ready_time - mark_timestamp).total_seconds()

    def __repr__(self):
        return f"{len(self._request_log)}:{self.duration}"


class _RateLimitRecord(NamedTuple):

    datetime_returned: datetime
    rate_cap: str
    rate_count: str


class RateLimitState:

    def __init__(self):

        self._rate_limits = {}
        for key, value in REGION_ROUTING_MAP.items():
            self._rate_limits.setdefault(key, {})
            self._rate_limits.setdefault(value, {})

    def set_up_buckets(self, routing_value: str, key: str, cap_string: str):

        key_records = self._rate_limits[routing_value].setdefault(key, {})
        for str_record in cap_string.split(","):
            cap, size = str_record.split(":")
            if size not in key_records.keys():
                key_records[size] = RateLimitBucket(int(size), int(cap))
        return key_records

    def log_response(
        self,
        routing_value: str,
        rate_limit: _RateLimitRecord,
        endpoint: str | None = None,
    ):

        key = endpoint if endpoint else "app"
        app_records = self.set_up_buckets(routing_value, key, rate_limit.rate_cap)
        for str_record in rate_limit.rate_count.split(","):
            count, size = str_record.split(":")
            app_records[size].log_request(rate_limit.datetime_returned)
            app_records[size].reported_request_count = int(count)
            app_records[size].prune()

    def request_wait(self, routing_value: str, endpoint: str) -> int:

        min_wait_needed = 0

        for bucket in self._rate_limits[routing_value].get(endpoint, {}).values():
            bucket.prune()
            min_wait_needed = max(min_wait_needed, bucket.wait())

        for bucket in self._rate_limits[routing_value].get("app", {}).values():
            bucket.prune()
            min_wait_needed = max(min_wait_needed, bucket.wait())

        return min_wait_needed


# Some kind of rate limit mixin to handle Retry-After header?
