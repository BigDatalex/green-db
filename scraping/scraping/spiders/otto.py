import json
from logging import getLogger
from typing import Iterator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from scrapy_splash import SplashJsonResponse, SplashRequest

from ..splash import scroll_end_of_page_script
from ._base import BaseSpider

logger = getLogger(__name__)


class OttoSpider(BaseSpider):
    name = "otto"
    allowed_domains = ["otto.de"]

    def parse_SERP(self, response: SplashJsonResponse) -> Iterator[SplashRequest]:

        # Save HTML to database
        self._save_SERP(response)

        # Get all unique links
        all_links = list(set(response.css("[href]::attr(href)").getall()))

        # Filter for product links
        all_product_links = [
            response.urljoin(link)
            for link in all_links
            if "/#variationId=" in link and "/p/" in link
        ]

        if self.products_per_page:
            all_product_links = all_product_links[: self.products_per_page]

        logger.info(f"Number of products per page {len(all_product_links)} to be scraped")

        for product_link in all_product_links:
            yield SplashRequest(
                url=product_link,
                callback=self.parse_PRODUCT,
                endpoint="execute",
                args={  # passed to Splash HTTP API
                    "wait": self.request_timeout,
                    "lua_source": scroll_end_of_page_script,
                    "timeout": 180,
                },
            )

        # Pagination uses parameters 'l' and 'o' to load next batch of products
        pagination_list = response.css(
            '[class*="js_pagingLink ts-link p_btn50--1st san_paging__btn"]::attr(data-page)'
        ).getall()

        if len(pagination_list) > 0:

            pagination_info = json.loads(pagination_list[-1])
            if int(pagination_info["o"]) > response.meta.get("o", 0):

                # Drop existing 'o' and 'l' parameters
                url_parsed = urlparse(response.url)
                queries = parse_qs(url_parsed.query, keep_blank_values=True)
                queries.pop("o", None)
                queries.pop("l", None)
                url_parsed = url_parsed._replace(query=urlencode(queries, True))
                url = urlunparse(url_parsed)

                url = f'{url.rstrip("/")}&l={pagination_info["l"]}&o={pagination_info["o"]}'

                yield SplashRequest(
                    url=url,
                    callback=self.parse_SERP,
                    meta={"o": int(pagination_info["o"])},
                    endpoint="execute",
                    args={  # passed to Splash HTTP API
                        "wait": self.request_timeout,
                        "lua_source": scroll_end_of_page_script,
                        "timeout": 180,
                    },
                )
            else:
                logger.info(f"No further pages: {response.url}")

        else:
            logger.info(f"No pagination: {response.url}")
