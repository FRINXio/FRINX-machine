import copy
import json
import time
from random import randint

import requests
from conductor.ConductorWorker import ConductorWorker

from frinx_rest import conductor_url_base, odl_headers

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

    def start(self, taskType, exec_function, wait, domain=None):
        # Random small sleep in order to NOT start all the workers at the same time
        time.sleep(randint(25, 100) * 0.001)
        ConductorWorker.start(self, taskType, exec_function, wait, domain)

    # register task metadata into conductor
    def register(self, task_type, task_definition=None):
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
            task['outputData'] = resp.get('output', {})
            task['logs'] = resp.get('logs', "")
            self.taskClient.updateTask(task)
        except Exception as err:
            print('Error executing task: ' + str(err))
            task['status'] = 'FAILED'
            task['outputData'] = {'Error executing task:': str(task),
                                  'exec_function': str(exec_function), }
            task['logs'] = ["Logs: %s" % str(err)]
            self.taskClient.updateTask(task)


if __name__ == '__main__':
    main()
