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
    "password": "",
    "topology": "cli",
    "labels": []
}


def add_device(task):
    device_id = task['inputData']['device_id']

    id_url = Template(inventory_device_url).substitute({"id": device_id})

    add_body = copy.deepcopy(add_template)

    add_body["id"] = task['inputData']['device_id']
    add_body["host"] = task['inputData']['host']
    add_body["port"] = task['inputData']['port']
    add_body["transport_type"] = task['inputData']['protocol']
    add_body["device_type"] = task['inputData']['type']
    add_body["device_version"] = task['inputData']['version']
    add_body["username"] = task['inputData']['username']
    add_body["password"] = task['inputData']['password']

    if task['inputData']['labels'] is not None:
        device_labels = [label.strip() for label in task['inputData']['labels'].split(',')]
        for label in device_labels:
            add_body["labels"].append(label)

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


add_field_command = "ctx._source['$field'] = '$value'"

add_field_template = {
    "script": ""
}


def add_field_to_device(task):
    device_id = task['inputData']['device_id']
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
    device_id = task['inputData']['device_id']
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


add_array_field_command = "ctx._source.$field = [$value]"


def add_array_to_field(task):
    device_id = task['inputData']['device_id']
    field = task['inputData']['field']
    values = task['inputData']['values']

    id_url = Template(inventory_device_update_url).substitute({"id": device_id})
    array_values = []
    device_labels = [value.strip() for value in values.split(',')]
    for label in device_labels:
        array_values.append(label)

    data = Template(add_array_field_command).substitute({"field": field, "value": array_values})

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


def remove_device(task):
    device_id = task['inputData']['device_id']

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
    device_id = task['inputData']['device_id']

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
    "bool": {
      "must": []
    }
  }
}

device_query_labels_template = {"term": {"labels.keyword": ""}}

device_query_type_template = {"term": {"device_type.keyword": ""}}


def get_all_devices(task):
    device_labels = task['inputData']['labels']

    response_code, response_json = read_all_devices(device_labels)

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


def read_all_devices(device_labels):
    device_query_body = ""
    if device_labels is not None and device_labels is not "":
        if device_query_body is "":
            device_query_body = copy.deepcopy(device_query_template)
        device_labels = [label.strip() for label in device_labels.split(',')]
        for label in device_labels:
            labels_template = copy.deepcopy(device_query_labels_template)
            labels_template["term"]["labels.keyword"] = label
            device_query_body["query"]["bool"]["must"].append(labels_template)

    if device_query_body is not "":
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


def get_all_devices_as_dynamic_fork_tasks(task):
    add_params = task['inputData']['task_params'] if 'task_params' in task['inputData'] else {}
    add_params = json.loads(add_params) if isinstance(add_params, basestring) else (add_params if add_params else {})
    optional = task['inputData']['optional'] if 'optional' in task['inputData'] else "false"
    device_labels = task['inputData']['labels']
    task = task['inputData']['task']

    response_code, response_json = read_all_devices(device_labels)

    if response_code == requests.codes.ok:
        ids = [hits["_id"] for hits in response_json["hits"]["hits"]]

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
    command_id = task['inputData']['template_id']

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
    command_id = task['inputData']['template_id']

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

    cc.register('INVENTORY_add_device')
    cc.start('INVENTORY_add_device', add_device, False)

    cc.register('INVENTORY_add_field_to_device')
    cc.start('INVENTORY_add_field_to_device', add_field_to_device, False)

    cc.register('INVENTORY_add_nested_field_to_device')
    cc.start('INVENTORY_add_nested_field_to_device', add_nested_field_to_device, False)

    cc.register('INVENTORY_add_array_to_field')
    cc.start('INVENTORY_add_array_to_field', add_array_to_field, False)

    cc.register('INVENTORY_remove_device')
    cc.start('INVENTORY_remove_device', remove_device, False)

    cc.register('INVENTORY_get_device')
    cc.start('INVENTORY_get_device', get_device, False)

    cc.register('INVENTORY_get_all_devices')
    cc.start('INVENTORY_get_all_devices', get_all_devices, False)

    cc.register('INVENTORY_get_all_devices_as_dynamic_fork_tasks')
    cc.start('INVENTORY_get_all_devices_as_dynamic_fork_tasks', get_all_devices_as_dynamic_fork_tasks, False)

    cc.register('INVENTORY_add_show_command')
    cc.start('INVENTORY_add_show_command', add_show_command, False)

    cc.register('INVENTORY_get_show_command')
    cc.start('INVENTORY_get_show_command', get_show_command, False)
