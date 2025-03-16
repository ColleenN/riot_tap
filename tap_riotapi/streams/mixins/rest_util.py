import abc

from typing import Iterable

from singer_sdk.helpers.types import Context
from singer_sdk.pagination import BaseAPIPaginator
from singer_sdk import metrics


class ResumablePaginationMixin:

    def request_records(self, context: Context | None) -> Iterable[dict]:

        """Request records from REST endpoint(s), returning response records.

        If pagination is detected, pages will be recursed automatically.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            An item for every record in the response.
        """
        paginator = self.get_new_paginator(context)
        decorated_request = self.request_decorator(self._request)
        pages = 0

        with metrics.http_request_counter(self.name, self.path) as request_counter:
            request_counter.context = context

            while not paginator.finished:
                prepared_request = self.prepare_request(
                    context,
                    next_page_token=paginator.current_value,
                )
                resp = decorated_request(prepared_request, context)
                request_counter.increment()
                self.update_sync_costs(prepared_request, resp, context)
                records = iter(self.parse_response(resp))
                try:
                    first_record = next(records)
                except StopIteration:
                    self.logger.info(
                        "Pagination stopped after %d pages because no records were "
                        "found in the last response",
                        pages,
                    )
                    break
                yield first_record
                yield from records
                pages += 1

                paginator.advance(resp)

    def get_new_paginator(self, context: Context | None) -> BaseAPIPaginator:
        if not context:
            super().get_new_paginator()
        state_dict = self.get_context_state(context)
        new_paginator = self.build_paginator_from_state(state_dict)
        state_dict["current_paginator"] = new_paginator
        return new_paginator

    @abc.abstractmethod
    def build_paginator_from_state(self, state_dict: dict) -> BaseAPIPaginator:
        pass
