"""REST client handling, including RiotAPIStream base class."""

from __future__ import annotations
from datetime import datetime
from dateutil import parser
from time import sleep
from urllib.parse import urlparse, parse_qs
from typing import TYPE_CHECKING

from backoff import expo
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.helpers._state import write_starting_replication_value
from singer_sdk.streams import RESTStream
from singer_sdk.streams.core import REPLICATION_INCREMENTAL

from tap_riotapi.rate_limiting import _RateLimitRecord

if TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context
    from typing import Any, Callable, Generator, Iterable


def generate_wait(exception: Any) -> int | None:

    rsps = getattr(exception, "response", None)

    if rsps and rsps.status_code == 429 and "Retry-After" in rsps.headers:
        return rsps.headers["Retry-After"]

    return None


class RiotAPIStream(RESTStream):
    """RiotAPI stream class."""

    routing_type = "regional"

    def routing_value(self, context: Context):
        if self.routing_type == "regional":
            return context["region_routing_value"]
        else:
            return context["platform_routing_value"]

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        if self.routing_type == "regional":
            return "https://{region_routing_value}.api.riotgames.com"
        else:
            return "https://{platform_routing_value}.api.riotgames.com"

    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return APIKeyAuthenticator.create_for_stream(
            self,
            key="X-Riot-Token",
            value=self.config.get("auth_token", ""),
            location="header",
        )

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP ``requests.Response`` object.

        Yields:
            Each record from the source.
        """
        timestamp = parser.parse(response.headers["Date"])

        app_rate_limit = _RateLimitRecord(
            datetime_returned=timestamp,
            rate_cap=response.headers["X-App-Rate-Limit"],
            rate_count=response.headers["X-App-Rate-Limit-Count"],
        )
        method_rate_limit = _RateLimitRecord(
            datetime_returned=timestamp,
            rate_cap=response.headers["X-Method-Rate-Limit"],
            rate_count=response.headers["X-Method-Rate-Limit-Count"],
        )
        url_params = parse_qs(urlparse(response.request.url).query)

        data_iter = iter(super().parse_response(response))
        try:
            first_record = next(data_iter)
        except StopIteration:
            first_record = None
        yield {
            "data": first_record,
            "method_rate_limit": method_rate_limit,
            "app_rate_limit": app_rate_limit,
            "url_params_used": url_params,
        }

        for record in data_iter:
            yield {"data": record, "url_params_used": url_params}

    def post_process(
        self,
        row: dict,
        context: Context | None = None,  # noqa: ARG002
    ) -> dict | None:
        """As needed, append or transform raw data to match expected structure.

        Args:
            row: An individual record from the stream.
            context: The stream context.

        Returns:
            The updated record dictionary, or ``None`` to skip the record.
        """
        if "app_rate_limit" in row.keys():
            self.tap_state["rate_limits"].log_response(
                routing_value=self.routing_value(context),
                rate_limit=row["app_rate_limit"],
            )
        if "method_rate_limit" in row.keys():
            self.tap_state["rate_limits"].log_response(
                routing_value=self.routing_value(context),
                rate_limit=row["method_rate_limit"],
                endpoint=self.path,
            )
        if "data" not in row.keys():
            raise Exception(row)

        if self.replication_method == REPLICATION_INCREMENTAL:
            return {"data": row["data"], "url_params_used": row["url_params_used"]}
        return row["data"]

    def _request(
        self,
        prepared_request: requests.PreparedRequest,
        context: Context | None,
    ) -> requests.Response:

        sleep(
            self.tap_state["rate_limits"].request_wait(
                self.routing_value(context), self.path
            )
        )
        return super()._request(prepared_request, context)

    def backoff_runtime(  # noqa: PLR6301
        self,
        *,
        value: Callable[[Any], int],
    ) -> Generator[int, None, None]:
        exception = yield  # type: ignore[misc]
        backup_gen = expo(factor=2)
        backup_gen.send(None)
        while True:
            if result := value(exception):
                exception = yield result
            else:
                yield from backup_gen

    def backoff_wait_generator(self) -> Generator[float, None, None]:
        return self.backoff_runtime(value=generate_wait)

    def _write_starting_replication_value(self, context: Context | None) -> None:
        """Write the starting replication value, if available.

        Args:
            context: Stream partition or context dictionary.
        """
        value = None
        state = self.get_context_state(context)

        if self.replication_key:
            replication_key_value = state.get("replication_key_value")
            if replication_key_value and self.replication_key == state.get(
                "replication_key",
            ):
                value = replication_key_value

            # Use start_date if it is more recent than the replication_key state
            start_date_value: datetime | None = self._tap.initial_timestamp
            if start_date_value:
                if not value:
                    value = start_date_value
                else:
                    value = max(start_date_value, value)

            self.logger.info("Starting incremental sync with bookmark value: %s", value)

        write_starting_replication_value(state, value)
