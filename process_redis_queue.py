#!/usr/bin/env python3

import redis, hiredis
import ujson as json
import psycopg2
import sys
import time
import configparser
import logging
logging.basicConfig(level=logging.INFO)


r = redis.StrictRedis(host='localhost', port=6379, db=0)
Config = configparser.ConfigParser()
Config.read("config.ini")
db_pw = Config.get("Database", "password")
user = Config.get("Database", "username")
host = Config.get("Database", "host")
database = Config.get("Database", "database")
conn = psycopg2.connect(f"dbname='{database}' user='{user}' host='{host}' password='{db_pw}'")
cur = conn.cursor()
symbols_cache = {}

while True:
    for key in r.scan_iter("stocktwits:post:*"):
        key = key.decode()
        c = key.split(":")
        ticker = c[2]
        post = r.get(key)
        message = json.loads(post)
        symbols = message['symbols']
        symbol_id = None

        for symbol in symbols:
            if symbol['symbol'] not in symbols_cache:
                cur.execute("INSERT INTO symbol (id, symbol, title, watchlist_count) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", (symbol['id'], symbol['symbol'], symbol['title'], symbol['watchlist_count']))
                symbols_cache[symbol['symbol']] = symbol['id']
            if symbol['symbol'] == ticker:
                symbol_id = symbol['id']
        conn.commit()
        if symbol_id is None:
            logging.error("Could not find symbol id.")
            sys.exit()
        user_id = message['user']['id']
        id = message['id']
        created_at = message['created_at']
        #if 'user' in message and message['user'] is not None:
        #    user = message['user']
        #    cur.execute("""INSERT OR IGNORE INTO user (id, username, name, join_date, followers,
        #                   following, ideas, watchlist_stocks_count, like_count) VALUES (?,?,?,?,?,?,?,?,?)""", (
        #                   user['id'], user['username'], user['name'], user['join_date'], user['followers'],
        #                   user['following'], user['ideas'], user['watchlist_stocks_count'], user['like_count']))

#        if 'source' in message and message['source'] is not None:
#            source = message['source']
#            cur.execute("INSERT OR IGNORE INTO source (id, title, url) VALUES (?,?,?)", (source['id'], source['title'], source['url']))

#        if 'symbols' in message:
#            for symbol in message['symbols']:
#                cur.execute("INSERT OR IGNORE INTO symbol (id, symbol, title, watchlist_count) VALUES (?,?,?,?)", (symbol['id'], symbol['symbol'], symbol['title'], symbol['watchlist_count']))

        json_data = json.dumps(message, ensure_ascii=False, escape_forward_slashes=False)
        cur.execute("INSERT INTO post (id, user_id, symbol_id, data) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", (id, user_id, symbol_id, json_data))
        conn.commit()
        logging.info(f"Processed message id: {id}, ticker: {ticker}.")
        r.delete(key)

    time.sleep(.2)
