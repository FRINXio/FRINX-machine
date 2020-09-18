from __future__ import print_function

import copy
import json
from string import Template

import requests

from frinx_rest import odl_url_base, odl_credentials, parse_response, elastic_url_base, elastic_headers, add_uniconfig_tx_cookie

odl_url_netconf_mount = odl_url_base + "/data/network-topology:network-topology/topology=topology-netconf/node=$id"
odl_url_netconf_mount_oper = odl_url_base + "/data/network-topology:network-topology/topology=topology-netconf/node=$id?content=nonconfig"

mount_template = {
    "node": 
        {
            "node-id": "",

            "netconf-node-topology:host": "",
            "netconf-node-topology:port": "",
            "netconf-node-topology:keepalive-delay": "",
            "netconf-node-topology:tcp-only": "",
            "netconf-node-topology:username": "",
            "netconf-node-topology:password": "",
        }
}


def execute_mount_netconf(task):
    device_id = task['inputData']['device_id']
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    mount_body = copy.deepcopy(mount_template)

    mount_body["node"]["node-id"] = task['inputData']['device_id']
    mount_body["node"]["netconf-node-topology:host"] = task['inputData']['host']
    mount_body["node"]["netconf-node-topology:port"] = task['inputData']['port']
    mount_body["node"]["netconf-node-topology:keepalive-delay"] = task['inputData']['keepalive-delay']
    mount_body["node"]["netconf-node-topology:tcp-only"] = task['inputData']['tcp-only']
    mount_body["node"]["netconf-node-topology:username"] = task['inputData']['username']
    mount_body["node"]["netconf-node-topology:password"] = task['inputData']['password']

    if 'reconcile' in task['inputData'] and task['inputData']['reconcile'] is not None\
            and task['inputData']['reconcile'] is not"":
        mount_body["node"]["node-extension:reconcile"] = task['inputData']['reconcile']

    if 'sleep-factor' in task['inputData'] and task['inputData']['sleep-factor'] is not None\
            and task['inputData']['sleep-factor'] is not "":
        mount_body["node"]["netconf-node-topology:sleep-factor"] = task['inputData']['sleep-factor']

    if 'between-attempts-timeout-millis' in task['inputData'] and task['inputData']['between-attempts-timeout-millis'] is not None\
            and task['inputData']['between-attempts-timeout-millis'] is not "":
        mount_body["node"]["netconf-node-topology:between-attempts-timeout-millis"] = task['inputData']['between-attempts-timeout-millis']

    if 'connection-timeout-millis' in task['inputData'] and task['inputData']['connection-timeout-millis'] is not None\
            and task['inputData']['connection-timeout-millis'] is not "":
        mount_body["node"]["netconf-node-topology:connection-timeout-millis"] = task['inputData']['connection-timeout-millis']

    if 'uniconfig-native' in task['inputData'] and task['inputData']['uniconfig-native'] is not None\
            and task['inputData']['uniconfig-native'] is not "":
        mount_body["node"]["uniconfig-config:uniconfig-native-enabled"] = task['inputData']['uniconfig-native']

    if 'blacklist' in task['inputData'] and task['inputData']['blacklist'] is not None:
        mount_body["node"]["uniconfig-config:blacklist"] = {'uniconfig-config:path':[]}
        model_array = [model.strip() for model in task['inputData']['blacklist'].split(',')]
        for model in model_array:
            mount_body["node"]["uniconfig-config:blacklist"]["uniconfig-config:path"].append(model)
            
    if 'dry-run-journal-size' in task['inputData'] and task['inputData']['dry-run-journal-size'] is not None:
        mount_body["node"]["netconf-node-topology:dry-run-journal-size"] = task['inputData']['dry-run-journal-size']

    id_url = Template(odl_url_netconf_mount).substitute({"id": device_id})

    r = requests.put(id_url, data=json.dumps(mount_body), headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
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


def execute_unmount_netconf(task):
    device_id = task['inputData']['device_id']
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_netconf_mount).substitute({"id": device_id})

    r = requests.delete(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
    response_code, response_json = parse_response(r)

    return {'status': 'COMPLETED', 'output': {'url': id_url,
                                              'response_code': response_code,
                                              'response_body': response_json},
            'logs': ["Mountpoint with ID %s removed" % device_id]}


def execute_check_netconf_id_available(task):
    device_id = task['inputData']['device_id']
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_netconf_mount).substitute({"id": device_id}) + "?content=config"

    r = requests.get(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
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
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_netconf_mount_oper).substitute({"id": device_id})

    r = requests.get(id_url, headers=add_uniconfig_tx_cookie(uniconfig_tx_id), auth=odl_credentials)
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


def read_structured_data(task):
    device_id = task['inputData']['device_id']
    uri = task['inputData']['uri']
    uniconfig_tx_id = task['inputData']['uniconfig_tx_id'] if 'uniconfig_tx_id' in task['inputData'] else ""

    id_url = Template(odl_url_netconf_mount).substitute({"id": device_id}) + "/yang-ext:mount" + (uri if uri else "")

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


def start(cc):
    print('Starting Netconf workers')

    cc.register('Netconf_mount_netconf', {
        "name": "Netconf_mount_netconf",
        "description": "{\"description\": \"mount a Netconf device\", \"labels\": [\"BASICS\",\"NETCONF\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "host",
            "port",
            "keepalive-delay",
            "tcp-only",
            "username",
            "password",
            "uniconfig-native",
            "blacklist",
            "dry-run-journal-size",
            "reconcile",
            "sleep-factor",
            "between-attempts-timeout-millis",
            "connection-timeout-millis",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "request_body",
            "response_code",
            "response_body"
        ]
    })
    cc.start('Netconf_mount_netconf', execute_mount_netconf, False)

    cc.register('Netconf_unmount_netconf', {
        "name": "Netconf_unmount_netconf",
        "description": "{\"description\": \"unmount a CLI device\", \"labels\": [\"BASICS\",\"NETCONF\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
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
            "device_id",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('Netconf_check_netconf_connected', execute_check_connected_netconf, False)

    cc.register('Netconf_check_netconf_id_available', {
        "name": "Netconf_check_netconf_id_available",
        "description": "{\"description\": \"checks if netconf device is available\", \"labels\": [\"BASICS\",\"NETCONF\"]}",
        "retryCount": 0,
        "timeoutSeconds": 60,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 10,
        "inputKeys": [
            "device_id",
            "uniconfig_tx_id"
        ],
        "outputKeys": [
            "url",
            "response_code",
            "response_body"
        ]
    })
    cc.start('Netconf_check_netconf_id_available', execute_check_netconf_id_available, False)

    cc.register('Netconf_read_structured_device_data', {
        "name": "Netconf_read_structured_device_data",
        "description": "{\"description\": \"Read device configuration or operational data in structured format e.g. netconf\", \"labels\": [\"BASICS\",\"NETCONF\"]}",
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
    cc.start('Netconf_read_structured_device_data', read_structured_data, False)
