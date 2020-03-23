# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import math
from email.header import Header
from email.mime.text import MIMEText
import smtplib

from pymongo import MongoClient
from scrapy.exceptions import DropItem


class BuffPipeline(object):

    def __init__(self, mongo_url, mongo_port, mongo_db):
        self.mongo_url = mongo_url
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.client = 'Undetermined'
        self.db = 'Undetermined'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_port=crawler.settings.get('MONGO_PORT'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_url, self.mongo_port)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        change = dict(item)  # 把item转化成字典形式
        change.update({"_id": item['good_inst_id']})
        good_inst_id = item['good_inst_id']
        good_id = item['good_id']

        # 查询库里是否已有该武器的doc
        doc = self.db[good_id].find_one({"_id": good_inst_id})

        if doc is not None:
            if not math.isclose(doc['price'], item['price'], rel_tol=1e-9):
                # 库中存在记录，但价格发生了变化
                self.update(good_id, good_inst_id, change)
            else:
                # 商品存在，且价格未发生变化，无需邮件通知
                raise DropItem()
        else:
            # 库中不存在此记录
            self.insert(good_id, change)

        if item['init']:
            # 商品初始化，无需发送邮件
            raise DropItem()
        else:
            return item

    def close_spider(self, spider):
        self.client.close()

    def update(self, good_id, good_inst_id, change):
        query = {"_id": good_inst_id}
        value = {"$set": change}
        self.db[good_id].update_one(query, value)

    def insert(self, good_id, value):
        self.db[good_id].insert(value)


class EmailPipeline(object):

    def __init__(self, email, email_password, email_server):
        self.email = email
        self.email_password = email_password
        self.email_server = email_server

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            email=crawler.settings.get('EMAIL'),
            email_password=crawler.settings.get('EMAIL_PASSWORD'),
            email_server=crawler.settings.get('EMAIL_SERVER')
        )

    def process_item(self, item, spider):
        # 格式化邮件整体信息
        msg = MIMEText('<html><body>'
                       '<h3>饰品价格：<font color="#FF0000">' + str(item['price']) + '</font></h3>'
                       '<h3>描述：<font color="#FF0000">' + item['description'] + '</font></h3>'
                       '<h3>是否允许还价：<font color="#FF0000">' + item['can_bargain'] + '</font></h3>'
                       '<h3>最低还价金额：<font color="#FF0000">' + str(item['lowest_bargain_price']) + '</font></h3>'
                       '<p><img src="' + item['image_url'] + '"></p>'
                       '</body></html>', 'html', 'utf-8')
        msg['Subject'] = Header("CSGO 价格变动：" + item['good_name'], 'utf-8')
        msg['From'] = self.email
        msg['To'] = self.email

        # 连接并发送邮件
        server = smtplib.SMTP(host=self.email_server, port=25)
        server.login(self.email, self.email_password)
        server.sendmail(self.email, self.email, msg.as_string())
        server.quit()
        return item
