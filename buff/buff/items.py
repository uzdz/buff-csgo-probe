# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BuffItem(scrapy.Item):

    # 商品实例id
    good_inst_id = scrapy.Field()

    # 商品id
    good_id = scrapy.Field()

    # 商品名称
    good_name = scrapy.Field()

    # 是否允许还价
    can_bargain = scrapy.Field()

    # 描述
    description = scrapy.Field()

    # 最低还价金额
    lowest_bargain_price = scrapy.Field()

    # 此饰品价格
    price = scrapy.Field()

    # 商品图片
    image_url = scrapy.Field()

    # 初始化状态
    init = scrapy.Field()

    pass


