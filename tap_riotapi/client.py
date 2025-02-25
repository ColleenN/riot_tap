"""REST client handling, including RiotAPIStream base class."""

from __future__ import annotations

from datetime import datetime
import typing as t

from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BaseAPIPaginator  # noqa: TC002
from singer_sdk.streams import RESTStream

from tap_riotapi.utils import _RateLimitRecord

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context


class RiotAPIStream(RESTStream):
    """RiotAPI stream class."""

    routing_type = "regional"

    # Update this value if necessary or override `parse_response`.
    records_jsonpath = "$[*]"

    # Update this value if necessary or override `get_new_paginator`.
    next_page_token_jsonpath = "$.next_page"  # noqa: S105

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

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Create a new pagination helper instance.

        If the source API can make use of the `next_page_token_jsonpath`
        attribute, or it contains a `X-Next-Page` header in the response
        then you can remove this method.

        If you need custom pagination that uses page numbers, "next" links, or
        other approaches, please read the guide: https://sdk.meltano.com/en/v0.25.0/guides/pagination-classes.html.

        Returns:
            A pagination helper instance.
        """
        return super().get_new_paginator()

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ANN401
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary of URL query parameters.
        """
        params: dict = {}
        if next_page_token:
            params["page"] = next_page_token
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        return params

    def prepare_request_payload(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ARG002, ANN401
    ) -> dict | None:
        """Prepare the data payload for the REST API request.

        By default, no payload will be sent (return None).

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary with the JSON body for a POST requests.
        """
        # TODO: Delete this method if no payload is required. (Most REST APIs.)
        return None

    def routing_value(self, context: Context):
        if self.routing_type == "regional":
            return context["region_routing_value"]
        else:
            return context["platform_routing_value"]

    def parse_response(self, response: requests.Response) -> t.Iterable[dict]:
        """Parse the response and return an iterator of result records.

        Args:
            response: The HTTP ``requests.Response`` object.

        Yields:
            Each record from the source.
        """
        timestamp = datetime.strptime(
            response.headers["Date"], "%a, %d %b %Y %H:%M:%S %Z"
        )

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

        data_iter = iter(super().parse_response(response))
        first_record = next(data_iter)
        yield {
            "data": first_record,
            "method_rate_limit": method_rate_limit,
            "app_rate_limit": app_rate_limit,
        }

        for record in data_iter:
            yield {"data": record}

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
            self.update_rate_limit_state(
                routing_value=self.routing_value(context),
                new_info=row["app_rate_limit"]
            )
        if "method_rate_limit" in row.keys():
            self.update_rate_limit_state(
                routing_value=self.routing_value(context),
                new_info=row["method_rate_limit"],
                endpoint=self.get_url(context)
            )
        if "data" not in row.keys():
            raise Exception(row)
        return row["data"]

    def update_rate_limit_state(
        self,
        routing_value: str,
        new_info: _RateLimitRecord,
        endpoint: str | None = None,
    ):

        if not "rate_limits" in self._tap_state.keys():
            self._tap_state["rate_limits"] = {}

        if not routing_value in self._tap_state["rate_limits"].keys():
            self._tap_state["rate_limits"][routing_value] = {}

        key = endpoint if endpoint else "app"

        if not self._tap_state["rate_limits"][routing_value].get(key):
            self._tap_state["rate_limits"][routing_value][key] = new_info
        else:
            current = self._tap_state["rate_limits"][routing_value].get(key)
            if current.datetime_returned < new_info.datetime_returned:
                self._tap_state["rate_limits"][routing_value][key] = new_info
