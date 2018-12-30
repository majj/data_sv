# -*-coding:utf-8 -*

from nameko.extensions import DependencyProvider

from lib.oracle_lib import OracleDB as _OracleDB

Oracle_KEY = "ORACLE"


class Oracle(DependencyProvider):
    """"""

    def __init__(self, **options):
        # self.key = key
        self.client = None
        self.options = {"decode_responses": True}
        self.options.update(options)

    def setup(self):
        Oracle_conf = self.container.config[Oracle_KEY]
        self.db_info = Oracle_conf
        pass

    def start(self):
        self.client = _OracleDB(self.db_info)

    def stop(self):
        self.client = None

    def kill(self):
        self.client = None

    def get_dependency(self, worker_ctx):
        return self.client
