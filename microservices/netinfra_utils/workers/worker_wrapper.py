import cli_worker
import inventory_worker
import l3vpn_worker
import lldp_worker
import netconf_worker
import platform_worker
import terraform_worker
import uniconfig_worker
import unified_worker
import time
from conductor.ConductorWorker import ConductorWorker


class WorkerWrapper(ConductorWorker):

    def execute(self, task, exec_function):
        try:
            resp = exec_function(task)
            if resp is None:
                raise Exception('Task execution function MUST return a response as a dict with status and output fields')
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
    cc = WorkerWrapper()
    register_workers(cc)

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


if __name__ == '__main__':
    main()