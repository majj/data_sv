# -*-coding:utf-8 -*
"""

"""
_version = "2.0"
_author = "mabotech"

from logging import getLogger

from redis import StrictRedis

log = getLogger("redis_lib")

class RedisExt(StrictRedis):
    def call_lua(self, method, keys, args):
        """"""
        sha = self.sha_d.get(method, None)

        if sha == None:
            raise Exception(">>> no {}".format(method))
        else:
            return self.evalsha(sha, len(keys), *keys, *args)
            # sha = self.client.script_load(script)

    def call_lua2(self, method, keys, args):
        """"""
        ## self.client.method(keys, args)  # call lua script
        try:
            result = getattr(self, method)(keys, args)
        except Exception as ex:
            # result = traceback.format_exc()
            log.error(ex)
            result = getattr(self, method).script

        return result

    def get_sha(self):
        """"""
        return self.sha_d

    def register(self, key, lua_script):
        """"""
        try:
            # e = self.client.eval(lua_script, 1, *["key"],*[])
            # multiply = self.client.register_script(lua_script)
            sha = self.script_load(lua_script)
            # self.client.sha_d[key] = multiply.sha
            self.hset("lua", key, sha)
            self.hset("lua_src", key, lua_script)
            self.sha_d[key] = sha
            # log.debug(lua_script)
        except Exception as ex:
            raise Exception(repr(ex))
            log.error(ex)

        return self.sha_d[key]

    def register2(self, name):

        try:
            lua_script = self.hget("lua_src", name)
            return self.register(name, lua_script)
        except Exception as ex:
            log.error(ex)
            return "error"

    def register3(self, key, lua_script):

        try:
            # e = self.client.eval(lua_script, 1, *["key"],*[])

            multiply = self.register_script(lua_script)
            self.sha_d[key] = multiply.sha

            setattr(self, key, multiply)

        except Exception as ex:
            # raise Exception(repr(ex))
            log.error(ex)

        return self.sha_d[key]


def test():
    pass


if __name__ == "__main__":
    test()
