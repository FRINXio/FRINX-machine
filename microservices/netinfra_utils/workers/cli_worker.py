from __future__ import print_function

import json
import copy
from string import Template

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response

odl_url_cli_mount = odl_url_base + "/data/network-topology:network-topology/topology=cli/node=$id"
odl_url_cli_oper = odl_url_base + "/data/network-topology:network-topology/topology=cli?content=nonconfig"
odl_url_unified_oper_shallow = odl_url_base + "/data/network-topology:network-topology/topology=cli?content=nonconfig&depth=3"
odl_url_cli_mount_oper = odl_url_base + "/data/network-topology:network-topology/topology=cli/node=$id?content=nonconfig"
odl_url_cli_mount_rpc = odl_url_base + "/operations/network-topology:network-topology/topology=cli/node=$id"
odl_url_cli_read_journal = odl_url_base + "/operations/network-topology:network-topology/topology=cli/node=$id/yang-ext:mount/journal:read-journal?content=nonconfig"

mount_template = {
    "network-topology:node":
        {
            "network-topology:node-id": "",

            "cli-topology:host": "",
            "cli-topology:port": "",
            "cli-topology:transport-type": "",

            "cli-topology:device-type": "",
            "cli-topology:device-version": "",

            "cli-topology:username": "",
            "cli-topology:password": "",

            "cli-topology:journal-size": 500,
            "cli-topology:dry-run-journal-size": 180
        }
}


def execute_mount_cli(task):
    device_id = task['inputData']['device_id']

    mount_body = copy.deepcopy(mount_template)

    mount_body["network-topology:node"]["network-topology:node-id"] = task['inputData']['device_id']
    mount_body["network-topology:node"]["cli-topology:host"] = task['inputData']['host']
    mount_body["network-topology:node"]["cli-topology:port"] = task['inputData']['port']
    mount_body["network-topology:node"]["cli-topology:transport-type"] = task['inputData']['protocol']
    mount_body["network-topology:node"]["cli-topology:device-type"] = task['inputData']['type']
    mount_body["network-topology:node"]["cli-topology:device-version"] = task['inputData']['version']
    mount_body["network-topology:node"]["cli-topology:username"] = task['inputData']['username']
    mount_body["network-topology:node"]["cli-topology:password"] = task['inputData']['password']

    id_url = Template(odl_url_cli_mount).substitute({"id": device_id})

    r = requests.put(id_url, data=json.dumps(mount_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.no_content:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'request_body': mount_body,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s registered" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'request_body': mount_body,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to register device with ID %s" % device_id]}


execute_and_read_template = {
    "input":
        {
            "ios-cli:command": ""
        }
}


def execute_and_read_rpc_cli(task):
    device_id = task['inputData']['device_id']
    template = task['inputData']['template']
    params = task['inputData']['params'] if task['inputData']['params'] else {}
    params = params if isinstance(params, dict) else eval(params)

    commands = Template(template).substitute(params)
    exec_body = copy.deepcopy(execute_and_read_template)

    exec_body["input"]["ios-cli:command"] = commands

    id_url = Template(odl_url_cli_mount_rpc).substitute({"id": device_id}) + "/yang-ext:mount/cli-unit-generic:execute-and-read"

    r = requests.post(id_url, data=json.dumps(exec_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'request_body': exec_body,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s configured" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'request_body': exec_body,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to configure device with ID %s" % device_id]}


def execute_unmount_cli(task):
    device_id = task['inputData']['device_id']

    id_url = Template(odl_url_cli_mount).substitute({"id": device_id})

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    return {'status': 'COMPLETED', 'output': {'url': id_url,
                                              'response_code': response_code,
                                              'response_body': response_json},
            'logs': ["Mountpoint with ID %s removed" % device_id]}


def execute_check_cli_id_available(task):
    device_id = task['inputData']['device_id']

    id_url = Template(odl_url_cli_mount).substitute({"id": device_id})

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code != requests.codes.not_found:
        # Mountpoint with such ID already exists
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to mount device with ID %s" % device_id]}
    else:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s is available" % device_id]}


