import frinx_rest
frinx_rest.odl_url_base = "http://localhost:8181/rests"
import json
import time

from flask import Flask, request
from flask_restful import Resource, Api
from flask_basicauth import BasicAuth

from main import register_workers

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


DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWD = 'admin'


def main():
    print('Starting FRINX STANDALONE workers')
    app = Flask(__name__)

    app.config['BASIC_AUTH_USERNAME'] = DEFAULT_USERNAME
    app.config['BASIC_AUTH_PASSWORD'] = DEFAULT_PASSWD
    app.config['BASIC_AUTH_FORCE'] = True

    basic_auth = BasicAuth(app)

    api = Api(app)
    cc = StandaloneWorker(api)
    register_workers(cc)
    print app.url_map
    app.run("0.0.0.0", 6454, True)

    # block
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
