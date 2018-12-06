from __future__ import print_function

import json
from string import Template

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response

odl_url_cli_mount = odl_url_base + "/config/network-topology:network-topology/topology/cli/node/"
odl_url_cli_oper = odl_url_base + "/operational/network-topology:network-topology/topology/cli/"
odl_url_unified_oper_shallow = odl_url_base + "/operational/network-topology:network-topology/topology/cli?depth=3"
odl_url_cli_mount_oper = odl_url_base + "/operational/network-topology:network-topology/topology/cli/node/"
odl_url_cli_mount_rpc = odl_url_base + "/operations/network-topology:network-topology/topology/cli/node/"
odl_url_cli_read_journal = odl_url_base + "/operations/network-topology:network-topology/topology/cli/node/$id/yang-ext:mount/journal:read-journal"

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
    device_id = task['inputData']['id']

    mount_body = mount_template.copy()

    mount_body["network-topology:node"]["network-topology:node-id"] = task['inputData']['id']
    mount_body["network-topology:node"]["cli-topology:host"] = task['inputData']['host']
    mount_body["network-topology:node"]["cli-topology:port"] = task['inputData']['port']
    mount_body["network-topology:node"]["cli-topology:transport-type"] = task['inputData']['protocol']
    mount_body["network-topology:node"]["cli-topology:device-type"] = task['inputData']['type']
    mount_body["network-topology:node"]["cli-topology:device-version"] = task['inputData']['version']
    mount_body["network-topology:node"]["cli-topology:username"] = task['inputData']['username']
    mount_body["network-topology:node"]["cli-topology:password"] = task['inputData']['password']

    id_url = odl_url_cli_mount + device_id

    r = requests.put(id_url, data=json.dumps(mount_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created:
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


def execute_execute_and_read_rpc_cli(task):
    device_id = task['inputData']['id']
    template = task['inputData']['template']
    params = task['inputData']['params'] if task['inputData']['params'] else {}
    params = params if isinstance(params, dict) else eval(params)

    commands = Template(template).substitute(params)
    exec_body = execute_and_read_template.copy()

    exec_body["input"]["ios-cli:command"] = commands

    id_url = odl_url_cli_mount_rpc + device_id + "/yang-ext:mount/cli-unit-generic:execute-and-read"

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
    device_id = task['inputData']['id']

    id_url = odl_url_cli_mount + device_id

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    return {'status': 'COMPLETED', 'output': {'url': id_url,
                                              'response_code': response_code,
                                              'response_body': response_json},
            'logs': ["Mountpoint with ID %s removed" % device_id]}


def execute_check_cli_id_available(task):
    device_id = task['inputData']['id']

    id_url = odl_url_cli_mount + device_id

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
    device_id = task['inputData']['id']

    id_url = odl_url_cli_mount_oper + device_id

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


def get_all_devices_as_tasks(task):
    task_name = task['inputData']['task']
    task_input = task['inputData']['task_input']

    response_code, response_json = read_all_devices(odl_url_unified_oper_shallow)

    if response_code == requests.codes.ok:
        ids = map(lambda x: x["node-id"], response_json["topology"][0]["node"])

        dynamic_tasks_i = {}
        for device_id in ids:
            dynamic_tasks_i.update({device_id: {"id": device_id}})
            print(task_input)
            print(dynamic_tasks_i)
            dynamic_tasks_i[device_id].update(task_input)
            print(dynamic_tasks_i)

        dynamic_tasks = []
        for device_id in ids:
            task_body = task_body_template.copy()
            task_body["taskReferenceName"] = device_id
            task_body["subWorkflowParam"]["name"] = task_name
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
    device_id = task['inputData']['id']

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

    cc.start('CLI_mount_cli', execute_mount_cli, False)
    cc.start('CLI_unmount_cli', execute_unmount_cli, False)
    cc.start('CLI_check_cli_connected', execute_check_connected_cli, False)
    cc.start('CLI_execute_and_read_rpc_cli', execute_execute_and_read_rpc_cli, False)
    cc.start('CLI_check_cli_id_available', execute_check_cli_id_available, False)
    cc.start('CLI_read_cli_topology_operational', execute_read_cli_topology_operational, False)
    cc.start('CLI_get_all_devices_as_tasks', get_all_devices_as_tasks, False)
    cc.start('CLI_get_cli_journal', execute_get_cli_journal, False)


