import frinx_rest
frinx_rest.odl_url_base = "http://localhost:8181/restconf"

import json
import time

from flask import Flask, request
from flask_restful import Resource, Api

import cli_worker
import inventory_worker
import l3vpn_worker
import lldp_worker
import netconf_worker
import platform_worker
import terraform_worker
import uniconfig_worker
import unified_worker
import vll_worker
import vll_service_worker


class StandaloneWorker:

    def __init__(self, api):
        pass
        self.api = api

    def register(self, task_type, task_definition=None):
        pass

    def start(self, task_type, exec_function, wait, domain=None, task_definition=None):
        print('Starting task %s' % task_type)
        self.api.add_resource(TaskInvocation, "/" + task_type, endpoint=task_type, resource_class_args=[exec_function])


class TaskInvocation(Resource):

    def __init__(self, func):
        pass
        self.func = func

    def get(self):
        # TODO reject
        pass

    def put(self):
        # TODO log
        # TODO check content type
        # TODO reject

        try:
            input_dict = self.parse_input_json()
            # TODO print logs from function invocation
            return self.func({"inputData": input_dict})
        except Exception as e:
            print e
            return {"error": "Invocation failed due to: %s" % str(e.message)}

    @staticmethod
    def parse_input_json():
        if request.data is None or not request.data.strip():
            input_string = "{}"
        else:
            input_string = request.data

        input_dict = json.loads(input_string)

        if input_dict is None:
            input_dict = {}

        return input_dict


def main():
    print('Starting FRINX STANDALONE workers')
    app = Flask(__name__)
    api = Api(app)
    cc = StandaloneWorker(api)
    register_workers(cc)
    print app.url_map
    app.run("0.0.0.0", 6454, True)

    # block
    while 1:
        time.sleep(1)


def register_workers(cc):
    cli_worker.start(cc)
    netconf_worker.start(cc)
    platform_worker.start(cc)
    l3vpn_worker.start(cc)
    lldp_worker.start(cc)
    inventory_worker.start(cc)
    unified_worker.start(cc)
    uniconfig_worker.start(cc)
    terraform_worker.start(cc)
    vll_worker.start(cc)
    vll_service_worker.start(cc)


if __name__ == '__main__':
    main()
