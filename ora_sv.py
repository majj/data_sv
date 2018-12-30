# -*-coding:utf-8 -*
"""
Oracle DB services

"""
from __future__ import absolute_import
### import io
### import sys
### sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
### from __future__ import unicode_literals

_version = "1.7.1"
_author = "mabotech"

import time
import traceback
from logging import getLogger

from nameko.timer import timer
from nameko.dependency_providers import Config
from nameko.rpc import rpc, RpcProxy
from nameko.constants import DEFAULT_HEARTBEAT
from nameko_oracle import Oracle

from constants import ORA_TYPE_MAP

log = getLogger("ora_sv")


class OracleService:
    """ oracle service    
    """

    name = "oracle_service"

    config = Config()
    ora = Oracle()

    @timer(interval=DEFAULT_HEARTBEAT)
    def heartbeat(self):
        """
        """
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = 1000 * time.time()
        log.debug("heartbeat: {}".format(now))

    def _prep_params(self, sp_name, params):
        """
        """
        sp_params = []
        sp_params_names = []

        i = 0  ## index of input parameter
        oi = 0  ## index of output parameter

        for item in params:
            # item = param.split(":")[-1]
            i = i + 1

            if isinstance(item, str):
                xparam = item.split(":")  ##  pname:<STRING>
                if xparam[-1] in ORA_TYPE_MAP:
                    oi = oi + 1
                    sp_params.append(
                        self.ora.cursor.var(ORA_TYPE_MAP[xparam[-1]]))
                    if len(xparam) > 1:
                        sp_params_names.append(xparam[0])
                    else:
                        sp_params_names.append("X{}".format(oi))
                else:
                    sp_params.append(item)
                    sp_params_names.append("P{}".format(i))
            else:
                sp_params.append(item)
                sp_params_names.append("P{}".format(i))

        return sp_params, sp_params_names

    def _prep_result(self, result, params: list, sp_params_names: list,
                     rtype: str):
        """
        """
        i = 0
        data = []
        data_d = {}

        for item in params:
            if rtype == "dict":  ## return dict
                name = sp_params_names[i]
                if item == "<CURSOR>":
                    v = self.ora.get_ref_rows(result[i])
                    data_d[name] = v
                else:
                    # v = self.ora.get_rows(result[i])
                    ### data.append(result[i])
                    data_d[name] = result[i]
            else:  ## return list
                if item == "<CURSOR>":
                    v = self.ora.get_ref_rows(result[i])
                    data.append(v)
                else:
                    # v = self.ora.get_rows(result[i])
                    data.append(result[i])
            i = i + 1

        return data, data_d

    @rpc
    def query(self, sql: str, args={}):
        """
        TODO:add schema to sql?
        """
        try:
            self.ora.execute(sql, args)
            return self.ora.get_rows()
        except Exception as ex:
            log.error(sql)
            log.error(traceback.format_exc())
            raise Exception(repr(ex))

    @rpc
    def call_proc(self, sp_name: str, params: list, rtype="dict"):
        """
        sp_name: stored procudure
        params: in, out(number, string, datetime, timestamp, cursor...)
        """
        schema = self.config.get("ORACLE")["username"]

        sp_name_a = sp_name.split(".")

        if sp_name_a[0].lower() == schema.lower():
            pass
        else:
            ## -> schema.sp_name
            sp_name = ".".join([schema, sp_name])

        log.debug(sp_name)
        log.debug(params)

        sp_params, sp_params_names = self._prep_params(sp_name, params)

        ### log.debug(sp_params)

        try:
            result = self.ora.callproc(sp_name, sp_params)

            data, data_d = self._prep_result(result, params, sp_params_names,
                                             rtype)

            if rtype == "dict":
                return data_d
            else:
                return data

        except Exception as ex:
            log.debug(traceback.format_exc())
            raise Exception(repr(ex))
            return {"error": repr(ex)}
