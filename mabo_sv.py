# -*-coding:utf-8 -*
"""
mabo services(web api)

"""
from __future__ import absolute_import

import json
import time
import traceback
from logging import getLogger

from nameko.constants import DEFAULT_HEARTBEAT
from nameko.dependency_providers import Config
from nameko.rpc import RpcProxy, rpc
from nameko.timer import timer
from nameko.web.handlers import http
from nameko_redis import Redis
from werkzeug.wrappers import Response

import constants
from lib.utils import parse_ip

_version = "0.2"
_author = "mabotech"

### import ujson as json
### import requests

log = getLogger("mabo_sv")


class MaboService:
    """ web api """

    name = "mabo_service"

    conf = Config()

    db = RpcProxy("oracle_service")

    ### redis = RpcProxy("redis_service")
    redis = Redis("development")

    @timer(interval=constants.INTERVAL_HEARTBEAT)
    def heartbeat(self):
        """set heartbeat time to redis[key: heartbeat] """
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        ## timestamp = 1000 * time.time()
        log.debug("heartbeat: {}".format(now))
        try:
            self.redis.set("heartbeat", now)
        except Exception as ex:
            log.error(ex)

    #################################################################
    ## Redis Lua
    #################################################################
    @http("POST", "/lua/register")
    def post_lua_register(self, request):
        """register lua in redis """

        json_text = request.get_data(as_text=True)
        data = json.loads(json_text)
        # log.debug(data)
        for key, lua_script in data.items():

            result = self.redis.register(key, lua_script)
            # log.debug(result)
        return json.dumps(self.redis.get_sha())

    @http("GET", "/lua/register2")
    def get_lua_register2(self, request):
        """register lua from redis lua_src by name """

        name = request.args.get("name")
        result = self.redis.register2(name)

    @http("GET","/lua/get_src")
    def get_lua_src(self, request):
        pass

    #################################################################
    ## 数据库
    #################################################################
    @http("GET", "/ora")
    def get_data(self, request):
        """ work Instructions """

        wi = {"wiurl": "", "tdurl": ""}

        IP = request.args.get("IP", request.remote_addr)

        type_, wskey, addr, ip_, group, timestamp = parse_ip(IP)

        data = self.db.call_proc("sp_test", ["string"], "array")

        return json.dumps({"value": data, "IP": IP, "id": 1})

    #################################################################
    ## JSONRPC
    #################################################################
    @http("POST", "/jsonrpc/call")
    def call_jsonrpc(self, request):
        """ jsonrpc """
        """
        --> {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}
        <-- {"jsonrpc": "2.0", "result": 19, "id": 1}

        --> {"jsonrpc": "2.0", "method": "foobar", "id": "1"}
        <-- {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "1"}

        """
        IP: str = request.args.get("IP", request.remote_addr)

        type_, wskey, addr, ip_, group, timestamp = parse_ip(IP)

        json_text: str = request.get_data(as_text=True)

        res = json.loads(json_text)

        method = res["method"]
        params = res["params"]

        id_ = res["id"]
        # call method(params) here,
        # redis lua ; pg function/stored procedure; oracle sp...

        mtype: list = method.split("_")[0]

        if mtype == "lua":
            """lua in redis"""
            try:
                result = self.redis.call_lua(
                    method=method,
                    keys=[group],
                    args=[json.dumps(params), IP, id_, timestamp],
                )

                data = {
                    "jsonrpc": "2.0",
                    "result": json.loads(result),
                    "id": id_
                }
            except Exception as ex:
                log.error(ex)
                raise (Exception(repr(ex)))

        elif mtype == "ora":
            """oracle"""
            data = ["ora"]

        elif mtype == "ht":
            """http"""
            data = [mtype]

        elif mtype == "pg":
            """postgresql"""
            data = [mtype]

        elif mtype == "py":
            """python"""
            data = []

        else:

            data = {"jsonrpc": "2.0", "result": data, "id": id_}

        return json.dumps(data)

    #################################################################
    ## GRAFANA: for grafana simple JSON\InfluxDB
    #################################################################
    @http("GET", "/")
    def root_get(self, request):
        """"""

        return "service list"

    @http("POST", "/")
    def root_post(self, request):
        """"""

        return "root"

    @http("POST", "/search")
    def search(self, request):
        """"""

        json_text = request.get_data(as_text=True)

        log.debug(json_text)

        data = ["upper_25", "upper_50", "upper_75", "upper_90", "upper_95"]

        return json.dumps(data)

    @http("GET", "/query")
    def query_get(self, request):
        """
        datasource: influxDB
        """
        IP = request.args.get("IP", request.remote_addr)

        type_, wskey, addr, ip_, group, timestamp = parse_ip(IP)

        db = request.args.get("db")
        q = request.args.get("q")
        epoch = request.args.get("epoch")

        log.debug(db)
        log.debug(q)
        log.debug(epoch)

        a1 = request.args.get("IP")
        # type = "table"
        d1 = []
        d2 = []
        for i in range(1, 5):
            d1.append([i * i, 1000 * time.time() - 1000 * i])
            d2.append([10 + i * i, 1000 * time.time() - 1000 * i])

        data = {
            "results": [{
                "series": [{
                    "name":
                    "node_st",
                    "columns": ["time", "eqpt", "desc", "status"],
                    "values": [
                        [1000 * time.time(), "HPU", "Running", 2],
                        [1452858402099, "BEP", "Running", 2],
                        [1452858402121, "BEP-M1", "Running", 2],
                        [1452858402152, "BEP-M2", "Running", 2],
                        [1452858402175, "AVL", "Off", 1],
                        [1452858402199, "AVL-M1", "Off", 1],
                        [1452858402220, "DOOR", "Running", 2],
                    ],
                }]
            }]
        }
        return json.dumps(data)

    @http("POST", "/query")
    def query_post(self, request):
        """
        datasource: JSON
        """

        json_text = request.get_data(as_text=True)

        log.debug(json_text)

        type = "table"

        if type == "table":
            d1 = []
            d2 = []
            for i in range(1, 5):
                d1.append([i * i, 1000 * time.time() - 1000 * i])
                d2.append([10 + i * i, 1000 * time.time() - 1000 * i])

            data = [
                {
                    "target": "upper_75",
                    "datapoints": d1
                },  # The field being queried for
                {
                    "target": "upper_90",
                    "datapoints": d2
                },
            ]
            return json.dumps(data)

        elif type == "timeseries":
            data = []

            return json.dumps(data)
        else:
            data = []

            return json.dumps(data)

    @http("POST,OPTIONS", "/annotations")
    def get_annotations(self, request):
        """"""

        json_text = request.get_data(as_text=True)

        log.debug(json_text)

        data = [{
            "text":
            "text shown in body",  # Text for the annotation. (required)
            "title":
            "Annotation Title",  # // The title for the annotation tooltip. (optional)
            "isRegion":
            True,  # // Whether is region. (optional) (http://docs.grafana.org/reference/annotations/#adding-regions-events)
            "time": 1000 * time.time() -
            1000,  # // Time since UNIX Epoch in milliseconds. (required)
            "timeEnd": 1000 * time.time(
            ),  # // Time since UNIX Epoch in milliseconds (required if `isRegion` is true )
            "tags": ["tag1"],  # // Tags for the annotation. (optional)
        }]
        """
        OPTIONS:
        Access-Control-Allow-Headers:accept, content-type
        Access-Control-Allow-Methods:POST
        Access-Control-Allow-Origin:*
        """
        return json.dumps(data)

    @http("GET,POST", "/tag-keys")
    def get_tag_keys(self, request):
        """"""

        json_text = request.get_data(as_text=True)

        log.debug(json_text)

        return ""

    @http("GET,POST", "/tag-values")
    def get_tag_values(self, request):
        """"""

        json_text = request.get_data(as_text=True)

        log.debug(json_text)

        return ""
