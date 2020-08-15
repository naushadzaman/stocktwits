#!/usr/bin/env python3

import requests
import ujson as json
import sys
import time
import psycopg2
import configparser
import yaml
import redis, hiredis
import sqlite3
import logging
import luminati as lm
import configparser
from queue import Queue
import threading
logging.basicConfig(level=logging.INFO)


class stocktwits:

    def __init__(self):

        self.BASE_URL = "https://api.stocktwits.com/api/2/"
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.RETRY_LIMIT = 5
        # Read Credentials
        Config = configparser.ConfigParser()
        Config.read("credentials.ini")
        luminati_user = Config.get("Luminati","username")
        luminati_pw = Config.get("Luminati","password")
        logging.debug("Creating a new luminati session...")
        self.session = lm.session(luminati_user, luminati_pw)
        logging.debug("Success!")

    def load_configuration(self):
        '''Load configuration file'''
        try:
            config_file_data = open(self.config_file, "r").read()
            self.config = yaml.safe_load(config_file_data)
        except Exception as e:
            logging.error(e)
            sys.exit()

    def streams(self, ticker=None, streams_type="symbol", **kwargs):
        '''Method to fetch posts for a particular ticker symbol'''
        params = {}
        params = kwargs
        if streams_type == "symbol":
            POSTS_URL = f"{self.BASE_URL}streams/symbol/{ticker}.json"
        elif streams_type == "trending":
            POSTS_URL = f"{self.BASE_URL}streams/trending.json"
        retries = self.RETRY_LIMIT

        while retries:
            logging.debug(f"{self.rate_limit_remaining} API calls remaining.")
            if self.rate_limit_remaining is not None and self.rate_limit_remaining < 1:
                wait_time_in_seconds = (self.rate_limit_reset - int(time.time())) + 1
                logging.info(f"Rate limit exhausted. Sleeping for {wait_time_in_seconds:,} seconds until next rate limit window.")
                time.sleep(wait_time_in_seconds)
            try:
                r = self.session.get(f"{POSTS_URL}", params=params)
            except requests.exceptions.ProxyError as e:
                retries -= 1
                continue
            response_headers = r.headers
            if 'X-RateLimit-Remaining' in response_headers:
                '''Sometimes the response headers do not have the rate-limit information so we need to check
                that they exist and if they don't, manually adjust the number of API calls remaining.'''
                self.rate_limit_remaining = int(response_headers['X-RateLimit-Remaining'])
                self.rate_limit_reset = int(response_headers['X-RateLimit-Reset'])
            else:
                if self.rate_limit_remaining is not None:
                    self.rate_limit_remaining -= 1
            if r.ok:
                return r.json()
            elif r.status_code == 429:
                self.rate_limit_remaining = 0
            else:
                logging.warning(f"Failed request. Received status code: {r.status_code}.")
                retries -= 1

def create_sqlite_db(db_name):

    conn = sqlite3.connect(f"{db_name}.db",timeout=60.0)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS post (id INT PRIMARY KEY, ticker TEXT, data TEXT)')
    c.execute('PRAGMA journal_mode = wal')
    return conn

def lookup_symbol_id(conn, symbol):

    c = conn.cursor()
    c.execute('SELECT id FROM symbol where symbol = %s', (symbol,))
    id = c.fetchone()
    conn.commit()
    if id is None:
        logging.warning(f"Could not find id for symbol '{symbol}'.")
        return None
    else:
        return id[0]

def get_min_id_for_symbol_id(conn, symbol_id):

    c = conn.cursor()
    c.execute('SELECT min(id) FROM post WHERE symbol_id = %s', (symbol_id,))
    id = c.fetchone()
    conn.commit()
    if id is None:
        return None
    else:
        return id[0]

def get_top_symbols(conn, n=25):

    c = conn.cursor()
    c.execute(f"SELECT symbol FROM symbol ORDER BY watchlist_count DESC LIMIT %s", (n,))
    symbols = c.fetchall()
    return [symbol[0] for symbol in symbols]


def fetch_posts(q):

    st = stocktwits()
    red = redis.StrictRedis(host='localhost', port=6379, db=0)
    Config = configparser.ConfigParser()
    Config.read("config.ini")
    db_pw = Config.get("Database", "password")
    user = Config.get("Database", "username")
    host = Config.get("Database", "host")
    database = Config.get("Database", "database")
    conn = psycopg2.connect(f"dbname='{database}' user='{user}' host='{host}' password='{db_pw}'")

    while True:
        ticker = q.get()
        if ticker is None:
            return
        symbol_id = lookup_symbol_id(conn, ticker)
        min_id = get_min_id_for_symbol_id(conn, symbol_id)
        count = 0

        while True:
            data = st.streams(ticker=ticker, streams_type="symbol", max=min_id)
            retrieved_utc = int(time.time())
            messages = data['messages']
            created_at = None

            if not messages:
                break

            pipeline = red.pipeline()
            for message in messages:
                id = message['id']
                message['retrieved_utc'] = retrieved_utc
                created_at = message['created_at']

                json_data = json.dumps(message, ensure_ascii=False, escape_forward_slashes=False)
                pipeline.set(f"stocktwits:post:{ticker}:{id}", json_data)
                if min_id is None or id < min_id:
                    min_id = id

            pipeline.execute()
            logging.info(f"Symbol: {ticker} -- Current date position: {created_at} | ID: {min_id:,} | Rate-limit remaining: {st.rate_limit_remaining:,}.")

            count += 1

            if count >= 25:
                break

Config = configparser.ConfigParser()
Config.read("config.ini")
db_pw = Config.get("Database", "password")
user = Config.get("Database", "username")
host = Config.get("Database", "host")
database = Config.get("Database", "database")
conn = psycopg2.connect(f"dbname='{database}' user='{user}' host='{host}' password='{db_pw}'")
NUMBER_OF_WORKERS = 50
queue = Queue(maxsize=NUMBER_OF_WORKERS+1)



def setup_workers():

    global threads
    threads = []

    logging.info("Setting up workers.")
    for x in range(NUMBER_OF_WORKERS):
        t = threading.Thread(target=fetch_posts, args=(queue,))
        threads.append(t)
        t.start()

top_symbols = get_top_symbols(conn, 50000)
setup_workers()

for idx, symbol in enumerate(top_symbols):
    queue.put(symbol)
    print(f"{idx:,} symbols sent to workers.")

for x in range(NUMBER_OF_WORKERS):
    queue.put(None)

for thread in threads:
    thread.join()

