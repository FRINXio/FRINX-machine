from __future__ import print_function

import copy
import json
import re
import urllib
from string import Template

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response, parse_header, add_uniconfig_tx_cookie

odl_url_uniconfig_config_shallow = odl_url_base + "/data/network-topology:network-topology/topology=uniconfig?content=config&depth=3"
odl_url_uniconfig_oper = odl_url_base + "/data/network-topology:network-topology/topology=uniconfig?content=nonconfig"
odl_url_uniconfig_node_oper = odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=$id?content=nonconfig"
odl_url_uniconfig_config = odl_url_base + "/data/network-topology:network-topology/topology=uniconfig?content=config"
odl_url_uniconfig_node_config = odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=$id?content=config"
odl_url_uniconfig_mount = odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=$id"
odl_url_uniconfig_commit = odl_url_base + '/operations/uniconfig-manager:commit'
odl_url_uniconfig_dryrun_commit = odl_url_base + '/operations/dryrun-manager:dryrun-commit'
odl_url_uniconfig_checked_commit = odl_url_base + '/operations/uniconfig-manager:checked-commit'
odl_url_uniconfig_calculate_diff = odl_url_base + '/operations/uniconfig-manager:calculate-diff'
odl_url_uniconfig_sync_from_network = odl_url_base + '/operations/uniconfig-manager:sync-from-network'
odl_url_uniconfig_replace_config_with_operational = odl_url_base + '/operations/uniconfig-manager:replace-config-with-operational'
odl_url_uniconfig_create_snapshot = odl_url_base + '/operations/snapshot-manager:create-snapshot'
odl_url_uniconfig_delete_snapshot = odl_url_base + '/operations/snapshot-manager:delete-snapshot'
odl_url_uniconfig_replace_config_with_snapshot = odl_url_base + '/operations/snapshot-manager:replace-config-with-snapshot'
odl_url_uniconfig_create_transaction = odl_url_base + '/operations/uniconfig-manager:create-transaction?maxAgeSec=$sec'
odl_url_uniconfig_close_transaction = odl_url_base + '/operations/uniconfig-manager:close-transaction'


