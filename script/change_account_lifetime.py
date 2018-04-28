# -*- coding: utf-8 -*
import os
import sys
import re
sys.path.append('/tools/python_common')
sys.path.append('../source')
import logging
from account import PptpAccount
from common_func import logInit
from settings import *

def usage():
    print '''
Usage:
    python %s <lifetime> [account name]
''' % (sys.argv[0])

if __name__ == '__main__':
    lifetime = 10
    account_name = ''
    if len(sys.argv) >= 2:
        lifetime = sys.argv[1]
        if re.match('\d+', lifetime) and int(lifetime) > 0:
            lifetime = int(lifetime)
        else:
            print 'Invalid Number!'
            usage()
            sys.exit(1)

        logInit(logging.DEBUG, 'logs/account.log', 10, True)
        ac = PptpAccount(ZOOKEEPER_HOSTS)

        if len(sys.argv) >= 3:
            for account_name in sys.argv[2:]:
                ac.change_account_lifetime(lifetime, account_name)
        else:
            ac.change_account_lifetime(lifetime)
    else:
        usage()

