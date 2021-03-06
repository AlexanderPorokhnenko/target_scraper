import scrapy
import json
import re
import jmespath
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst
from ..items import TargetScraperItem


class TargetSpider(scrapy.Spider):
    name = 'target'
    allowed_domains = ['target.com']

    def start_requests(self):
        url = 'https://www.target.com/p/reese-39-s-easter-peanut-butter-eggs-7-2oz-6ct/-/A-53957905'
        yield scrapy.Request(url=url, callback=self.parse)

    def parse_json(self, response):
        loader = ItemLoader(item=TargetScraperItem(), response=response)
        loader.default_output_processor = TakeFirst()
        page_body = json.loads(response.body.decode())
        loader.add_value('price', jmespath.search('data.product.price.current_retail', page_body))
        loader.add_value('images', jmespath.search('data.product.item.enrichment.images.primary_image', page_body))
        loader.add_value('description',
                         jmespath.search('data.product.item.product_description.downstream_description', page_body))
        loader.add_value('title', jmespath.search('data.product.item.product_description.title', page_body))
        loader.add_value('images', jmespath.search('data.product.item.enrichment.images.alternate_images', page_body))
        return loader.load_item()

    def parse(self, response):
        page_body = response.body.decode()
        api_key = re.search(pattern=r'apiKey\":\"([^\"]+)', string=page_body).group(1)
        graph_data = json.loads(response.css('script[type="application/ld+json"]::text').extract_first())
        sku = jmespath.search('\"@graph\"[0].sku', graph_data)
        yield scrapy.Request(url=f'https://redsky.target.com/redsky_aggregations/v1/web/'
                                 f'pdp_client_v1?key={api_key}&tcin={sku}&store_id=86&has_store_id=true&'
                                 f'pricing_store_id=86&scheduled_delivery_store_id=none&'
                                 f'has_scheduled_delivery_store_id=false&has_financing_options=false',
                             callback=self.parse_json)
