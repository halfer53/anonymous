#encoding=utf-8
import os
import sys
import logging
sys.path.append('/tools/python_common')
sys.path.append('..')
from settings import *
from common_func import logInit
from time import time, sleep
import datetime
import pymongo


def get_mongo_db():
    for mongo_ip in MONGO_IPS:
        try:
            mongo_db = pymongo.MongoClient(mongo_ip, MONGO_PORT).anti_ban
            logging.info('[connect mongo] connect mongo succeed! %s:%d', mongo_ip, MONGO_PORT)
            return mongo_db
        except Exception, e:
            logging.warning(str(e))
            continue

if __name__ == "__main__":
    logInit(logging.DEBUG, 'logs/account_status_monitor.log', 10, True)
    mongo_db = get_mongo_db()
    for item in mongo_db.pptp_proxy.find({'status': 0}): ## all available proxy
        try:
            diff_time = time() - item['update_time']
            if (diff_time + 1) > int(item['lifetime']):
                mongo_db.pptp_proxy.update({'account_name': item['account_name']},
                                           {'$set': {'status': 2}}) ## proxy invalid
                logging.info('%s update status 2 %d:%d', item['account_name'], int(item['lifetime']), diff_time)
        except Exception, e:
            logging.error('someting erro! (%s)', str(e))
