# -*-coding:utf-8 -*
"""
data services(web api) for ACEC

"""
from __future__ import absolute_import

_version = "0.2"
_author = "mabotech"

import logging
import traceback
import requests

import json
import time

from werkzeug.wrappers import Response

from nameko.dependency_providers import Config
from nameko.rpc import rpc, RpcProxy
from nameko.timer import timer
from nameko.web.handlers import http
from nameko.constants import DEFAULT_HEARTBEAT

from nameko_redis import Redis

from lib.utils import parse_ip
import constants

log = logging.getLogger("data_sv")


class HttpService:
    """ web api """

    name = "http_service"

    conf = Config()

    db = RpcProxy("oracle_service")

    ### redis = RpcProxy("redis_service")
    redis = Redis("development")

    @timer(interval=constants.INTERVAL_HEARTBEAT)
    def heartbeat(self):
        """set heartbeat time to redis[key: heartbeat] """
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = 1000 * time.time()
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

    #################################################################
    ## 用户
    #################################################################
    @http("GET,POST", "/api/autologin")
    def auto_login(self, cookies):
        """"""
        callback = request.args.get("callback", None)
        try:
            redirect_to = ""
            if "redirect_to" in cookies:
                redirect_to = cookies["redirect_to"]
                res = {"is_login": 1, "redirect_to": redirect_to}
                return "{}({})".format(callback, res)
        except Exception as e:
            log.error(e)

    ## 获得登陆账户
    @http("GET", "/api/user/list")
    def get_user_list(self, request):
        """ get operators for this(IP) workstation """
        ##['pic_url',  'employeeno', 'name', 'status', 'zpq']

        IP = request.args.get("IP", request.remote_addr)
        callback = request.args.get("callback", None)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        result = self.db.call_proc(
            "sp_ws_emp",
            ["wip_order", "order_type", "operation", "step", "<CURSOR>"],
            "array",
        )

        empinfo = []

        tmp = result[4]

        for item in tmp:
            employeeno = item["employeeno"]
            login_ts = self.redis.hget("login:" + employeeno, "login_ts")
            if login_ts == None:
                item["login"] = False
            elif timestamp - float(login_ts) < 60 * 60 * 8 * 1000:
                item["login"] = True
            else:
                item["login"] = True
            empinfo.append(item)

        data = json.dumps({"jsonrpc": "2.0", "result": empinfo, "id": 1})

        if callback == None:
            return data
        else:
            return "{}({});".format(callback, data)

    @http("GET", "/api/user/login")
    def get_user_login(self, request):
        """"""
        ## Apriso ->

        callback = request.args.get("callback", None)

        id_ = request.args.get("id", 1)

        ### log.debug("{},{}".format(callback,id))

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        ### group = "ws:{}".format(wskey)

        payload = self.redis.call_lua(
            method="lua_user_get", keys=[group], args=[id_, timestamp])
        if callback == None:
            return Response(payload, status=200, mimetype="application/json")
        else:
            return "{}({});".format(callback, payload)

    @http("GET", "/api/user/scan")
    def scan_user(self, request):
        """"""
        ## IC scanner ->
        ## /api/user/scan?ic=4253955683

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        ic = request.args.get("ic", 1)
        id_ = request.args.get("id", 1)

        employeeNo = self.redis.call_lua(
            method="lua_user_scan", keys=[group], args=[ic, id_, timestamp])
        if employeeNo == "":
            return "user_not_found"
        else:
            ## submit order in db
            # result = self.db.call_proc("AP_3DXML.completeWipOrder", [employeeNo, '<NUMBER>'])
            # return json.dumps( {"jsonrpc": "2.0", "result": result, "id": id})
            return employeeNo

    ## 添加员工IC、EmployeeNo到Redis
    @http("POST", "/api/user/add")
    def add_user(self, request):
        ## add user ic & id to Redis
        ## /api/user/add?ic=4253955683&id=ADMIN
        """
        {"jsonrpc":"2.0", id=1, method="c1", params=[]}
        """
        json_text = request.get_data(as_text=True)

        id_ = request.args.get("id", 1)

        ic = request.args.get("ic")
        userid = request.args.get("userid")

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        result = self.redis.call_lua(
            method="lua_user_add", keys=[group], args=[ic, userid, timestamp])
        return "OK"

    #################################################################
    ## 零件
    #################################################################
    @http("GET", "/api/part/list")
    def get_part_list(self, request):
        """ parts as build """

        info = {"零件号": "", "零件名": "", "序列号": "", "装配人": "", "专配时间": ""}

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        ### q =self.conf.get("ORACLE")["QUERY"]

        ### ## rpc in ora_sv
        ### data1 = self.db.query(q["operators"], ['a'])
        result = self.db.call_proc("sp_get_parts", ["order1", "<CURSOR>"],
                                   "array")

        return json.dumps({"jsonrpc": "2.0", "result": result, "id": 1})

    @http("GET", "/api/part/<string:step>")
    def get_wi_part(self, request, step):
        """
        step: curr, next
        """

        info = {"零件号": "", "零件名": "", "序列号": "", "装配人": "", "专配时间": ""}

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        part = self.redis.hget(group, "part")
        changed = self.redis.hget(group, "changed")

        if changed == "1":
            self.redis.hset(group, "changed", 0)

        return json.dumps({"step": step, "part": part, "changed": changed})

    @http("GET", "/api/part/set")
    def set_part(self, request):
        """
        Apriso -> 设定零件
        """
        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        part = request.args.get("part")
        next = request.args.get("next")
        id_ = request.args.get("id", 1)
        callback = request.args.get("callback", None)

        result = self.redis.call_lua(
            method="lua_part_set",
            keys=[group],
            args=[part, next, id_, timestamp])

        if callback == None:
            return "{}({});".format(callback, result)
        else:
            return result

    @http("GET", "/api/part/get/<string:frame>")
    def get_part(self, request, frame):
        """part_current & part_next
        e.g. /api/part/get?IP=<ip>&callback=<callback>
        """
        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)
        frame = frame.lower()
        id_ = request.args.get("id", 1)
        seq = request.args.get("seq", 1)

        callback = request.args.get("callback", None)
        data = []
        error = ""
        try:
            # get part_curr
            rtn = self.redis.call_lua(
                method="lua_part_get",
                keys=[group],
                args=[IP, frame, seq, id_, timestamp],
            )
            x = json.loads(rtn)
            I_PRODUCTNSP = x["part"]
            # get part_next
            if I_PRODUCTNSP == "":
                data = []
            else:
                data = self.db.call_proc(
                    "AP_3DXML.ProcTdXml_GetGenelogy",
                    [
                        I_PRODUCTNSP,
                        "part:<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                        "<STRING>",
                    ],
                    "array",
                )
        except Exception as err:
            log.error(err)
            error = repr(err)
        result = json.dumps({
            "jsonrpc": "2.0",
            "result": data,
            "x": x,
            "id": id_,
            "error": error
        })

        if callback == None:
            return result
        else:
            return "{}({});".format(callback, result)

    #################################################################
    ## 作业指导
    #################################################################
    @http("GET", "/api/wi/get")
    def get_wi(self, request):
        """work Instructions
        e.g. http://localhost:8000/api/wi/get?IP=<IP>
        """
        IP = request.args.get("IP", request.remote_addr)
        seq = request.args.get("seq", 1)
        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        callback = request.args.get("callback", None)

        result = self.redis.call_lua(
            method="lua_wi_get", keys=[group], args=[seq, timestamp])

        if callback == None:
            return result
        else:
            return "{}({});".format(callback, result)

    #################################################################
    ## 工单
    #################################################################
    @http("GET", "/api/order/set")
    def set_order(self, request):
        """
        Apriso -> Redis, 设定工位工单
        """
        ## workstation, WI path, 3D model path, wip_order, operation, step
        params = set(["ws", "path_wi", "path_3d", "wip_order", "op", "step"])

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        ws = request.args.get("ws", "no_ws")
        path_wi = request.args.get("path_wi", "")
        path_3d = request.args.get("path_3d", "no_path")
        wip_order = request.args.get("wip_order", "")
        order_type = request.args.get("order_type", "")

        operation = request.args.get("operation", "")
        step = request.args.get("step", "")

        callback = request.args.get("callback", None)

        now = time.strftime("%Y-%m-%d %H:%M:%S")

        result = self.redis.call_lua(
            method="lua_order_set",
            keys=[group],
            args=[
                ws,
                path_wi,
                path_3d,
                wip_order,
                order_type,
                operation,
                step,
                timestamp,
                IP,
            ],
        )
        if callback == None:
            return result
        else:
            return "{}({});".format(callback, result)

    @http("GET", "/api/order/get")
    def get_order(self, request):
        """
        Apriso -> Redis, 设定工位工单
        """
        ## workstation, WI path, 3D model path, wip_order, operation, step

        result = None

        IP = request.args.get("IP", request.remote_addr)

        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        try:

            id_ = request.args.get("id", 1)

            callback = request.args.get("callback", None)

            now = time.strftime("%Y-%m-%d %H:%M:%S")

            result = self.redis.call_lua(
                method="lua_order_get", keys=[group], args=[id_, timestamp])
            if callback == None:
                return result
            else:
                return "{}({});".format(callback, result)

        except Exception as ex:
            log.error(ex)

    #################################################################
    ## 安灯
    #################################################################
    @http("GET", "/api/andon/set")
    def set_andon(self, request):
        """
        Apriso -> Andon
        """
        ### signals = set(['material', 'quality', 'equipment', 'start', 'beep'])

        IP = request.args.get("IP", request.remote_addr)
        id_ = request.args.get("id", 1)
        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        log.debug("{}:{}".format(addr, ip))

        signal = request.args.get("signal")

        status = request.args.get("status")

        callback = request.args.get("JSONCALLBACK", "ng_jsonp_callback")

        ## 7 for andon
        ip_4 = 10 * (int(addr[3]) // 10) + 7

        addrs = addr[:3]
        addrs.append(str(ip_4))

        IP_Andon = ".".join(addrs)

        # IP_Andon = "172.31.27.57"
        port = 8000

        url = "http://{}:{}/andon/change/status?title={}&status={}&JSONCALLBACK={}&IP={}".format(
            IP_Andon, port, signal, status, callback, IP)

        try:
            r = requests.get(url)
            log.debug(r.text)

            result = self.redis.call_lua(
                method="lua_andon_set",
                keys=[group],
                args=[signal, status, id_, timestamp],
            )
            log.debug(result)
            return r.text

        except Exception as ex:
            log.error(ex)
            return "{}({});".format(callback, json.dumps({"error": repr(ex)}))

    @http("GET", "/api/andon/get")
    def get_andon_status(self, request):
        """
        Redis ->
        """

        IP = request.args.get("IP", request.remote_addr)
        id_ = request.args.get("id", 1)
        callback = request.args.get("JSONCALLBACK", "ng_jsonp_callback")
        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        ip_4 = 10 * (int(addr[3]) // 10) + 7

        addrs = addr[:3]
        addrs.append(str(ip_4))

        IP_Andon = ".".join(addrs)
        port = 8000

        url = "http://{}:{}/andon/status?JSONCALLBACK={}&IP={}".format(
            IP_Andon, port, callback, IP)

        try:
            r = requests.get(url)
            return r.text
        except Exception as ex:
            log.error(ex)
            return "{}({});".format(callback, json.dumps({"error": repr(ex)}))

    @http("GET", "/api/andon/check")
    def check_andon(self, request):
        """
        Redis ->
        """

        IP = request.args.get("IP", request.remote_addr)
        id_ = request.args.get("id", 1)
        # callback = request.args.get("JSONCALLBACK", "ng_jsonp_callback")
        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        result = self.redis.call_lua(
            method="lua_andon_get", keys=[group], args=[id_, timestamp])

        return result

    @http("GET", "/ip")
    def ip_get(self, request):
        """"""
        return request.remote_addr

    #################################################################
    ## 现场数据采集
    #################################################################
    ## 游标卡尺
    @http("GET,POST", "/api/measure/set")
    def set_measure(self, request):
        """"""
        IP = request.args.get("IP", request.remote_addr)
        # val = request.args.get("val", None)
        type, wskey, addr, ip, group, timestamp = parse_ip(IP)

        ### print(json.loads(request.get_data(as_text=True)))
        ### return u"received: {}".format(request.get_data(as_text=True))
        if val != None:

            self.db.call_proc("AP_3DXML.ProcTDXML_SetSerialRuler", ["SN", val],
                              "array")

        return "OK"