def execute_check_connected_cli(task):
    device_id = task['inputData']['device_id']

    id_url = Template(odl_url_cli_mount_oper).substitute({"id": device_id})

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["node"][0]["cli-topology:connection-status"] == "connected":
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s is connected" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Mountpoint with ID %s not yet connected" % device_id]}


def execute_read_cli_topology_operational(task):
    r = requests.get(odl_url_cli_oper, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': odl_url_cli_oper,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_cli_oper,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def read_all_devices(url):
    r = requests.get(url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    actual_nodes = response_json['topology'][0]['node']
    filtered_nodes = []

    for node in actual_nodes:
        if node['cli-topology:connection-status'] == "connected":
            filtered_nodes.append(node)

    response_json['topology'][0].pop('node')
    response_json['topology'][0].update({'node': filtered_nodes})

    return response_code, response_json


task_body_template = {
    "name": "sub_task",
    "taskReferenceName": "",
    "type": "SUB_WORKFLOW",
    "subWorkflowParam": {
        "name": "",
        "version": 1
    }
}


def get_all_devices_as_dynamic_fork_tasks(task):
    subworkflow = task['inputData']['task']
    optional = task['inputData']['optional'] if 'optional' in task['inputData'] else "false"
    add_params = task['inputData']['task_params']
    add_params = json.loads(add_params) if isinstance(add_params, str) else (add_params if add_params else {})

    response_code, response_json = read_all_devices(odl_url_unified_oper_shallow)

    if response_code == requests.codes.ok:
        ids = [nodes["node-id"] for nodes in response_json["topology"][0]["node"]]

        dynamic_tasks_i = {}
        for device_id in ids:
            per_device_params = dict(add_params)
            per_device_params.update({"device_id": device_id})
            dynamic_tasks_i.update({device_id: per_device_params})

        dynamic_tasks = []
        for device_id in ids:
            task_body = copy.deepcopy(task_body_template)
            if optional == "true":
                task_body['optional'] = True
            task_body["taskReferenceName"] = device_id
            task_body["subWorkflowParam"]["name"] = subworkflow
            dynamic_tasks.append(task_body)

        return {'status': 'COMPLETED', 'output': {'url': odl_url_unified_oper_shallow,
                                                  'dynamic_tasks_i': dynamic_tasks_i,
                                                  'dynamic_tasks': dynamic_tasks},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_unified_oper_shallow,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def execute_get_cli_journal(task):
    device_id = task['inputData']['device_id']

    id_url = Template(odl_url_cli_read_journal).substitute({"id": device_id})

    r = requests.post(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Mountpoint with ID %s, cannot read journal" % device_id]}


def start(cc):
    print('Starting CLI workers')

    cc.register('CLI_mount_cli')
    cc.start('CLI_mount_cli', execute_mount_cli, False)

    cc.register('CLI_unmount_cli')
    cc.start('CLI_unmount_cli', execute_unmount_cli, False)

    cc.register('CLI_check_cli_connected', {
        "name": "CLI_check_cli_connected",
        "retryCount": 20,
        "timeoutSeconds": 10,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 5,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "id"
        ]
    })
    cc.start('CLI_check_cli_connected', execute_check_connected_cli, False)

    cc.register('CLI_execute_and_read_rpc_cli', {
        "name": "CLI_execute_and_read_rpc_cli",
        "retryCount": 0,
        "timeoutSeconds": 30,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 30,
        "inputKeys": [
            "template",
            "params"
        ]
    })
    cc.start('CLI_execute_and_read_rpc_cli', execute_and_read_rpc_cli, False)

    cc.register('CLI_check_cli_id_available')
    cc.start('CLI_check_cli_id_available', execute_check_cli_id_available, False)

    cc.register('CLI_read_cli_topology_operational')
    cc.start('CLI_read_cli_topology_operational', execute_read_cli_topology_operational, False)

    cc.register('CLI_get_all_devices_as_dynamic_fork_tasks')
    cc.start('CLI_get_all_devices_as_dynamic_fork_tasks', get_all_devices_as_dynamic_fork_tasks, False)

    cc.register('CLI_get_cli_journal')
    cc.start('CLI_get_cli_journal', execute_get_cli_journal, False)


