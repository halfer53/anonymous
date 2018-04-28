# -*- coding: utf-8 -*
import os
import sys
sys.path.append('/tools/python_common')
sys.path.append('..')
import logging
from account import PptpAccount
from common_func import logInit


if __name__ == '__main__':
    file_path = 'account.txt'
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]

    logInit(logging.DEBUG, 'logs/account.log', 10, True)

    ac = PptpAccount('192.168.60.17:2181')
    ac.set_account_from_file(file_path, ' ')
