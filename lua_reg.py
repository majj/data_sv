# -*-coding:utf-8 -*
"""
lua_reg.py
register lua files to redis by calling mabo_sv
"""

##
## load lua script
## EVAL -> Register -> Call

import json
import time
from pathlib import Path

from urllib3.exceptions import ConnectionError, NewConnectionError

import redis
import requests

LUA_REG_URL = "http://127.0.0.1:8001/lua/register"


class LuaReg(object):
    """"""

    def __init__(self):
        """"""

        self.url = LUA_REG_URL

        ### self.redis = redis.Redis(host="127.0.0.1", port=6379, db=0)

        ### z = self.redis.script_flush()

    def run(self, fn):
        """run """

        base_name = Path(fn).name

        key = "_".join(["lua", base_name.split(".")[0]])

        with open(fn, "r") as fh:

            lua_script = fh.read()

            payload = {key: lua_script}

            r = requests.post(self.url, data=json.dumps(payload))

            result = json.loads(r.text)

            print("{}:{}".format(key, result[key]))
            ### print(lua_script)
            print("==" * 20)


def main(lua_pattern: str):
    """reload lua from conf/lua/"""

    lua_files = Path().cwd().joinpath("conf", "lua").glob(lua_pattern)

    reg = LuaReg()

    for fn in lua_files:
        try:
            reg.run(fn)
            pass
        except Exception as ex:
            print("{} load failed".format(fn))
            print(ex)
            break
            ### raise (Exception(repr(ex)))


if __name__ == "__main__":

    lua_pattern = "*.lua"

    main(lua_pattern)
