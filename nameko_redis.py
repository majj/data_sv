# -*-coding:utf-8 -*

"""
nameko redis
"""
import traceback
from logging import getLogger

from nameko.extensions import DependencyProvider

from lib.redis_lib import RedisExt

log = getLogger("redis")

REDIS_KEY = "REDIS"


class Redis(DependencyProvider):
    def __init__(self, key, **options):

        self.key = key
        self.client = None

        self.options = {"decode_responses": True}

        self.options.update(options)

    def setup(self):
        redis_uris = self.container.config[REDIS_KEY]["URIS"]
        self.client_uri = redis_uris[self.key]

    def start(self):

        try:
            ### log.debug(dir(RedisExt))
            self.client = RedisExt.from_url(self.client_uri, **self.options)
            log.info("Connected to {}".format(self.client_uri))

            self.client.sha_d = {}

            sha_all = self.client.hscan("lua", match="lua_*")

            for key, sha in sha_all[1].items():
                self.client.sha_d[key] = sha

            ## TODO: remove in future?
            ## self._load_script()

            # self.client.lua_init()
        except:
            self.client = None
            log.error(traceback.format_exc())
            raise Exception("can't connect to Redis")

    def stop(self):
        self.client = None

    def kill(self):
        self.client = None

    def get_dependency(self, worker_ctx):
        return self.client

    """
    def _load_script(self):

        ## load lua scripts
        for key in self.container.config[REDIS_KEY]["LUA"]:

            script_path = self.container.config[REDIS_KEY]["LUA"][key]

            with open(script_path, "r") as fh:
                lua_script = fh.read()
                # if not hasattr(self.client, key):
                log.debug(key)
                multiply = self.client.register_script(lua_script)

                self.client.sha_d[key] = multiply.sha
                self.client.hset("lua", key, multiply.sha)
                self.client.hset("lua_src", key, lua_script)
                setattr(self.client, key, multiply)

        result = self.client.lua_init()
        log.debug("init " + result)


    """
