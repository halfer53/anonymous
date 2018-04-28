#encoding=gb18030
import sys
import requests
import os
from time import time, sleep
import re
import sys
import json
import re
import logging
sys.path.append('/tools/python_common')
from common_func import logInit

reload(sys)
sys.setdefaultencoding('gb18030')

USERAGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.36'


class IPManager():
    def __init__(self, server, username, password, mongo_db=None, last_time=0):
        self.server = server
        self.username = username
        self.password = password
        self.mongo_db = mongo_db
        self.last_time = last_time
        self.default_gw = self.get_default_gw()
        self.logger = logging.getLogger('IP Manager')

    def __del__(self):
        self.close_pptp()

    def get_default_gw(self):
        r = os.popen('route -n').read()
        gw = ''
        for line in r.split('\n'):
            items = re.split(r'\s+', line)
            if items and items[0] == '0.0.0.0' and items[1] != '0.0.0.0':
                gw = items[1]
        if gw:
            f = open('default_gw', 'w')
            f.write(gw)
            f.close()
        elif os.path.isfile('default_gw'):
            f = open('default_gw', 'r')
            gw = f.read()
            f.close()
        return gw

    def add_internal_route(self, ip):
        if self.default_gw:
            ip = ip.strip()
            if ip[-3:] == '/32':
                os.popen('route add -host %s gw %s' % (ip, self.default_gw))
            else:
                os.popen('route add -net %s gw %s' % (ip, self.default_gw))
            return True
        else:
            self.logger.warning('add internal route failed! not find default gw!')
            return False

    def get_ip(self):
        url = 'http://111.161.24.2:9001'
        try:
            r = requests.get(url, timeout=5)
            item = json.loads(r.text)
            return item['ip']
        except Exception, e:
            self.logger.error('get ip failed! %s', str(e))
            return ''

    def link_pptp(self):
        self.logger.info('link start %s %s %s', self.server, self.username, self.password)
        cmd = '/usr/sbin/pptpsetup --create hcvpn --server %s --username %s --password %s --encrypt --start' \
                              % (self.server, self.username, self.password)
        ret_create = os.popen(cmd).read()
        if ret_create and ret_create.find('address') > 0:
            num = re.findall('(?<=Using interface ppp)\d+', ret_create)
            num = num[0] if num else '0'
            p_name = 'ppp' + num
            os.popen('echo "persist" >> /etc/ppp/peers/hcvpn')
            os.popen('route del default')
            os.popen('route del default')
            os.popen('route add default dev %s' % (p_name))
            os.popen('service pptpd start')
            return True
        self.logger.error('link failed! %s', ret_create)
        return False

    def close_pptp(self):
        os.popen('service pptpd stop')
        os.popen('/usr/sbin/pptpsetup --delete hcvpn')
        os.popen('''ps aux | grep ppp | awk -F " " '{printf $2\"\\n\"}' | xargs kill -9''')
        os.popen('route add default gw %s' % (self.default_gw))

    def pptp_living(self):
        has_route = os.popen('''route -n | awk -F " " '{printf $8}' | grep ppp''').read()
        if has_route:
            return True
        return False

    def change_ip(self):
        new_ip = ''
        while True:
            self.close_pptp()
            if self.link_pptp():
                new_ip = self.get_ip()
                self.logger.info('change ip to %s', new_ip)
                return new_ip
            sleep(1)

if __name__ == '__main__':
    dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
    log_file = dirname + '/logs/ip_manager.log'
    logInit(logging.DEBUG, log_file, 10, True)

    m = IPManager('hcpptp001.ros2.chengshu.com', 'hcpptp001', '98273452')
    t1 = time()
    ip = m.change_ip()
    t2 = time()
    print t2-t1, ip

