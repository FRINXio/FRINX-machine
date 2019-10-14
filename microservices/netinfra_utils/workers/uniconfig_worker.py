from __future__ import print_function

import copy
import json
import re
import urllib
from string import Template

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response

odl_url_uniconfig_config_shallow = odl_url_base + "/config/network-topology:network-topology/topology/uniconfig?depth=3"
odl_url_uniconfig_oper = odl_url_base + "/operational/network-topology:network-topology/topology/uniconfig"
odl_url_uniconfig_config = odl_url_base + "/config/network-topology:network-topology/topology/uniconfig"
odl_url_uniconfig_mount = odl_url_base + "/config/network-topology:network-topology/topology/uniconfig/node/"
odl_url_uniconfig_commit = odl_url_base + '/operations/uniconfig-manager:commit'
odl_url_uniconfig_dryrun_commit = odl_url_base + '/operations/dryrun-manager:dryrun-commit'
odl_url_uniconfig_checked_commit = odl_url_base + '/operations/uniconfig-manager:checked-commit'
odl_url_uniconfig_calculate_diff = odl_url_base + '/operations/uniconfig-manager:calculate-diff'
odl_url_uniconfig_sync_from_network = odl_url_base + '/operations/uniconfig-manager:sync-from-network'
odl_url_uniconfig_replace_config_with_operational = odl_url_base + '/operations/uniconfig-manager:replace-config-with-operational'
odl_url_uniconfig_create_snapshot = odl_url_base + '/operations/snapshot-manager:create-snapshot'
odl_url_uniconfig_delete_snapshot = odl_url_base + '/operations/snapshot-manager:delete-snapshot'
odl_url_uniconfig_replace_config_with_snapshot = odl_url_base + '/operations/snapshot-manager:replace-config-with-snapshot'


def execute_read_uniconfig_topology_operational(task):
    devices = task['inputData']['device'] if 'device' in task['inputData'] else []
    response_code, response_json = read_all_devices(odl_url_uniconfig_oper) if len(devices) == 0 else read_selected_devices(odl_url_uniconfig_oper, devices)

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
    devices = task['inputData']['device'] if 'device' in task['inputData'] else []
    response_code, response_json = read_all_devices(odl_url_uniconfig_config) if len(devices) == 0 else read_selected_devices(odl_url_uniconfig_config, devices)

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


def read_all_devices(url):
    r = requests.get(url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)
    return response_code, response_json


def read_selected_devices(url, devices):
    response_code = requests.codes.ok
    response_json = {
        'topology': [
            {
                'node': []
            }
        ],
        'topology-id': 'uniconfig',
        'topology-types': {
            'frinx-uniconfig-topology:uniconfig': {}
        }
    }
    for d in devices:
        r = requests.get(url + "/node/" + d + "/", headers=odl_headers, auth=odl_credentials)
        response_code, response_json_tmp = parse_response(r)
        response_json['topology'][0]['node'].append(response_json_tmp['node'][0])
        if response_code != requests.codes.ok:
            raise "Cannot read device '" + d + "' from uniconfig topology"
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
    subworkflow = task['inputData']['task']
    add_params = task['inputData']['task_params']
    add_params = json.loads(add_params) if isinstance(add_params, basestring) else (add_params if add_params else {})

    response_code, response_json = read_all_devices(odl_url_uniconfig_config_shallow)

    if response_code == requests.codes.ok:
        print(response_json)
        ids = map(lambda x: x["node-id"], response_json["topology"][0]["node"])
        print(ids)

        dynamic_tasks_i = {}
        for device_id in ids:
            per_device_params = dict(add_params)
            per_device_params.update({"id": device_id})
            dynamic_tasks_i.update({device_id: per_device_params})

        dynamic_tasks = []
        for device_id in ids:
            task_body = copy.deepcopy(task_body_template)
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
    uri = re.sub(escape_regex, lambda match: urllib.quote(match.group(1), safe=''), uri)
    return uri


