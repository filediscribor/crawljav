import scrapy
import json
import os

from crawl_jav.items import CrawlJavItem
from crawl_jav.spiders import crawl_utils


class Toscrapy_Jav(scrapy.Spider):
    name = 'javspider'

    start_urls = ['http://www.jav321.com/']

    def parse(self, response):
        # url = self.start_urls[0] + '/series_title_list/{}'.format(1)
        url = self.start_urls[0] + '/series/13499/1'
        crawl_utils.execute(url)
