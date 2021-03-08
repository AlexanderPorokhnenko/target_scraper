import scrapy
import json
import re
import jmespath
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst
from ..items import TargetScraperItem


class TargetSpider(scrapy.Spider):
    name = 'target'
    API_URL = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key={0}&tcin={1}&store_id=86&' \
              'has_store_id=true&pricing_store_id=86&scheduled_delivery_store_id=none&' \
              'has_scheduled_delivery_store_id=false&has_financing_options=false'
    allowed_domains = ['target.com']

    def start_requests(self):
        url = 'https://www.target.com/p/reese-39-s-easter-peanut-butter-eggs-7-2oz-6ct/-/A-53957905'
        yield scrapy.Request(url=url, callback=self.parse)

    def parse_json(self, response):
        loader = ItemLoader(item=TargetScraperItem(), response=response)
        loader.default_output_processor = TakeFirst()
        page_body = json.loads(response.body.decode())
        loader.add_value('price', self.parse_price(page_body))
        loader.add_value('images', self.parse_images(page_body))
        loader.add_value('description', self.parse_description(page_body))
        loader.add_value('title', self.parse_title(page_body))
        return loader.load_item()

    def parse_title(self, page_body):
        return jmespath.search('data.product.item.product_description.title', page_body)

    def parse_price(self, page_body):
        return jmespath.search('data.product.price.current_retail', page_body)

    def parse_description(self, page_body):
        return jmespath.search('data.product.item.product_description.downstream_description', page_body)

    def parse_images(self, page_body):
        alternate_images = jmespath.search('data.product.item.enrichment.images.alternate_images', page_body)
        primary_image = jmespath.search('data.product.item.enrichment.images.primary_image', page_body)
        if alternate_images and isinstance(alternate_images, list):
            alternate_images.append(primary_image)
            return alternate_images
        return primary_image

    def parse(self, response):
        page_body = response.body.decode()
        pattern = r'apiKey\":\"([^\"]+)'
        found = re.search(pattern, page_body)
        if found:
            api_key = found.group(1)
            graph_data = json.loads(response.css('script[type="application/ld+json"]::text').extract_first())
            sku = jmespath.search('\"@graph\"[0].sku', graph_data)
            if api_key and sku:
                yield scrapy.Request(url=self.API_URL.format(api_key, sku),
                                     callback=self.parse_json)
