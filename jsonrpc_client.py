# -*-coding:utf-8 -*
"""
test jsonrpc
"""

import json

import requests

### import ujson as json



def main():

    data = {
        "jsonrpc": "2.0",
        "method": "lua_part_get3",
        "params": {
            "values": [1, 2, 3]
        },
        "id": "21",
    }

    print(data)

    url = "http://127.0.0.1:8001/jsonrpc/call"

    r = requests.post(url, json=data)

    print(r.text)


if __name__ == "__main__":
    main()
