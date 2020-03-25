# -*- coding: utf-8 -*-
import scrapy
import scrapy.http.response
import datetime
import json
import sys
import os
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 切换到当前工作目录
from pymongo import MongoClient
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from items import BuffItem


class GoodsSpider(scrapy.Spider):
    name = 'goods'
    allowed_domains = ['buff.163.com']
    start_urls = []
    author = 'uzdz'
    headers = {'content-type': 'charset=utf8'}

    def __init__(self, mongo_url, mongo_port, mongo_db, goods_collect,
                 session, auth, auth_user_name, auth_password):
        self.mongo_url = mongo_url
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.goods_collect = goods_collect
        self.session = session
        self.auth = auth
        self.auth_password = auth_password
        self.auth_user_name = auth_user_name
        self.client = 'Undetermined'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_port=crawler.settings.get('MONGO_PORT'),
            mongo_db=crawler.settings.get('MONGO_DB'),
            goods_collect=crawler.settings.get('MONGO_DB_GOODS_COLLECT'),
            session=crawler.settings.get('BUFF_SESSION'),
            auth=crawler.settings.get('MONGO_DB_AUTH'),
            auth_user_name=crawler.settings.get('MONGO_DB_AUTH_USER_NAME'),
            auth_password=crawler.settings.get('MONGO_DB_AUTH_PASSWORD')
        )

    def start_requests(self):

        self.client = MongoClient(self.mongo_url, self.mongo_port)

        if self.auth:
            db = self.client['admin']
            db.authenticate(self.auth_user_name, self.auth_password)

        dbs = self.client.list_database_names()
        if self.mongo_db not in dbs:
            print("MongoDB：数据库不存在!")
            raise Exception("MongoDB：数据库不存在")

        db = self.client[self.mongo_db]
        collections = db.list_collection_names()
        if self.goods_collect not in collections:
            print("MongoDB：商品列表goods：Collection不存在!")
            raise Exception("MongoDB：商品列表：Collection不存在!")

        goods_list = db[self.goods_collect].find()

        for x in goods_list:
            good_id = x['good_id']
            init = x['init']

            start_url = 'https://buff.163.com/api/market/goods/sell_order' \
                        '?game=csgo&goods_id=' + good_id + \
                        '&page_num=1&page_size=500&sort_by=default' \
                        '&mode=&allow_tradable_cooldown=1&_=1577431198385'

            current_header = self.headers
            current_header.update({'good_id': good_id})

            if init:
                current_header.update({'init': init})
            else:
                current_header.update({'init': ''})

            yield scrapy.Request(url=start_url, headers=current_header, callback=self.parse,
                                 cookies=self.session)

            query = {"good_id": good_id}
            value = {"$set": {"init": False}}
            db[self.goods_collect].update_one(query, value)

        # 关闭资源
        self.client.close()

    def parse(self, response):
        header = response.request.headers
        good_id = str(header['good_id'], 'utf-8')
        init = bool(str(header['init'], 'utf-8'))

        # print("爬取到的数据：" + response.text)

        x = json.loads(response.text)

        # # 当前页码
        # current_num = x['data']['page_num']
        # # 最大页码
        # max_num = x['data']['total_page']
        # if max_num > current_num:
        #     next_num = current_num + 1
        #     next_url = 'https://buff.163.com/api/market/goods/sell_order' \
        #                '?game=csgo&goods_id=43079&page_num=' + str(next_num) + '&sort_by=default' \
        #                '&mode=&allow_tradable_cooldown=1&_=1577431198385'
        #
        #     print(next_url)
        #     yield scrapy.Request(url=next_url, callback=self.parse, dont_filter=True)

        # 商品名称
        good_name = x['data']['goods_infos'][good_id]['name']

        print("【" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "】" + good_name + "，总共商品实例数量：" + str(len(x['data']['items'])))

        for good in x['data']['items']:
            item = BuffItem()

            # 商品id
            item['good_id'] = good_id

            # 商品名称
            item['good_name'] = good_name

            # 商品实例id
            item['good_inst_id'] = str(good.get('id', "None"))

            # 是否允许还价
            item['can_bargain'] = str(good.get('can_bargain', "None"))

            # 描述
            item['description'] = str(good.get('description', "None"))

            # 最低还价金额
            item['lowest_bargain_price'] = float(good.get('lowest_bargain_price', "None"))

            # 此饰品价格
            item['price'] = float(good.get('price', "None"))

            # 商品图片
            img = good['asset_info']['info']
            item['image_url'] = str(img.get('inspect_url', "None"))

            # 商品初始化状态
            item['init'] = init

            yield item
