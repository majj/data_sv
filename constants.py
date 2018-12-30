# -*-coding:utf-8 -*
"""
"""

import cx_Oracle

## for timer
INTERVAL_HEARTBEAT = 30

## for oracle SP-OUT
NUMBER = "<NUMBER>"
STRING = "<STRING>"
DATE = "<DATE>"
DATETIME = "<DATETIME>"
TIMESTAMP = "<TIMESTAMP>"
CURSOR = "<CURSOR>"

ORA_TYPE_MAP = {
    "<BINARY>": cx_Oracle.BINARY,
    "<BOOLEAN>": cx_Oracle.BOOLEAN,
    "<CURSOR>": cx_Oracle.CURSOR,
    "<DATETIME>": cx_Oracle.DATETIME,
    "<NUMBER>": cx_Oracle.NUMBER,
    "<STRING>": cx_Oracle.STRING,
    "<TIMESTAMP>": cx_Oracle.TIMESTAMP,
}
