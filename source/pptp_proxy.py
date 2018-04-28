#encoding=utf-8
from settings import *
import os
import sys
import logging
sys.path.append('/tools/python_common')
from common_func import logInit
from common_func import MyEncoder
from time import time, sleep
import datetime
import pymongo
import json
from ip_manager import IPManager
from account import PptpAccount
import random


def get_mongo_db():
    for mongo_ip in MONGO_IPS:
        try:
            mongo_db = pymongo.MongoClient(mongo_ip, MONGO_PORT).anti_ban
            logging.info('[connect mongo] connect mongo succeed! %s:%d', mongo_ip, MONGO_PORT)
            return mongo_db
        except Exception, e:
            logging.warning(str(e))
            continue

def get_my_name():
    f_name = os.getenv('FATHER_HOST_NAME')
    f_name = f_name if f_name else 'unknown_hostname'
    hostname = os.popen('hostname').read()
    return ':'.join([f_name, hostname.strip()])


if __name__ == '__main__':
    ## 0. init log
    dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
    log_file = dirname + '/logs/pptp_proxy.log'
    logInit(logging.INFO, log_file, 10, True)
    logging.info('start')

    ## 0. get name and proxy ip
    proxy_port = int(os.getenv('PROXY_PORT'))
    proxy_ip = os.getenv('PROXY_IP')
    proxy_tj_ip = os.getenv('PROXY_TJ_IP')
    name = get_my_name()
    if not proxy_ip and not proxy_tj_ip:
        logging.error('not find proxy ip! please run docker with "-e PROXY_IP=X.X.X.X"!')
        sys.exit(1)

    ## 1. connect mongo
    mongo_db = get_mongo_db()

    ## 2. get pptp account from zookeeper
    ac = PptpAccount(ZOOKEEPER_HOSTS)
    account_info = {}
    while True:
        account_info = ac.get_account(name)
        if not account_info:
            logging.warning('get account empty sleep 10s')
            sleep(10)
            continue
        break

    ## change mongo hostname
    mongo_db.pptp_proxy.update_one({'account_name': account_info['account_name']}, {'$set': {'hostname': name}})

    ## 3. create ip manager object and add internal route
    m = IPManager(account_info['host'], account_info['username'], account_info['password'], account_info['lifetime'])
    mongo_cur = mongo_db.pptp_route.find({}, {'src': 1})
    for internal_ip in mongo_cur:
        m.add_internal_route(internal_ip['src'].strip())

    retry_times = 3
    ip = m.change_ip()
    while True:
        proxy_info = mongo_db.pptp_proxy.find_one({'account_name': account_info['account_name']})

        ## 3.1 judge pptp has living
        if not m.pptp_living():
            ip = m.change_ip()
            logging.info('pptp not living, change ip: %s', ip)

        cur_time = time()
        lifetime = int(proxy_info.get('lifetime', int(account_info.get('lifetime', 20)))) if proxy_info else int(account_info.get('lifetime', 20))
        cur_proxy_info = {
            'hostname': name,
            'net_ip': ip,
            'proxy_port': proxy_port,
            'proxy_ip': proxy_ip,
            'proxy_tj_ip': proxy_tj_ip,
            'status': 0, ## OK
            'account_name': account_info['account_name'],
            'update_time': cur_time,
            'lifetime': lifetime,
            'manual_change': False,
        }
        ## 3.2 insert infomation to mongo
        if not proxy_info:
            mongo_db.pptp_proxy.insert_one(cur_proxy_info)
            continue

        ## 3.3 judge lifetime is over
        if not proxy_info.get('manual_change', False):
            if lifetime < 0 \
               or (
                   (cur_time - proxy_info.get('update_time',cur_time) > 0)
                and (cur_time - proxy_info.get('update_time',cur_time) < lifetime)
               ):
                ip = m.get_ip()
                if not ip:
                    retry_times -= 1
                else:
                    retry_times = 3

                if ip or retry_times > 0:
                    logging.info('no time to change ip. %s [%d:%d]', ip, lifetime, cur_time - proxy_info.get('update_time', cur_time))
                    sleep(1)
                    continue

        retry_times = 3
        ## 3.4 change ip
        logging.info('change ip %d:%d', lifetime, cur_time - proxy_info.get('update_time', cur_time))
        mongo_db.pptp_proxy.update({'account_name': account_info['account_name']},
                                   {'$set': {
                                       'status': 1, ## CHANGING
                                   }})
        ip = m.change_ip()

        ## 3.5 update mongo pptp_proxy
        cur_proxy_info['net_ip'] = ip
        cur_proxy_info['update_time'] = time()
        del cur_proxy_info['account_name']
        mongo_db.pptp_proxy.update({'account_name': account_info['account_name']},
                                   {'$set': cur_proxy_info})

        ## 3.6 update mongo pptp_account_count
        cur_date = datetime.datetime.now()
        cur_hour = cur_date - datetime.timedelta(minutes=cur_date.minute, seconds=cur_date.second, microseconds=cur_date.microsecond)
        mongo_db.pptp_account_count.update({'account_name': account_info['account_name'], "run_time": cur_hour},
                                           {'$set': {'last_change_time': cur_date, 'life_time': lifetime},
                                            "$inc": {'change_ok_times': 1}},
                                           True, True)
