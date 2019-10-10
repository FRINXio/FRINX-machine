from __future__ import print_function

import json

import requests

from frinx_rest import odl_url_base, odl_headers, odl_credentials, parse_response

odl_url_l3vpn = odl_url_base + "/config/ietf-l3vpn-svc:l3vpn-svc/vpn-services/vpn-service/"
odl_url_l3vpn_site = odl_url_base + "/config/ietf-l3vpn-svc:l3vpn-svc/sites/site/"
odl_url_l3vpn_commit = odl_url_base + "/operations/ietf-l3vpn-svc:commit-l3vpn-svc"

l3vpn_template = {
    "vpn-service": [
        {
            "vpn-id": "",
            "customer-name": "",
            "vpn-service-topology": "any-to-any",
            "l3vpn-param:vrf-name": "",
            "l3vpn-param:route-distinguisher": "",
            "l3vpn-param:import-route-targets": {
                "route-target": ""
            },
            "l3vpn-param:export-route-targets": {
                "route-target": ""
            }
        }
    ]
}


def create_l3vpn_instance(task):
    vpn_id = task['inputData']['vpn-id']

    l3vpn_body = l3vpn_template.copy()

    l3vpn_body["vpn-service"][0]["vpn-id"] = task['inputData']['vpn-id']
    l3vpn_body["vpn-service"][0]["customer-name"] = task['inputData']['vpn-customer']
    l3vpn_body["vpn-service"][0]["l3vpn-param:vrf-name"] = task['inputData']['vpn-id']
    l3vpn_body["vpn-service"][0]["l3vpn-param:route-distinguisher"] = task['inputData']['vpn-rd']
    l3vpn_body["vpn-service"][0]["l3vpn-param:import-route-targets"]["route-target"] = task['inputData'][
        'vpn-route-target']
    l3vpn_body["vpn-service"][0]["l3vpn-param:export-route-targets"]["route-target"] = task['inputData'][
        'vpn-route-target']

    id_url = odl_url_l3vpn + vpn_id

    r = requests.put(id_url, data=json.dumps(l3vpn_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'request_body': l3vpn_body,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["L3VPN with ID %s registered" % vpn_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'request_body': l3vpn_body,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to register L3VPN with ID %s" % vpn_id]}


def delete_l3vpn_instance(task):
    vpn_id = task['inputData']['vpn-id']

    id_url = odl_url_l3vpn + vpn_id

    r = requests.delete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["L3VPN with ID %s deleted" % vpn_id]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to delete L3VPN with ID %s" % vpn_id]}


l3vpn_site_template = {
    "site": [
        {
            "site-id": "",
            "site-vpn-flavor": "site-vpn-flavor-single",
            "management": {
                "type": "customer-managed"
            },
            "site-network-accesses": {
                "site-network-access": [
                    {
                        "l3vpn-param:pe-bgp-as": "",
                        "l3vpn-param:pe-bgp-router-id": "",
                        "l3vpn-param:route-policy-in": "",
                        "l3vpn-param:route-policy-out": "",
                        "site-network-access-id": "",
                        "bearer": {
                            "bearer-reference": "ios-pe/GigabitEthernet3/0"
                        },
                        "site-network-access-type": "multipoint",
                        "vpn-attachment": {
                            "vpn-id": "",
                            "site-role": "any-to-any-role"
                        },
                        "routing-protocols": {
                            "routing-protocol": [
                                {
                                    "type": "bgp",
                                    "bgp": {
                                        "autonomous-system": "",
                                        "address-family": [
                                            "ipv4"
                                        ]
                                    }
                                }
                            ]
                        },
                        "ip-connection": {
                            "ipv4": {
                                "address-allocation-type": "static-address",
                                "addresses": {
                                    "provider-address": "",
                                    "customer-address": "",
                                    "prefix-length": ""
                                }
                            }
                        }

                    }
                ]
            }
        }
    ]
}


def create_l3vpn_site(task):
    vpn_id = task['inputData']['vpn-id']
    site_id = task['inputData']['site-id']

    l3vpn_body = l3vpn_site_template.copy()

    l3vpn_body["site"][0]["site-id"] = task['inputData']['site-id']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["l3vpn-param:pe-bgp-as"] = task['inputData']['pe-as']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["l3vpn-param:pe-bgp-router-id"] = task['inputData']['bgp-router-id']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["l3vpn-param:route-policy-in"] = task['inputData']['bgp-route-policy']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["l3vpn-param:route-policy-out"] = task['inputData']['bgp-route-policy']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["site-network-access-id"] = task['inputData']['site-network-access-id']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["bearer"]["bearer-reference"] = task['inputData']['device-id'] + "/" + task['inputData']['device-interface']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["vpn-attachment"]["vpn-id"] = vpn_id
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["routing-protocols"]["routing-protocol"][0]["bgp"]["autonomous-system"] = task['inputData']['vpn-as']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["ip-connection"]["ipv4"]["addresses"]["provider-address"] = task['inputData']['provider-ip']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["ip-connection"]["ipv4"]["addresses"]["customer-address"] = task['inputData']['customer-ip']
    l3vpn_body["site"][0]["site-network-accesses"]["site-network-access"][0]["ip-connection"]["ipv4"]["addresses"]["prefix-length"] = task['inputData']['prefix-length']

    id_url = odl_url_l3vpn_site + site_id

    r = requests.put(id_url, data=json.dumps(l3vpn_body), headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'request_body': l3vpn_body,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["L3VPN site with ID %s registered for VPN: %s" % (site_id, vpn_id)]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'request_body': l3vpn_body,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to register L3VPN site with ID %s" % site_id]}


def delete_l3vpn_site(task):
    site_id = task['inputData']['site-id']

    id_url = odl_url_l3vpn_site + site_id

    r = requests.dalete(id_url, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': id_url,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["L3VPN site with ID %s deleted for VPN: %s" % (site_id, vpn_id)]}
    else:
        return {'status': 'FAILED', 'output': {'url': id_url,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to deleted L3VPN site with ID %s" % site_id]}


def commit_l3vpn(task):
    r = requests.post(odl_url_l3vpn_commit, headers=odl_headers, auth=odl_credentials)
    response_code, response_json = parse_response(r)

    if response_code == requests.codes.created or response_code == requests.codes.ok:
        return {'status': 'COMPLETED', 'output': {'url': odl_url_l3vpn_commit,
                                                  'response_code': response_code,
                                                  'response_body': response_json},
                'logs': ["L3VPN committed"]}
    else:
        return {'status': 'FAILED', 'output': {'url': odl_url_l3vpn_commit,
                                               'response_code': response_code,
                                               'response_body': response_json},
                'logs': ["Unable to commit L3VPN"]}


def start(cc):
    print('Starting L3VPN workers')

    cc.register('L3VPN_create_l3vpn_instance')
    cc.start('L3VPN_create_l3vpn_instance', create_l3vpn_instance, False)

    cc.register('L3VPN_delete_l3vpn_instance')
    cc.start('L3VPN_delete_l3vpn_instance', delete_l3vpn_instance, False)

    cc.register('L3VPN_create_l3vpn_site')
    cc.start('L3VPN_create_l3vpn_site', create_l3vpn_site, False)

    cc.register('L3VPN_delete_l3vpn_site')
    cc.start('L3VPN_delete_l3vpn_site', delete_l3vpn_site, False)

    cc.register('L3VPN_commit_l3vpn')
    cc.start('L3VPN_commit_l3vpn', commit_l3vpn, False)

