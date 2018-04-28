import sys
sys.path.append('..')
import pymongo
from settings import MONGO_IPS, MONGO_PORT


if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.exit(0)

    mongo_db = None
    for mongo_ip in MONGO_IPS:
        try:
            mongo_db = pymongo.MongoClient(mongo_ip, MONGO_PORT).anti_ban
        except Exception, e:
            print e

    if not mongo_db:
        print "mongo not connected"
        sys.exit(1)

    for ip in sys.argv[1:]:
        try:
            mongo_db.pptp_route.insert_one({'src': ip})
            print 'insert succeed: ', ip
        except pymongo.errors.DuplicateKeyError:
            continue
