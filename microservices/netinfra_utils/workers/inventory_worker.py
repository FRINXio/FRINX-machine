from __future__ import print_function

import json
import copy
from string import Template

import requests

from frinx_rest import elastic_url_base, parse_response, elastic_headers

inventory_device_url = elastic_url_base + "/inventory-device/device/$id"
inventory_device_get_url = elastic_url_base + "/inventory-device/device/$id/_source"
inventory_device_update_url = elastic_url_base + "/inventory-device/device/$id/_update"
inventory_all_devices_url = elastic_url_base + "/inventory-device/device/_search?size=10000"

add_template = {
    "id": "",
    "host": "",
    "port": "",
    "transport_type": "",
    "device_type": "",
    "device_version": "",
    "username": "",
    "password": ""
}


def add_device(task):
    device_id = task['inputData']['id']

    id_url = Template(inventory_device_url).substitute({"id": device_id})

    add_body = copy.deepcopy(add_template)

    add_body["id"] = task['inputData']['id']
    add_body["host"] = task['inputData']['host']
    add_body["port"] = task['inputData']['port']
    add_body["transport_type"] = task['inputData']['protocol']
    add_body["device_type"] = task['inputData']['type']
    add_body["device_version"] = task['inputData']['version']
    add_body["username"] = task['inputData']['username']
    add_body["password"] = task['inputData']['password']

    r = requests.post(id_url, data=json.dumps(add_body), headers=elastic_headers)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok or response_code == requests.codes.created:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


add_field_command = "ctx._source.$field = '$value'"

add_field_template = {
    "script": ""
}


def add_field_to_device(task):
    device_id = task['inputData']['id']
    field = task['inputData']['field']
    value = task['inputData']['value']

    id_url = Template(inventory_device_update_url).substitute({"id": device_id})
    data = Template(add_field_command).substitute({"field": field, "value": value})

    update_body = copy.deepcopy(add_field_template)

    update_body["script"] = data

    r = requests.post(id_url, data=json.dumps(update_body), headers=elastic_headers)
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
                'logs': []}


add_nested_field_template = {
    "doc": {
    }
}


def add_nested_field_to_device(task):
    device_id = task['inputData']['id']
    field = task['inputData']['field']
    value = task['inputData']['value']

    id_url = Template(inventory_device_update_url).substitute({"id": device_id})
    update_body = copy.deepcopy(add_nested_field_template)

    update_body["doc"][field] = value

    r = requests.post(id_url, data=json.dumps(update_body), headers=elastic_headers)
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
                'logs': []}


def remove_device(task):
    device_id = task['inputData']['id']

    id_url = Template(inventory_device_url).substitute({"id": device_id})

    r = requests.delete(id_url, headers=elastic_headers)
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
                'logs': []}


def get_device(task):
    device_id = task['inputData']['id']

    id_url = Template(inventory_device_get_url).substitute({"id": device_id})

    r = requests.get(id_url, headers=elastic_headers)
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
                'logs': []}


device_query_template = {
    "query": {
        "term": {"device_type": ""}
    }
}


def get_all_devices(task):
    device_type = task['inputData']['type']

    response_code, response_json = read_all_devices(device_type)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': inventory_all_devices_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': inventory_all_devices_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def read_all_devices(device_type):
    if device_type is not None and device_type is not "":
        device_query_body = copy.deepcopy(device_query_template)
        device_query_body["query"]["term"]["device_type"] = device_type
        r = requests.get(inventory_all_devices_url, data=json.dumps(device_query_body), headers=elastic_headers)
    else:
        r = requests.get(inventory_all_devices_url, headers=elastic_headers)

    return parse_response(r)


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
    device_type = task['inputData']['type']
    task = task['inputData']['task']

    response_code, response_json = read_all_devices(device_type)

    if response_code == requests.codes.ok:
        ids = map(lambda x: x["_id"], response_json["hits"]["hits"])

        dynamic_tasks_i = {}
        for device_id in ids:
            dynamic_tasks_i.update({device_id: {"id": device_id}})

        dynamic_tasks = []
        for device_id in ids:
            task_body = copy.deepcopy(task_body_template)
            task_body["taskReferenceName"] = device_id
            task_body["subWorkflowParam"]["name"] = task
            dynamic_tasks.append(task_body)

        return {'status': 'COMPLETED', 'output': {'url': inventory_all_devices_url,
                                                  'dynamic_tasks_i': dynamic_tasks_i,
                                                  'dynamic_tasks': dynamic_tasks},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': inventory_all_devices_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


inventory_show_command_url = elastic_url_base + "/inventory-show_cmd/show_command/$id"
inventory_show_command_get_url = elastic_url_base + "/inventory-show_cmd/show_command/$id/_source"

add_show_command_template = {
    "command": "",
}


def add_show_command(task):
    command_id = task['inputData']['id']

    id_url = Template(inventory_show_command_url).substitute({"id": command_id})

    add_body = copy.deepcopy(add_show_command_template)

    add_body["command"] = task['inputData']['command']
    add_body["id"] = command_id

    r = requests.post(id_url, data=json.dumps(add_body), headers=elastic_headers)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok or response_code == requests.codes.created:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def get_show_command(task):
    command_id = task['inputData']['id']

    id_url = Template(inventory_show_command_get_url).substitute({"id": command_id})

    r = requests.get(id_url, headers=elastic_headers)
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
                'logs': []}


def start(cc):
    print('Starting Inventory workers')

    cc.start('INVENTORY_add_device', add_device, False)
    cc.start('INVENTORY_add_field_to_device', add_field_to_device, False)
    cc.start('INVENTORY_add_nested_field_to_device', add_nested_field_to_device, False)
    cc.start('INVENTORY_remove_device', remove_device, False)
    cc.start('INVENTORY_get_device', get_device, False)
    cc.start('INVENTORY_get_all_devices', get_all_devices, False)
    cc.start('INVENTORY_get_all_devices_as_tasks', get_all_devices_as_tasks, False)

    cc.start('INVENTORY_add_show_command', add_show_command, False)
    cc.start('INVENTORY_get_show_command', get_show_command, False)
