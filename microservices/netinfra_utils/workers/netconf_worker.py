from __future__ import print_function

import copy
import json
from string import Template

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response, elastic_url_base, elastic_headers

odl_url_netconf_mount = odl_url_base + "/config/network-topology:network-topology/topology/topology-netconf/node/"
odl_url_netconf_mount_oper = odl_url_base + "/operational/network-topology:network-topology/topology/topology-netconf/node/"

inventory_netconf_device_url = elastic_url_base + "/inventory-device/device/$id"

mount_template = {
    "node": 
        {
            "node-id": "",

            "netconf-node-topology:host": "",
            "netconf-node-topology:port": "",
            "netconf-node-topology:keepalive-delay":"",
            "netconf-node-topology:tcp-only":"",
            "netconf-node-topology:username": "",
            "netconf-node-topology:password": "",
        }
}


def execute_mount_netconf(task):
    device_id = task['inputData']['device_id']

    mount_body = copy.deepcopy(mount_template)

    mount_body["node"]["node-id"] = task['inputData']['device_id']
    mount_body["node"]["netconf-node-topology:host"] = task['inputData']['host']
    mount_body["node"]["netconf-node-topology:port"] = task['inputData']['port']
    mount_body["node"]["netconf-node-topology:keepalive-delay"] = task['inputData']['keepalive-delay']
    mount_body["node"]["netconf-node-topology:tcp-only"] = task['inputData']['tcp-only']
    mount_body["node"]["netconf-node-topology:username"] = task['inputData']['username']
    mount_body["node"]["netconf-node-topology:password"] = task['inputData']['password']

    if 'blacklist' in task['inputData'] and task['inputData']['blacklist'] is not None:
        mount_body["node"]["uniconfig-config:uniconfig-native-enabled"] = True
        mount_body["node"]["uniconfig-config:blacklist"] = {'uniconfig-config:path':[]}

        model_array = [model.strip() for model in task['inputData']['blacklist'].split(',')]
        for model in model_array:
            mount_body["node"]["uniconfig-config:blacklist"]["uniconfig-config:path"].append(model)

    id_url = odl_url_netconf_mount + device_id

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


def execute_unmount_netconf(task):
    device_id = task['inputData']['device_id']

    id_url = odl_url_netconf_mount + device_id

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    return {'status': 'COMPLETED', 'output': {'url': id_url,
                                              'response_code': response_code,
                                              'response_body': response_json},
            'logs': ["Mountpoint with ID %s removed" % device_id]}


def execute_check_netconf_id_available(task):
    device_id = task['inputData']['device_id']

    id_url = odl_url_netconf_mount + device_id

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


def execute_check_connected_netconf(task):
    device_id = task['inputData']['device_id']

    id_url = odl_url_netconf_mount_oper + device_id

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.ok and response_json["node"][0]["netconf-node-topology:connection-status"] == "connected":
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["Mountpoint with ID %s is connected" % device_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Mountpoint with ID %s not yet connected" % device_id]}


netconf_device_template = {
    "id": "",
    "host": "",
    "port": "",
    "keepalive-delay": "",
    "tcp-only": "",
    "username": "",
    "password": "",
    "topology": "netconf",
    "blacklist": "",
    "labels": []
}


def add_netconf_device(task):
    device_id = task['inputData']['device_id']

    id_url = Template(inventory_netconf_device_url).substitute({"id": device_id})

    add_body = copy.deepcopy(netconf_device_template)

    add_body["id"] = task['inputData']['device_id']
    add_body["host"] = task['inputData']['host']
    add_body["port"] = task['inputData']['port']
    add_body['keepalive-delay'] = task['inputData']['keepalive-delay']
    add_body['tcp-only'] = task['inputData']['tcp-only']
    add_body["username"] = task['inputData']['username']
    add_body["password"] = task['inputData']['password']
    add_body["blacklist"] = task['inputData']['blacklist']

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


def start(cc):
    print('Starting Netconf workers')

    cc.register('Netconf_mount_netconf')
    cc.start('Netconf_mount_netconf', execute_mount_netconf, False)

    cc.register('Netconf_unmount_netconf')
    cc.start('Netconf_unmount_netconf', execute_unmount_netconf, False)

    cc.register('Netconf_check_netconf_connected', {
        "name": "Netconf_check_netconf_connected",
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
    cc.start('Netconf_check_netconf_connected', execute_check_connected_netconf, False)

    cc.register('Netconf_check_netconf_id_available')
    cc.start('Netconf_check_netconf_id_available', execute_check_netconf_id_available, False)

    cc.register('INVENTORY_add_netconf_device')
    cc.start('INVENTORY_add_netconf_device', add_netconf_device, False)