def read_structured_data(task):
    device_id = task['inputData']['id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)

    id_url = odl_url_uniconfig_mount + device_id + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
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
    device_id = task['inputData']['id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    template = task['inputData']['template']
    params = task['inputData']['params']
    params = json.loads(params) if isinstance(params, basestring) else (params if params else {})

    data_json = template if isinstance(template, basestring) else json.dumps(template if template else {})
    data_json = Template(data_json).substitute(params)

    id_url = odl_url_uniconfig_mount + device_id + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")
    id_url = Template(id_url).substitute(params)

    r = requests.put(id_url, data=data_json, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok or response_code == requests.codes.created:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


def write_structured_data_as_tasks(task):
    device_id = task['inputData']['id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)
    template = task['inputData']['template']
    add_params = task['inputData']['task_params']
    add_params = json.loads(add_params) if isinstance(add_params, basestring) else (add_params if add_params else {})

    dynamic_tasks_i = {}
    dynamic_tasks = []
    for param in add_params:
        data_json = template if isinstance(template, basestring) else json.dumps(template if template else {})
        data_json = Template(data_json).substitute(iface=param)
        escaped_param = param.replace("/", "%2F")
        url = Template(uri).substitute(iface=escaped_param)
        per_iface_params = {"id": device_id, "template": data_json, "uri": url}
        key = device_id + param
        dynamic_tasks_i.update({key:per_iface_params})
        task_body = copy.deepcopy(task_body_template)
        task_body["taskReferenceName"] = key
        task_body["subWorkflowParam"]["name"] = "Write_structured_device_data_in_uniconfig"
        dynamic_tasks.append(task_body)

    return {'status': 'COMPLETED', 'output': {'dynamic_tasks_i': dynamic_tasks_i,
                                              'dynamic_tasks': dynamic_tasks},
            'logs': []}


def delete_structured_data(task):
    device_id = task['inputData']['id']
    uri = task['inputData']['uri']
    uri = apply_functions(uri)

    id_url = odl_url_uniconfig_mount + device_id + "/frinx-uniconfig-topology:configuration" + (uri if uri else "")

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Node with ID %s updated successfully" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to update device with ID %s" % device_id]}


commit_input = {
    "input": {
        "target-nodes": {

        }
    }
}


def commit(task):
    r = requests.post(odl_url_uniconfig_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-configuration-status"] == "complete":
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
    r = requests.post(odl_url_uniconfig_dryrun_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-configuration-status"] == "complete":
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
    r = requests.post(odl_url_uniconfig_checked_commit,
                      data=json.dumps(create_commit_request(task)),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-configuration-status"] == "complete":
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
    r = requests.post(odl_url_uniconfig_calculate_diff,
                      data=json.dumps(create_commit_request(task)),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
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
    r = requests.post(odl_url_uniconfig_sync_from_network,
                      data=json.dumps(create_commit_request(task)),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["overall-sync-status"] == "complete":
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
    r = requests.post(odl_url_uniconfig_replace_config_with_operational,
                      data=json.dumps(create_commit_request(task)),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["result"] == "complete":
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
    snapshot_body = create_snapshot_request(task)
    r = requests.post(odl_url_uniconfig_create_snapshot,
                      data=json.dumps(snapshot_body),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["result"] == "complete":
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


def delete_snapshot(task):
    snapshot_body = copy.deepcopy(snapshot_template)
    snapshot_body["input"]["name"] = task["inputData"]["name"]

    r = requests.post(odl_url_uniconfig_delete_snapshot,
                      data=json.dumps(snapshot_body),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok:
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
    snapshot_body = create_snapshot_request(task)
    r = requests.post(odl_url_uniconfig_replace_config_with_snapshot,
                      data=json.dumps(snapshot_body),
                      headers=odl_headers,
                      auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["output"]["result"] == "complete":
        return {'status': 'COMPLETED', 'output': {'url': odl_url_uniconfig_replace_config_with_snapshot,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Uniconfig replace config with snapshot was successful"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_uniconfig_replace_config_with_snapshot,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Uniconfig replace config with snapshot failed"]}


def start(cc):
    print('Starting Uniconfig workers')

    cc.register('UNICONFIG_read_unified_topology_operational')
    cc.start('UNICONFIG_read_unified_topology_operational', execute_read_uniconfig_topology_operational, False)

    cc.register('UNICONFIG_read_unified_topology_config')
    cc.start('UNICONFIG_read_unified_topology_config', execute_read_uniconfig_topology_config, False)

    cc.register('UNICONFIG_get_all_devices_as_tasks')
    cc.start('UNICONFIG_get_all_devices_as_tasks', get_all_devices_as_tasks, False)

    cc.register('UNICONFIG_read_structured_device_data')
    cc.start('UNICONFIG_read_structured_device_data', read_structured_data, False)

    cc.register('UNICONFIG_write_structured_device_data')
    cc.start('UNICONFIG_write_structured_device_data', write_structured_data, False)

    cc.register('UNICONFIG_write_structured_data_as_tasks')
    cc.start('UNICONFIG_write_structured_data_as_tasks', write_structured_data_as_tasks, False)

    cc.register('UNICONFIG_delete_structured_device_data')
    cc.start('UNICONFIG_delete_structured_device_data', delete_structured_data, False)

    cc.register('UNICONFIG_commit')
    cc.start('UNICONFIG_commit', commit, False)

    cc.register('UNICONFIG_dryrun_commit')
    cc.start('UNICONFIG_dryrun_commit', dryrun_commit, False)

    cc.register('UNICONFIG_checked_commit')
    cc.start('UNICONFIG_checked_commit', checked_commit, False)

    cc.register('UNICONFIG_calculate_diff')
    cc.start('UNICONFIG_calculate_diff', calc_diff, False)

    cc.register('UNICONFIG_sync_from_network')
    cc.start('UNICONFIG_sync_from_network', sync_from_network, False)

    cc.register('UNICONFIG_replace_config_with_oper')
    cc.start('UNICONFIG_replace_config_with_oper', replace_config_with_oper, False)

    cc.register('UNICONFIG_create_snapshot')
    cc.start('UNICONFIG_create_snapshot', create_snapshot, False)

    cc.register('UNICONFIG_delete_snapshot')
    cc.start('UNICONFIG_delete_snapshot', delete_snapshot, False)

    cc.register('UNICONFIG_replace_config_with_snapshot')
    cc.start('UNICONFIG_replace_config_with_snapshot', replace_config_with_snapshot, False)
