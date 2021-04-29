import redis
import datetime
import time
import os


def main():
    rhost = os.getenv('REDIS_NODE_ADDR', 'localhost')
    rport = os.getenv('REDIS_NODE_TCP_PORT', 6379)

    r = redis.Redis(host=rhost, port=rport, db=0)

    while True:
        now = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        print('Sending {0}'.format(now))
        r.publish('public-timestamp', now)
        time.sleep(1)


if __name__ == '__main__':
    main()
