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
    
import json
import math
import scrapy
from urllib.parse import urlencode

class WalmartSpider(scrapy.Spider):
    name = "walmart"

    custom_settings = {
        'FEEDS': { 'data/%(name)s_%(time)s.csv': { 'format': 'csv',}}
        }

    def start_requests(self):
        keyword_list = ['laptop']
        for keyword in keyword_list:
            payload = {'q': keyword, 'sort': 'best_seller', 'page': 1, 'affinityOverride': 'default'}
            walmart_search_url = 'https://www.walmart.com/search?' + urlencode(payload)
            yield scrapy.Request(url=walmart_search_url, callback=self.parse_search_results, meta={'keyword': keyword, 'page': 1})

    def parse_search_results(self, response):
        page = response.meta['page']
        keyword = response.meta['keyword'] 
        script_tag  = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if script_tag is not None:
            json_blob = json.loads(script_tag)

            ## Request Product Page
            product_list = json_blob["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["items"]
            for idx, product in enumerate(product_list):
                walmart_product_url = 'https://www.walmart.com' + product.get('canonicalUrl', '').split('?')[0]
                yield scrapy.Request(url=walmart_product_url, callback=self.parse_product_data, meta={'keyword': keyword, 'page': page, 'position': idx + 1})
            
            ## Request Next Page
            if page == 1:
                total_product_count = json_blob["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["count"]
                max_pages = math.ceil(total_product_count / 40)
                if max_pages > 5:
                    max_pages = 5
                for p in range(2, max_pages):
                    payload = {'q': keyword, 'sort': 'best_seller', 'page': p, 'affinityOverride': 'default'}
                    walmart_search_url = 'https://www.walmart.com/search?' + urlencode(payload)
                    yield scrapy.Request(url=walmart_search_url, callback=self.parse_search_results, meta={'keyword': keyword, 'page': p})
    

    def parse_product_data(self, response):
        script_tag  = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if script_tag is not None:
            json_blob = json.loads(script_tag)
            raw_product_data = json_blob["props"]["pageProps"]["initialData"]["data"]["product"]
            yield {
                'keyword': response.meta['keyword'],
                'page': response.meta['page'],
                'position': response.meta['position'],
                'id':  raw_product_data.get('id'),
                'type':  raw_product_data.get('type'),
                'name':  raw_product_data.get('name'),
                'brand':  raw_product_data.get('brand'),
                'averageRating':  raw_product_data.get('averageRating'),
                'manufacturerName':  raw_product_data.get('manufacturerName'),
                'shortDescription':  raw_product_data.get('shortDescription'),
                'thumbnailUrl':  raw_product_data['imageInfo'].get('thumbnailUrl'),
                'price':  raw_product_data['priceInfo']['currentPrice'].get('price'), 
                'currencyUnit':  raw_product_data['priceInfo']['currentPrice'].get('currencyUnit'),  
            }