def execute_read_uniconfig_topology_operational(task):
    devices = task['inputData']['devices'] if 'devices' in task['inputData'] else []
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    response_code, response_json = read_all_devices(odl_url_uniconfig_oper, uniconfig_tx_id)\
        if len(devices) == 0 else read_selected_devices(odl_url_uniconfig_node_oper, devices, uniconfig_tx_id)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_oper,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_oper,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def execute_read_uniconfig_topology_config(task):
    devices = task['inputData']['devices'] if 'devices' in task['inputData'] else []
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    response_code, response_json = read_all_devices(odl_url_uniconfig_config, uniconfig_tx_id) \
        if len(devices) == 0 else read_selected_devices(odl_url_uniconfig_node_config, devices, uniconfig_tx_id)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_config,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_config,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def read_all_devices(url, uniconfig_tx_id):
    r = requests.get(url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
    response_code, response_json = parse_response(r)
    return response_code, response_json


def read_selected_devices(url, devices, uniconfig_tx_id):
    response_code = requests.codes.ok
    response_json = {
        'topology': [
            {
                'node': []
            }
        ]
    }
    devices_array = [device.strip() for device in devices.split(',')]
    for d in devices_array:
        r = requests.get(Template(url).substitute({"id": d}), headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
        response_code, response_json_tmp = parse_response(r)
        response_json['topology'][0]['node'].append(response_json_tmp['node'][0])
        if response_code != requests.codes.ok:
            raise "Cannot read device '" + d + "' from uniconfig topology"
    return response_code, response_json


subworkflow_template = {
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
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    response_code, response_json = read_all_devices(odl_url_uniconfig_config_shallow, uniconfig_tx_id)

    if response_code == requests.codes.ok:
        ids = [nodes["node-id"] for nodes in response_json["topology"][0]["node"]]

        dynamic_tasks_i = {}
        for device_id in ids:
            per_device_params = dict(add_params)
            per_device_params.update({"device_id": device_id})
            dynamic_tasks_i.update({device_id: per_device_params})

        dynamic_tasks = []
        for device_id in ids:
            task_body = copy.deepcopy(subworkflow_template)
            if optional == "true":
                task_body['optional'] = True
            task_body["taskReferenceName"] = device_id
            task_body["subWorkflowParam"]["name"] = subworkflow
            dynamic_tasks.append(task_body)

        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_config_shallow,
                                                  'dynamic_tasks_i': dynamic_tasks_i,
                                                  'dynamic_tasks': dynamic_tasks},
                'logs': []}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_config_shallow,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': []}


def apply_functions(uri):
    if not uri:
        return uri
    escape_regex = r"escape\(([^\)]*)\)"
    uri = re.sub(escape_regex, lambda match: urllib.parse.quote(match.group(1), safe=''), uri)
    return uri


def read_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_uniconfig_mount).substitute({"id": device_id}) + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")

    r = requests.get(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s read successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to read device with ID %s" % device_id]}


def write_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    template = task['inputData']['template']
    params = task['inputData']['params']
    params = json.loads(params) if isinstance(params, str) else (params if params else {})
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    data_json = template if isinstance(template, str) else json.dumps(template if template else {})
    data_json = Template(data_json).substitute(params)

    id_url = Template(odl_url_uniconfig_mount).substitute({"id": device_id}) + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")
    id_url = Template(id_url).substitute(params)

    r = requests.put(id_url, data=data_json, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.no_content or response_code == requests.codes.created:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


task_body_template = {
    "name": "",
    "taskReferenceName": "",
    "type": "SIMPLE"
}


def write_structured_data_as_dynamic_fork_tasks(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    template = task['inputData']['template']
    add_params = task['inputData']['task_params']
    add_params = [param.strip() for param in add_params.split(',')] if isinstance(add_params, str) else (add_params if add_params else {})

    dynamic_tasks_i = {}
    dynamic_tasks = []
    for param in add_params:
        data_json = template if isinstance(template, str) else json.dumps(template if template else {})
        data_json = Template(data_json).substitute(iface=param)
        escaped_param = param.replace("/", "%2F")
        url = Template(uri).substitute(iface=escaped_param)
        per_iface_params = {"device_id": device_id, "template": data_json, "uri": url, "params": {}}
        key = device_id + param
        dynamic_tasks_i.update({key: per_iface_params})
        task_body = copy.deepcopy(task_body_template)
        task_body["taskReferenceName"] = key
        task_body["name"] = "UNICONFIG_write_structured_device_data"
        dynamic_tasks.append(task_body)

    return {'status': 'COMPLETED', 'output': {'dynamic_tasks_i': dynamic_tasks_i,
                                              'dynamic_tasks': dynamic_tasks},
            'logs': []}


def delete_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_uniconfig_mount).substitute({"id": device_id}) + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")

    r = requests.delete(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.no_content:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


def execute_check_uniconfig_node_exists(task):
    device_id = task['inputData']['device_id']
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_uniconfig_mount).substitute({"id": device_id}) + "/frinx-uniconfig-topology:connection-status?content=nonconfig"

    r = requests.get(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code != requests.codes.not_found and response_json["frinx-uniconfig-topology:connection-status"] == "installed":
        # Mountpoint with such ID already exists
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig mountpoint with ID %s exists" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig mountpoint with ID %s doesn't exist" % device_id]}


commit_input = {
    "input": {
        "target-nodes": {

        }
    }
}


def commit(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(odl_url_uniconfig_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_commit,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig commit successfully"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_commit,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable commit failed"]}


def dryrun_commit(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(odl_url_uniconfig_dryrun_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_dryrun_commit,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig dryrun commit successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_dryrun_commit,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig dryrun commit failed"]}


def checked_commit(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(odl_url_uniconfig_checked_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_checked_commit,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig checked commit successfully"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_checked_commit,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable checked commit failed"]}


def calc_diff(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(odl_url_uniconfig_calculate_diff,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_calculate_diff,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig calculate diff successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_calculate_diff,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig calculate diff failed"]}


def sync_from_network(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(odl_url_uniconfig_sync_from_network,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_sync_from_network,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig sync successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_sync_from_network,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig sync failed"]}


def replace_config_with_oper(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    r = requests.post(odl_url_uniconfig_replace_config_with_operational,
                      data=json.dumps(create_commit_request(task)),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_replace_config_with_operational,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig replace successfull"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_replace_config_with_operational,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig replace failed"]}


snapshot_template = {
        "input": {
            "name": "",
            "target-nodes": {

            }
        }
    }


def create_snapshot(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    snapshot_body = create_snapshot_request(task)
    r = requests.post(odl_url_uniconfig_create_snapshot,
                      data=json.dumps(snapshot_body),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_create_snapshot,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig create snapshot successful"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_create_snapshot,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig create snapshot failed"]}


def create_snapshot_request(task):
    snapshot_body = copy.deepcopy(snapshot_template)
    snapshot_body["input"]["name"] = task["inputData"]["name"]
    device_list = parse_devices(task)
    if device_list:
        snapshot_body["input"]["target-nodes"]["node"] = device_list
    return snapshot_body


def create_commit_request(task):
    commit_body = copy.deepcopy(commit_input)
    device_list = parse_devices(task)
    if device_list:
        commit_body["input"]["target-nodes"]["node"] = device_list
    return commit_body


def parse_devices(task):
    devices = task['inputData'].get('devices', [])
    if type(devices) is list:
        extracted_devices = devices
    else:
        extracted_devices = [x.strip() for x in devices.split(",") if x is not ""] if devices else []

    if len(extracted_devices) is 0:
        raise Exception("For Uniconfig RPCs, a list of devices needs to be specified. "
               "Global RPCs (involving all devices in topology) are not allowed for your own safety.")
    return extracted_devices


delete_snapshot_template = {
    "input": {
        "name": "",
    }
}


def delete_snapshot(task):
    snapshot_body = copy.deepcopy(delete_snapshot_template)
    snapshot_body["input"]["name"] = task["inputData"]["name"]
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    r = requests.post(odl_url_uniconfig_delete_snapshot,
                      data=json.dumps(snapshot_body),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_delete_snapshot,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig delete snapshot successful"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_delete_snapshot,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig delete snapshot failed"]}


def replace_config_with_snapshot(task):
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""
    snapshot_body = create_snapshot_request(task)
    r = requests.post(odl_url_uniconfig_replace_config_with_snapshot,
                      data=json.dumps(snapshot_body),
                      headers=add_uniconfig_tx_cookie(uniconfig_tx_id),
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-status"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_replace_config_with_snapshot,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig replace config with snapshot was successful"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_replace_config_with_snapshot,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig replace config with snapshot failed"]}


def create_transaction(task):
    max_age_sec = task["inputData"]["maxAgeSec"] if 'maxAgeSec' in task['inputData'] else ""
    id_url = Template(odl_url_uniconfig_create_transaction).substitute({"sec": max_age_sec})
    r = requests.post(id_url,
                      data=json.dumps({}),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)
    if response_code == requests.codes.created:
        response_json = parse_header(r)
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig create transaction was successful"]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig create transaction failed"]}


def close_transaction(task):
    uniconfig_tx_id = task["inputData"]["uniconfig_tx_id"]
    custom_header = {"Cookie": "UNICONFIGTXID="+uniconfig_tx_id} if uniconfig_tx_id else {"Cookie": ""}
    r = requests.post(odl_url_uniconfig_close_transaction,
                      data=json.dumps({}),
                      headers=custom_header,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)
    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_close_transaction,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig close transaction was successful"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_close_transaction,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig close transaction failed"]}


def start(cc):
    print('Starting Uniconfig workers')

    cc.register('UNICONFIG_read_uniconfig_topology_operational', {
        "name": "UNICONFIG_read_uniconfig_topology_operational",
        "description": "{\"description\": \"Read operational state of Uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNICONFIG_read_uniconfig_topology_operational', execute_read_uniconfig_topology_operational, False)

    cc.register('UNICONFIG_read_uniconfig_topology_config', {
        "name": "UNICONFIG_read_uniconfig_topology_config",
        "description": "{\"description\": \"Read config state of Uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNICONFIG_read_uniconfig_topology_config', execute_read_uniconfig_topology_config, False)

    cc.register('UNICONFIG_get_all_devices_as_dynamic_fork_tasks', {
        "name": "UNICONFIG_get_all_devices_as_dynamic_fork_tasks",
        "description": "{\"description\": \"get all devices in uniconfig topology as dynamic fork tasks\", \"labels\": [\"BASICS\"\",\"UNICONFIG\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "task",
            "task_params",
            "optional",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "dynamic_tasks_i",
            "dynamic_tasks"
        ]
    })
    cc.start('UNICONFIG_get_all_devices_as_dynamic_fork_tasks', get_all_devices_as_dynamic_fork_tasks, False)

    cc.register('UNICONFIG_read_structured_device_data', {
        "name": "UNICONFIG_read_structured_device_data",
        "description": "{\"description\": \"Read device configuration or operational data in structured format e.g. openconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\",\"OPENCONFIG\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uri",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNICONFIG_read_structured_device_data', read_structured_data, False)

    cc.register('UNICONFIG_write_structured_device_data', {
        "name": "UNICONFIG_write_structured_device_data",
        "description": "{\"description\": \"Write device configuration data in structured format e.g. openconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
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
            "params",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNICONFIG_write_structured_device_data', write_structured_data, False)

    cc.register('UNICONFIG_write_structured_data_as_dynamic_fork_tasks', {
        "name": "UNICONFIG_write_structured_data_as_dynamic_fork_tasks",
        "description": "{\"description\": \"Write device configuration data in strucuted format e.g. openconfig as a task\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
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
            "dynamic_tasks_i",
            "dynamic_tasks"
        ]
    })
    cc.start('UNICONFIG_write_structured_data_as_dynamic_fork_tasks', write_structured_data_as_dynamic_fork_tasks, False)

    cc.register('UNICONFIG_delete_structured_device_data', {
        "name": "UNICONFIG_delete_structured_device_data",
        "description": "{\"description\": \"Delete device configuration data in structured format e.g. openconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\",\"OPENCONFIG\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uri",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('UNICONFIG_delete_structured_device_data', delete_structured_data, False)

    cc.register('UNICONFIG_commit', {
        "name": "UNICONFIG_commit",
        "description": "{\"description\": \"Commit uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_commit', commit, False)

    cc.register('UNICONFIG_dryrun_commit', {
        "name": "UNICONFIG_dryrun_commit",
        "description": "{\"description\": \"Dryrun Commit uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_dryrun_commit', dryrun_commit, False)

    cc.register('UNICONFIG_checked_commit', {
        "name": "UNICONFIG_checked_commit",
        "description": "{\"description\": \"Checked Commit uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_checked_commit', checked_commit, False)

    cc.register('UNICONFIG_calculate_diff', {
        "name": "UNICONFIG_calculate_diff",
        "description": "{\"description\": \"Calculate uniconfig diff\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_calculate_diff', calc_diff, False)

    cc.register('UNICONFIG_sync_from_network', {
        "name": "UNICONFIG_sync_from_network",
        "description": "{\"description\": \"Sync uniconfig from network\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_sync_from_network', sync_from_network, False)

    cc.register('UNICONFIG_replace_config_with_oper', {
        "name": "UNICONFIG_replace_config_with_oper",
        "description": "{\"description\": \"Replace config with oper in uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_replace_config_with_oper', replace_config_with_oper, False)

    cc.register('UNICONFIG_create_snapshot', {
        "name": "UNICONFIG_create_snapshot",
        "description": "{\"description\": \"Create snapshot in uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "name",
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_create_snapshot', create_snapshot, False)

    cc.register('UNICONFIG_delete_snapshot', {
        "name": "UNICONFIG_delete_snapshot",
        "description": "{\"description\": \"Delete snapshot in uniconfig\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "name",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_delete_snapshot', delete_snapshot, False)

    cc.register('UNICONFIG_replace_config_with_snapshot', {
        "name": "UNICONFIG_replace_config_with_snapshot",
        "description": "{\"description\": \"Replace config with snapshot\",  \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "name",
            "devices",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_replace_config_with_snapshot', replace_config_with_snapshot, False)

    cc.register('UNICONFIG_check_uniconfig_node_exists', {
        "name": "UNICONFIG_check_uniconfig_node_exists",
        "retryCount": 20,
        "timeoutSeconds": 10,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 5,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uniconfig_tx_id"
        ]
    })
    cc.start('UNICONFIG_check_uniconfig_node_exists', execute_check_uniconfig_node_exists, False)

    cc.register('UNICONFIG_create_transaction', {
        "name": "UNICONFIG_create_transaction",
        "description": "{\"description\": \"Create uniconfig transaction\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "maxAgeSec"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_create_transaction', create_transaction, False)

    cc.register('UNICONFIG_close_transaction', {
        "name": "UNICONFIG_close_transaction",
        "description": "{\"description\": \"Close uniconfig transaction\", \"labels\": [\"BASICS\",\"UNICONFIG\"]}",
        "inputKeys": [
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ],
        "retryCount": 0,
        "responseTimeoutSeconds": 600
    })
    cc.start('UNICONFIG_close_transaction', close_transaction, False)
