from __future__ import print_function

import json
import copy

import requests
from string import Template

from frinx_rest import elastic_url_base, odl_url_base, odl_headers, odl_credentials, parse_response, elastic_headers

build_lldp_url = odl_url_base + "/operations/lldptopo:build"
export_lldp_url = odl_url_base + "/operations/lldptopo:export"
read_lldp_url = odl_url_base + "/data/network-topology:network-topology/topology=$topology?content=nonconfig"
inventory_lldp_url = elastic_url_base + "/inventory-lldp/lldp/$id"


lldp_build_template = {
  "input": {
    "node-aggregation": "",
    "link-aggregation": "",

    "per-node-read-timeout": 0,
    "concurrent-read-nodes": 0,

    "destination-topology": ""
  }
}


def build_lldp(task):
    topo_id = task['inputData']['destination-topology']

    lldp_body = copy.deepcopy(lldp_build_template)

    lldp_body["input"]["node-aggregation"] = task['inputData']['node-aggregation']
    lldp_body["input"]["link-aggregation"] = task['inputData']['link-aggregation']
    lldp_body["input"]["per-node-read-timeout"] = task['inputData']['per-node-read-timeout']
    lldp_body["input"]["concurrent-read-nodes"] = task['inputData']['concurrent-read-nodes']
    lldp_body["input"]["destination-topology"] = task['inputData']['destination-topology']

    r = requests.post(build_lldp_url, data=json.dumps(lldp_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': build_lldp_url,
                                                  'request_body': lldp_body,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["LLDP topology built and stored in %s" % topo_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': build_lldp_url,
                                               'request_body': lldp_body,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Failed to build LLDP topology %s" % topo_id]}


lldp_export_template = {
  "input": {
  }
}


def export_lldp(task):

    lldp_body = copy.deepcopy(lldp_export_template)

    r = requests.post(export_lldp_url, data=json.dumps(lldp_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': export_lldp_url,
                                                  'request_body': lldp_body,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["LLDP topology exported"]}
    else:
        return {'status': 'FAILED', 'output': {'url': export_lldp_url,
                                               'request_body': lldp_body,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Failed to export LLDP topology"]}


def read_lldp(task):
    topo_id = task['inputData']['destination-topology']

    id_url = Template(read_lldp_url).substitute({"topology": topo_id})

    r = requests.get(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["LLDP topology read: %s" % topo_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Failed to read LLDP topology: %s" % topo_id]}


def store_lldp(task):
    topo_id = task['inputData']['destination-topology']
    topo = task['inputData']['content']

    id_url = Template(inventory_lldp_url).substitute({"id": topo_id})

    add_body = {}
    add_body["lldp"] = task['inputData']['content']

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
    print('Starting LLDP topology workers')

    cc.register('LLDP_build_topology')
    cc.start('LLDP_build_topology', build_lldp, False)

    cc.register('LLDP_export_topology')
    cc.start('LLDP_export_topology', export_lldp, False)

    cc.register('LLDP_read_topology')
    cc.start('LLDP_read_topology', read_lldp, False)

    cc.register('LLDP_store_topology')
    cc.start('LLDP_store_topology', store_lldp, False)
