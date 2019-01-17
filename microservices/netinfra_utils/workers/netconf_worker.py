from __future__ import print_function

import json
from string import Template

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response

odl_url_netconf_mount = odl_url_base + "/config/network-topology:network-topology/topology/topology-netconf/node/"

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
    device_id = task['inputData']['id']

    mount_body = mount_template.copy()

    mount_body["node"]["node-id"] = task['inputData']['id']
    mount_body["node"]["netconf-node-topology:host"] = task['inputData']['host']
    mount_body["node"]["netconf-node-topology:port"] = task['inputData']['port']
    mount_body["node"]["netconf-node-topology:keepalive-delay"] = task['inputData']['keepalive-delay']
    mount_body["node"]["netconf-node-topology:tcp-only"] = task['inputData']['tcp-only']
    mount_body["node"]["netconf-node-topology:username"] = task['inputData']['username']
    mount_body["node"]["netconf-node-topology:password"] = task['inputData']['password']

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
    device_id = task['inputData']['id']

    id_url = odl_url_netconf_mount + device_id

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    return {'status': 'COMPLETED', 'output': {'url': id_url,
                                              'response_code': response_code,
                                              'response_body': response_json},
            'logs': ["Mountpoint with ID %s removed" % device_id]}


def execute_check_netconf_id_available(task):
    device_id = task['inputData']['id']

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
    device_id = task['inputData']['id']

    id_url = odl_url_netconf_mount_oper + device_id

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


def start(cc):
    print('Starting Netconf workers')

    cc.start('Netconf_mount_netconf', execute_mount_netconf, False)
    cc.start('Netconf_unmount_netconf', execute_unmount_netconf, False)
    cc.start('Netconf_check_netconf_connected', execute_check_connected_netconf, False)
    cc.start('Netconf_check_netconf_id_available', execute_check_netconf_id_available, False)

