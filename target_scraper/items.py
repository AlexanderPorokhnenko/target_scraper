import scrapy
from itemloaders.processors import Identity


class TargetScraperItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    images = scrapy.Field(output_processor=Identity())
    description = scrapy.Field()
