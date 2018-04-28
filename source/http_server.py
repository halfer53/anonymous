# coding=utf-8
import os
import sys
sys.path.append('/tools/python_common')
from common_func import logInit
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from settings import *
from pptp_proxy import get_mongo_db, get_my_name
import logging
import urlparse
import json


class PPTPHandle(BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info('[GET] %s %s', self.client_address, self.path)

        ## parse request
        rs = urlparse.urlparse(self.path)
        q = urlparse.parse_qs(rs.query.lower())

        buf = ''

        if 'change' in q and q['change'][0] == '1':
            mongo_db = get_mongo_db()
            name = get_my_name()
            mongo_db.pptp_proxy.update(
                {'hostname': name},
                {'$set': {
                    'manual_change': True,
                }})
            logging.info('change ip [%s]', name)
        elif 'get_status' in q:
            mongo_db = get_mongo_db()
            name = get_my_name()
            item = mongo_db.pptp_proxy.find_one({'hostname': name})
            if item:
                del item['_id']
                buf = json.dumps(item)

        ## send response
        self.protocal_version = "HTTP/1.1"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(buf)


if __name__ == '__main__':
    DIR_PATH = os.path.split(os.path.realpath(__file__))[0]
    LOG_FILE = DIR_PATH + '/logs/' + __file__.replace('.py', '.log')
    logInit(logging.INFO, LOG_FILE, 0, True)

    httpd = HTTPServer(("", HTTP_PORT), PPTPHandle)
    logging.info('start http server port:%d', HTTP_PORT)
    httpd.serve_forever()
