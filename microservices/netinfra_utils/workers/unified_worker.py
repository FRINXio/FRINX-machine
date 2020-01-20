from __future__ import print_function

import requests
import json
import copy
from string import Template
from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response
import uniconfig_worker

odl_url_unified_oper_shallow = odl_url_base + "/data/network-topology:network-topology/topology=unified?content=nonconfig&depth=3"
odl_url_unified_oper = odl_url_base + "/data/network-topology:network-topology/topology=unified?content=nonconfig"
odl_url_unified_oper_mount = odl_url_base + "/data/network-topology:network-topology/topology=unified/node=$id?content=nonconfig"
odl_url_unified_mount = odl_url_base + "/data/network-topology:network-topology/topology=unified/node=$id"


def execute_read_unified_topology_operational(task):
    response_code, response_json = read_all_devices(odl_url_unified_oper)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': odl_url_unified_oper,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_unified_oper,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def read_all_devices(url):
    r = requests.get(url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    actual_nodes = response_json['topology'][0]['node']
    filtered_nodes = []

    for node in actual_nodes:
        if node['unified-topology:connection-status'] == "connected":
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
    add_params = task['inputData']['task_params']
    optional = task['inputData']['optional'] if 'optional' in task['inputData'] else "false"
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


def read_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = uniconfig_worker.apply_functions(uri)

    id_url = Template(odl_url_unified_mount).substitute({"id": device_id}) + "/yang-ext:mount" + (uri if uri else "") + "?content=config"

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s read successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to read device with ID %s" % device_id]}


def write_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = uniconfig_worker.apply_functions(uri)

    template = task['inputData']['template']
    params = task['inputData']['params'] if task['inputData']['params'] else {}

    data_json = template if isinstance(template, str) else json.dumps(template if template else {})
    data_json = Template(data_json).substitute(params)

    id_url = Template(odl_url_unified_mount).substitute({"id": device_id}) + "/yang-ext:mount" + (uri if uri else "")
    id_url = Template(id_url).substitute(params)

    r = requests.put(id_url, data=data_json, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.no_content or response_code == requests.codes.created:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'request_url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'request_url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


def delete_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = uniconfig_worker.apply_functions(uri)

    id_url = Template(odl_url_unified_mount).substitute({"id": device_id}) + "/yang-ext:mount" + (uri if uri else "")

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.no_content:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'request_url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'request_url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


def execute_check_unified_node_exists(task):
    device_id = task['inputData']['device_id']

    id_url = Template(odl_url_unified_oper_mount).substitute({"id": device_id})

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code != requests.codes.not_found:
        # Mountpoint with such ID already exists
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Unified mountpoint with ID %s exists" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unified mountpoint with ID %s doesn't exist" % device_id]}


def start(cc):
    print('Starting Unified workers')

    cc.register('UNIFIED_read_unified_topology_operational', {
        "name": "UNIFIED_read_unified_topology_operational",
        "description": "Read operational state of Unified - BASICS,UNIFIED",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNIFIED_read_unified_topology_operational', execute_read_unified_topology_operational, False)

    cc.register('UNIFIED_get_all_devices_as_dynamic_fork_tasks', {
        "name": "UNIFIED_get_all_devices_as_dynamic_fork_tasks",
        "description": "get all devices in unified topology as workflow tasks - BASICS,UNIFIED",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "task",
            "task_params",
            "optional"
        ],
        "outputKeys": [
            "url",
            "dynamic_tasks_i",
            "dynamic_tasks"
        ]
    })
    cc.start('UNIFIED_get_all_devices_as_dynamic_fork_tasks', get_all_devices_as_dynamic_fork_tasks, False)

    cc.register('UNIFIED_read_structured_device_data', {
        "name": "UNIFIED_read_structured_device_data",
        "description": "Read device configuration or operational data in structured format e.g. openconfig - BASICS,UNIFIED,OPENCONFIG",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uri"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNIFIED_read_structured_device_data', read_structured_data, False)

    cc.register('UNIFIED_write_structured_device_data', {
        "name": "UNIFIED_write_structured_device_data",
        "description": "Write device configuration data in structured format e.g. openconfig - BASICS,UNIFIED",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uri",
            "template",
            "params"
        ],
        "outputKeys": [
            "url",
            "request_url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNIFIED_write_structured_device_data', write_structured_data, False)

    cc.register('UNIFIED_delete_structured_device_data', {
        "name": "UNIFIED_delete_structured_device_data",
        "description": "Delete device configuration data in structured format e.g. openconfig - BASICS,UNIFIED,OPENCONFIG",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uri"
        ],
        "outputKeys": [
            "url",
            "request_url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNIFIED_delete_structured_device_data', delete_structured_data, False)

    cc.register('UNIFIED_check_unified_node_exists', {
        "name": "UNIFIED_check_unified_node_exists",
        "description": "check unified node exists - BASICS,UNIFIED",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNIFIED_check_unified_node_exists', execute_check_unified_node_exists, False)
