import scrapy
from basic_scrapy_spider.items import QuoteItem
import scrapy
from urllib.parse import urljoin  # Import urljoin
from basic_scrapy_spider.items import QuoteItem  # Ensure this item is defined if used


class AmazonReviewsSpider(scrapy.Spider):
    name = "amazon_reviews"

    custom_settings = {
        'FEEDS': { 'data/%(name)s_%(time)s.csv': { 'format': 'csv',}}
        }

    def start_requests(self):
        asin_list = ['B0CZDG3M67']
        for asin in asin_list:
            amazon_reviews_url = f'https://www.amazon.com/product-reviews/{asin}/'
            yield scrapy.Request(url=amazon_reviews_url, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': 0})


    def parse_reviews(self, response):
        asin = response.meta['asin']
        retry_count = response.meta['retry_count']

        next_page_relative_url = response.css(".a-pagination .a-last>a::attr(href)").get()
        if next_page_relative_url is not None:
            retry_count = 0
            next_page = urljoin('https://www.amazon.com/', next_page_relative_url)
            yield scrapy.Request(url=next_page, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': retry_count})

        ## Adding this retry_count here so we retry any amazon js rendered review pages
        elif retry_count < 3:
            retry_count = retry_count+1
            yield scrapy.Request(url=response.url, callback=self.parse_reviews, dont_filter=True, meta={'asin': asin, 'retry_count': retry_count})


        ## Parse Product Reviews
        review_elements = response.css("#cm_cr-review_list div.review")
        for review_element in review_elements:
            yield {
                    "asin": asin,
                    "text": "".join(review_element.css("span[data-hook=review-body] ::text").getall()).strip(),
                    "title": review_element.css("*[data-hook=review-title]>span::text").get(),
                    "location_and_date": review_element.css("span[data-hook=review-date] ::text").get(),
                    "verified": bool(review_element.css("span[data-hook=avp-badge] ::text").get()),
                    "rating": review_element.css("*[data-hook*=review-star-rating] ::text").re(r"(\d+\.*\d*) out")[0],
                    }
    

import scrapy
from urllib.parse import urljoin

class WalmartReviewsSpider(scrapy.Spider):
    name = "walmart_reviews"

    custom_settings = {
        'FEEDS': {'data/%(name)s_%(time)s.csv': {'format': 'csv',}}
    }

    def start_requests(self):
        asin_list = ['747584156']
        for asin in asin_list:
            walmart_reviews_url = f'https://www.walmart.com/reviews/product/{asin}/'
            yield scrapy.Request(url=walmart_reviews_url, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': 0})

    def parse_reviews(self, response):
        asin = response.meta['asin']
        retry_count = response.meta['retry_count']

        next_page_relative_url = response.css('a[aria-label="Next Page"]::attr(href)').get()
        if next_page_relative_url is not None:
            retry_count = 0
            next_page = urljoin('https://www.walmart.com/', next_page_relative_url)
            yield scrapy.Request(url=next_page, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': retry_count})

        # Retry logic for JavaScript rendered review pages
        elif retry_count < 3:
            retry_count += 1
            yield scrapy.Request(url=response.url, callback=self.parse_reviews, dont_filter=True, meta={'asin': asin, 'retry_count': retry_count})

        # Parse Product Reviews
        review_elements = response.css(".review")

        if not review_elements:
            self.logger.warning(f"No review elements found on page: {response.url}")

        for review_element in review_elements:
            try:
                text = "".join(review_element.css(".review-text ::text").getall()).strip()
                title = review_element.css(".review-title ::text").get()
                location_and_date = review_element.css(".review-footer-userLocation ::text").get()
                verified = bool(review_element.css(".review-badge ::text").get())
                rating = review_element.css(".stars-container span.visuallyhidden::text").re_first(r"(\d+\.*\d*) out of 5 stars")

                if not text or not title or not rating:
                    self.logger.warning(f"Missing data in review element: {review_element.extract()}")

                yield {
                    "asin": asin,
                    "text": text,
                    "title": title,
                    "location_and_date": location_and_date,
                    "verified": verified,
                    "rating": rating,
                }
            except Exception as e:
                self.logger.error(f"Error parsing review element: {review_element.extract()} - Error: {e}")


