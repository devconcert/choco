#-*- coding: utf-8 -*-
"""
choco.py - An KakaoTalk Bot
Copyright 2014, ssut
Licensed under the MIT License.

Do you like chocopy? :)
"""

import time
import os
import sys
import base64
import redis
from multiprocessing import Process, Queue

from lib.endpoint import Endpoint
from lib.run_async import run_async

home = os.getcwd()
sys.path.append(os.path.join(home, 'modules'))
sys.path.append(os.path.join(home, 'pykakao'))
from pykakao import kakaotalk

class Choco(object):
    def __init__(self, config):
        self.config = config
        self.queue = Queue(10000)
        self.pool = [Process(target=self.process) for i in range(config.WORKER_COUNT)]
        self.exit = False
        self.kakao = None

        redis_pool = redis.ConnectionPool(host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD)
        self.cache = redis.Redis(connection_pool=redis_pool)
        self.module = Endpoint()

        auth_mail = self.cache.hget('choco_auth', 'mail')
        auth_pass = self.cache.hget('choco_auth', 'password')
        auth_client = self.cache.hget('choco_auth', 'client')
        auth_uuid = base64.b64encode(self.cache.hget('choco_auth', 'uuid'))

        if not auth_mail:
            print >> sys.stderr, "Authenticate failed: email address not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_pass:
            print >> sys.stderr, "Authenticate failed: password not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_client:
            print >> sys.stderr, "Authenticate failed: client name not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)
        elif not auth_uuid:
            print >> sys.stderr, "Authenticate failed: uuid not found\n" + \
                "Please check config.py and set 'choco_auth' to redis server"
            sys.exit(1)

        self.load_module()
        if self.auth_kakao(auth_mail, auth_pass, auth_client, auth_uuid):
            print >> sys.stdout, 'Successfully connected to KakaoTalk server'

    def load_module(self):
        from modules import set_endpoint, module_loader
        set_endpoint(self.module)
        module_loader(home, self.config)

    def auth_kakao(self, mail, password, client, uuid):
        user_session = self.cache.hget('choco_session', 'key')
        user_id = self.cache.hget('choco_session', 'id')

        if not user_session or not user_id:
            self.kakao = kakaotalk(debug=self.config.DEBUG)
            print (mail, password, client, uuid)
            auth_result = self.kakao.auth(mail, password, client, uuid)
            if auth_result is False:
                print >> sys.stderr, "KakaoTalk auth failed"
                sys.exit(1)
            else:
                login_result = self.kakao.login(timeout=15)
                if login_result is False:
                    print >> sys.stderr, "KakaoTalk login failed"
                    sys.exit(1)
                else:
                    self.cache.hset('choco_session', 'key', self.kakao.session_key)
                    self.cache.hset('choco_session', 'id', self.kakao.user_id)
        else:
            self.kakao = kakaotalk(user_session, client, user_id,
                debug=self.config.DEBUG)
            login_result = self.kakao.login(timeout=15)
            if login_result is False:
                print >> sys.stderr, "KakaoTalk login failed"
                sys.exit(1)

        return True


    @staticmethod
    def run(config):
        bot = Choco(config)
        for p in bot.pool:
            p.start()
        bot.watch()

    def watch(self):
        while True:
            pass

    def process(self):
        pass

    @run_async
    def dispatch(self):
        pass