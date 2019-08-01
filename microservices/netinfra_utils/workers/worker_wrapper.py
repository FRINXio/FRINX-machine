import copy
import json
import time

import requests
from conductor.ConductorWorker import ConductorWorker

from workers import standalone_main
from workers.frinx_rest import conductor_url_base, odl_headers

DEFAULT_TASK_DEFINITION = {
    "name": "",
    "retryCount": 0,
    "timeoutSeconds": 60,
    "timeoutPolicy": "TIME_OUT_WF",
    "retryLogic": "FIXED",
    "retryDelaySeconds": 0,
    "responseTimeoutSeconds": 10
}

conductor_task_url = conductor_url_base + "/metadata/taskdefs"


class ExceptionHandlingConductorWrapper(ConductorWorker):

    # submit
    def register(self, task_type, task_definition):
        if task_definition is None:
            task_definition = DEFAULT_TASK_DEFINITION
        task_meta = copy.deepcopy(task_definition)
        task_meta["name"] = task_type
        r = requests.post(conductor_task_url,
                          data=json.dumps([task_meta]),
                          headers=odl_headers)

        response_code = r.status_code

    def execute(self, task, exec_function):
        try:
            resp = exec_function(task)
            if resp is None:
                raise Exception(
                    'Task execution function MUST return a response as a dict with status and output fields')
            task['status'] = resp['status']
            task['outputData'] = resp['output']
            task['logs'] = resp['logs']
            self.taskClient.updateTask(task)
        except Exception as err:
            print('Error executing task: ' + str(err))
            task['status'] = 'FAILED'
            task['outputData'] = {'Error executing task:': str(task),
                                  'exec_function': str(exec_function), }
            task['logs'] = ["Logs: %s" % str(err)]
            self.taskClient.updateTask(task)


def main():
    print('Starting FRINX workers with wrapper')
    cc = ExceptionHandlingConductorWrapper()
    standalone_main.register_workers(cc)

    # block
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
