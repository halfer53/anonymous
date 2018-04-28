# -*- coding: utf-8 -*
import os
import sys
import logging
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
import json

class PptpAccount():
    def __init__(self, zk_hosts, timeout=10):
        self.zk_hosts = zk_hosts
        self.timeout = timeout
        self.zk = KazooClient(hosts=self.zk_hosts)
        self.link_zookeeper()

    def __del__(self):
        if self.zk.state != 'LOST':
            self.zk.stop()

    def link_zookeeper(self):
        err_msg = ''
        try:
            self.zk.start(self.timeout)
        except Exception, e:
            err_msg = str(e)

        if self.zk.state == 'CONNECTED':
            return True
        else:
            logging.error('link zookeeper failed! (%s) (%s)', self.zk_hosts, err_msg)
            return False

    def set_account(self, host, username, password, lifetime=600):
        if self.zk.state == 'LOST':
            self.link_zookeeper()

        if self.zk.state != 'LOST':
            info = {
                'host': host,
                'username': username,
                'password': password,
                'lifetime': lifetime
            }

            ##create(self, path, value=b"", acl=None, ephemeral=False, sequence=False, makepath=False)
            path = '/search/spider/hc_pptp_account/%s' % (':'.join([info['host'], info['username']]))
            try:
                self.zk.create(path, json.dumps(info))
                logging.info('path [%s] create succeed!', path)
                return True
            except NodeExistsError:
                logging.warning('path [%s] has exists!', path)
            except Exception, e:
                logging.warning('path [%s] create failed! (%s)', path, str(e))
        else:
            logging.error('zookeeper state abnormal!')
        return False

    def set_account_from_file(self, file_path, seg=' '):
        if file_path and os.path.isfile(file_path):
            with open(file_path, 'r') as fp:
                for l in fp:
                    item = l.strip().split(seg)
                    if len(item) != 4:
                        logging.warning('account record formart split with "%s" failed! (%s)', seg, l)
                        continue
                    host, username, password, lifetime = item
                    self.set_account(host, username, password, lifetime)
        else:
            logging.warning('file_path open failed! (%s)', file_path)

    def get_account(self, value=''):
        if self.zk.state == 'LOST':
            self.link_zookeeper()

        if self.zk.state != 'LOST':
            ##create(self, path, value=b"", acl=None, ephemeral=False, sequence=False, makepath=False)
            for account_name in self.zk.get_children('/search/spider/hc_pptp_account'):
                try:
                    path = '/search/spider/hc_pptp_account/%s/using' % (account_name)
                    self.zk.create(path, value, None, True)

                    path = '/search/spider/hc_pptp_account/%s' % (account_name)
                    item = self.zk.get(path)
                    if item:
                        info = item[0]
                        info = json.loads(info)
                        info['account_name'] = account_name
                        logging.info('get account succeed! from=%s info=%s', value, info)
                        return info
                except NodeExistsError:
                    continue
                except Exception, e:
                    logging.warning('get account path [%s] failed! (%s)', path, str(e))

            logging.warning('no avliable account!')
            return''
        else:
            logging.error('zookeeper state abnormal!')
            return ''

    def change_account_lifetime(self, lifetime, account_name=''):
        if self.zk.state == 'LOST':
            self.link_zookeeper()

        if self.zk.state != 'LOST':
            accounts = []
            if account_name:
                accounts.append(account_name)
            else:
                for account_name in self.zk.get_children('/search/spider/hc_pptp_account'):
                    accounts.append(account_name)

            for account_name in accounts:
                path = '/search/spider/hc_pptp_account/%s' % (account_name)
                item = self.zk.get(path)
                if item:
                    info = item[0]
                    info = json.loads(info)
                    old_lifetime = info['lifetime']
                    info['lifetime'] = str(lifetime)
                    self.zk.set(path, json.dumps(info))
                    logging.info('change account lifetime succeed! %s %s-->%s', account_name, old_lifetime, str(lifetime))

if __name__ == '__main__':
    ## test
    sys.path.append('/tools/python_common')
    from common_func import logInit
    logInit(logging.DEBUG, 'logs/account.log', 10, True)

    ac = PptpAccount('192.168.60.17:2181')
    print ac.set_account('pptp1232.ros2.chengshu.com', 'pptp1232', '99892', 60)
    a = input()
    for _ in range(3):
        info = ac.get_account('spider_tj_03:a902b3c2d')
        print info
        a = input()

    # ac.change_account_lifetime(10)
    # ac.change_account_lifetime(10, 'hcpptp002.ros2.chengshu.com:hcpptp002')
