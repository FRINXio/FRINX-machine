import copy
import json
import time
import traceback
from random import randint
from datetime import datetime

import requests
from conductor.ConductorWorker import ConductorWorker

from frinx_rest import conductor_url_base, odl_headers

DEFAULT_TASK_DEFINITION = {
    "name": "",
    "retryCount": 0,
    "ownerEmail":"example@example.com",
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

        print('Registering task ' + task_type + ' : ' + str(task_definition))
        task_meta = copy.deepcopy(task_definition)
        task_meta["name"] = task_type
        try:
            r = requests.post(conductor_task_url,
                              data=json.dumps([task_meta]),
                              headers=odl_headers)
            # response_code = r.status_code
        except Exception as err:
            print('Error while registering task ' + traceback.format_exc())

    def poll_and_execute(self, taskType, exec_function, domain=None):
        poll_wait = 5000
        while True:
            time.sleep(float(self.polling_interval))
            print(self.timestamp() + ' Polling for task: ' + taskType + ' with wait ' + str(poll_wait))
            polled = self.taskClient.pollForBatch(taskType, 1, poll_wait, self.worker_id, domain)
            if polled is not None:
                print(self.timestamp() + ' Polled batch for ' + taskType + ':' + str(len(polled)))
                for task in polled:
                    print(self.timestamp() + ' Polled ' + taskType + ': ' + task['taskId'])
                    if self.taskClient.ackTask(task['taskId'], self.worker_id):
                        self.execute(task, exec_function)

    def timestamp(self):
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S:%f")

    def execute(self, task, exec_function):
        try:
            print(self.timestamp() + ' Executing task: ' + task['taskId'])
            resp = exec_function(task)
            if resp is None:
                raise Exception(
                    'Task execution function MUST return a response as a dict with status and output fields')
            task['status'] = resp['status']
            task['outputData'] = resp.get('output', {})
            task['logs'] = resp.get('logs', "")
            self.taskClient.updateTask(task)
        except Exception as err:
            print('Error executing task: ' + traceback.format_exc())
            task['status'] = 'FAILED'
            task['outputData'] = {'Error executing task:': str(task),
                                  'exec_function': str(exec_function), }
            task['logs'] = ["Logs: %s" % traceback.format_exc()]

            try:
                self.taskClient.updateTask(task)
            except Exception as err2:
                # Can happen when task timed out
                print('Unable to update task: ' + task['taskId'] + ': ' + traceback.format_exc())

if __name__ == '__main__':
    main()
