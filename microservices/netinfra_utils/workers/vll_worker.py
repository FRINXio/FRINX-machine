from __future__ import print_function

import copy
import itertools
import urllib
from string import Template

import uniconfig_worker

odl_url_uniconfig_network_instance_config = '/frinx-openconfig-network-instance:network-instances/network-instance/$vll'
odl_url_uniconfig_ifc_config = '/frinx-openconfig-interfaces:interfaces/interface/$ifc'


vll_local_template = {
    'network-instance': [
        {
            'name': '',
            'interfaces': {
                'interface': [
                    {
                        'id': ''
                    },
                    {
                        'id': ''
                    }
                ]
            },
            'connection-points': {
                'connection-point': [
                    {
                        'connection-point-id': '1',
                        'config': {
                            'connection-point-id': '1'
                        },
                        'endpoints': {
                            'endpoint': [
                                {
                                    'endpoint-id': 'default',
                                    'config': {
                                        'endpoint-id': 'default',
                                        'precedence': 0,
                                        'type': 'frinx-openconfig-network-instance-types:LOCAL'
                                    },
                                    'local': {
                                        'config': {
                                            'interface': ''
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'connection-point-id': '2',
                        'config': {
                            'connection-point-id': '2'
                        },
                        'endpoints': {
                            'endpoint': [
                                {
                                    'endpoint-id': 'default',
                                    'config': {
                                        'endpoint-id': 'default',
                                        'precedence': 0,
                                        'type': 'frinx-openconfig-network-instance-types:LOCAL'
                                    },
                                    'local': {
                                        'config': {
                                            'interface': ''
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            'config': {
                'name': '',
                'type': 'frinx-openconfig-network-instance-types:L2P2P',
                'mtu': 0
            }
        }
    ]
}


vll_remote_template = {
    'network-instance': [
        {
            'name': '',
            'interfaces': {
                'interface': [
                    {
                        'id': ''
                    }
                ]
            },
            'connection-points': {
                'connection-point': [
                    {
                        'connection-point-id': '1',
                        'config': {
                            'connection-point-id': '1'
                        },
                        'endpoints': {
                            'endpoint': [
                                {
                                    'endpoint-id': 'default',
                                    'config': {
                                        'endpoint-id': 'default',
                                        'precedence': 0,
                                        'type': 'frinx-openconfig-network-instance-types:LOCAL'
                                    },
                                    'local': {
                                        'config': {
                                            'interface': ''
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'connection-point-id': '2',
                        'config': {
                            'connection-point-id': '2'
                        },
                        'endpoints': {
                            'endpoint': [
                                {
                                    'endpoint-id': 'default',
                                    'config': {
                                        'endpoint-id': 'default',
                                        'precedence': 0,
                                        'type': 'frinx-openconfig-network-instance-types:REMOTE'
                                    },
                                    'remote': {
                                        'config': {
                                            'remote-system': '',
                                            'virtual-circuit-identifier': 0
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            'config': {
                'name': '',
                'type': 'frinx-openconfig-network-instance-types:L2P2P',
                'mtu': 0
            }
        }
    ]
}


def device_create_vll_remote(task):
    # FIXME support subinterfaces (vlans)
    vll_config = create_vll_remote_request(task)
    response = uniconfig_worker.write_structured_data({'inputData': {
        'id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vll': (task['inputData']['service_id'])})),
        'template': vll_config, 'params': {}}})
    response.update({'vll_data': vll_config})
    return response


def read_interface(device, interface):
    ifc = urllib.quote(interface, safe='')
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': ifc})
    ifc_response = uniconfig_worker.read_structured_data({'inputData': {
        'id': device,
        'uri': url,
    }})
    return ifc_response


def put_interface(device, interface, description):
    # TODO add autoneg mode
    ifc = urllib.quote(interface, safe='')
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': ifc})
    ifc_config = {
        "frinx-openconfig-interfaces:interface": [
            {
                "name": interface,
                "config": {
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "name": interface,
                    "description": description,
                    "frinx-brocade-if-extension:priority": 3,
                    "frinx-brocade-if-extension:priority-force": True,
                    "frinx-openconfig-vlan:tpid": "frinx-openconfig-vlan-types:TPID_0X8100"
                }
            }
        ]
    }
    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def device_create_vll_local(task):
    # FIXME support subinterfaces (vlans)
    vll_config = create_vll_local_request(task)
    response = uniconfig_worker.write_structured_data({'inputData': {
        'id': task['inputData']['id'], 'uri': (
        Template(odl_url_uniconfig_network_instance_config).substitute({'vll': (task['inputData']['service_id'])})),
        'template': vll_config, 'params': {}}})
    response.update({'vll_data': vll_config})
    return response


def device_delete_vll(task):
    return uniconfig_worker.delete_structured_data({'inputData': {
        'id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vll': (task['inputData']['service_id'])})),
    }})


def device_read_vll(task):
    return uniconfig_worker.read_structured_data({'inputData': {
        'id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vll': (task['inputData']['service_id'])})),
    }})


def create_vll_remote_request(task):
    instance, vll_body = create_vll_base_request(task, vll_remote_template)

    cp1 = instance['connection-points']['connection-point'][0]
    instance['interfaces']['interface'][0]['id'] = task['inputData']['interface']
    cp1['endpoints']['endpoint'][0]['local']['config']['interface'] = task['inputData']['interface']

    cp2 = instance['connection-points']['connection-point'][1]
    cp2['endpoints']['endpoint'][0]['remote']['config']['remote-system'] = task['inputData']['remote_ip']
    cp2['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'] = task['inputData']['vccid']
    return vll_body


def create_vll_base_request(task, template):
    vll_body = copy.deepcopy(template)
    instance = vll_body['network-instance'][0]
    instance['name'] = task['inputData']['service_id']
    instance['config']['name'] = task['inputData']['service_id']
    mtu = task['inputData'].get('mtu', 0)
    if mtu == 0:
        instance['config'].pop('mtu')
    else:
        instance['config']['mtu'] = mtu
    return instance, vll_body


def create_vll_local_request(task):
    instance, vll_body = create_vll_base_request(task, vll_local_template)

    cp1 = instance['connection-points']['connection-point'][0]
    instance['interfaces']['interface'][0]['id'] = task['inputData']['interface_1']
    cp1['endpoints']['endpoint'][0]['local']['config']['interface'] = task['inputData']['interface_1']

    cp2 = instance['connection-points']['connection-point'][1]

    if not task['inputData']['interface_2'] == task['inputData']['interface_1']:
        instance['interfaces']['interface'][1]['id'] = task['inputData']['interface_2']
    else:
        instance['interfaces']['interface'].pop(1)

    cp2['endpoints']['endpoint'][0]['local']['config']['interface'] = task['inputData']['interface_2']
    return vll_body


def service_create_vll_local(task):
    service_id, devices, service = parse_service(task)
    device_1_id, device_1_ifc = parse_device_local(devices, 0)
    device_2_id, device_2_ifc = parse_device_local(devices, 1)

    assert device_2_id == device_1_id, 'For local VLL service, 1 device is expected. Received: %s, %s' % (device_1_id, device_2_id)

    response1 = device_create_vll_local({'inputData': {
        'id': device_1_id,
        'service_id': service_id,
        'interface_1': device_1_ifc,
        'interface_2': device_2_ifc,
        'mtu': service['mtu'] if 'mtu' in service else 0
    }})
    if response1['status'] is not 'COMPLETED':
        response1_delete = remove_device_vll(device_1_id, service_id)

        return {'status': 'FAILED', 'output': {'response': response1,
                                               'response_for_rollback': response1_delete,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service_id]}}

    return {'status': 'COMPLETED', 'output': {'response': response1,
                                              'logs': ['VLL instance: %s configured in uniconfig successfully' % service_id]}}


def service_create_vll(task):
    service_id, devices, _ = parse_service(task)
    device_1_id, device_1_ifc = parse_device_local(devices, 0)
    device_2_id, device_2_ifc = parse_device_local(devices, 1)

    # TODO check if service already exists on one of the devices, if so, fail
    # TODO add update vll so that it finds existing service, removes it and creates a new one

    if device_1_id == device_2_id:
        return service_create_vll_local(task)
    elif not device_1_id == device_2_id:
        return service_create_vll_remote(task)


def service_delete_vll(task):
    # TODO implement
    raise NotImplementedError


def service_delete_vll_dryrun(task):
    # FIXME
    raise NotImplementedError


def service_create_vll_dryrun(task):
    # TODO refactor the input parameter parsing. Create dedicated class for Service and Device and also parsing/serialization for them and use that to load dictionaries into classes and use those
    service_id, devices, _ = parse_service(task)
    device_1_id, device_1_ifc = parse_device_local(devices, 0)
    device_2_id, device_2_ifc = parse_device_local(devices, 1)

    ifc_response = read_interface(device_1_id, device_1_ifc)
    if ifc_response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                                        % (service_id, device_1_id, device_1_ifc)]}}

    ifc_response = read_interface(device_2_id, device_2_ifc)
    if ifc_response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Interface %s does not exist'
                                                        % (service_id, device_2_id, device_2_ifc)]}}

    ifc_put_response1 = put_interface(device_1_id, device_1_ifc, service_id)
    if ifc_put_response1['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_put_response1,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                                        % (service_id, device_1_id, device_1_ifc)]}}

    ifc_put_response2 = put_interface(device_2_id, device_2_ifc, service_id)
    if ifc_put_response2['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_put_response2,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                                        % (service_id, device_2_id, device_2_ifc)]}}

    # TODO disable STP on ports, also for commit
    # TODO configure policies, also for commit
    # TODO refactor, too much duplicate code especially dryrun vs commit

    response = service_create_vll(task)
    if response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service_id]}}

    response_dryrun = uniconfig_worker.dryrun_commit({'inputData': {
        'devices': [device_1_id, device_2_id],
    }})

    if response_dryrun['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response,
                                               'response_dryrun': response_dryrun,
                                               'logs': ['VLL instance: %s dry-run FAIL' % service_id]}}

    # FIXNE, check response_dryrun overall configuration status not just 'status' for failure, same for commit
    # "response_dryrun": {
    #     "logs": [
    #         "Uniconfig dryrun commit successfull"
    #     ],
    #     "output": {
    #         "response_body": {
    #             "output": {
    #                 "node-config-results": {
    #                     "node-config-result": [
    #                         {
    #                             "configuration-status": "complete",
    #                             "node-id": "B28",
    #                             "rollback-status": "complete"
    #                         },
    #                         {
    #                             "configuration-status": "fail",
    #                             "error-message": "Interface ethernet 3/4 already used in L2P2P network as: ethernet 3/4\n",
    #                             "error-type": "processing-error",
    #                             "node-id": "B21",
    #                             "rollback-status": "complete"
    #                         }
    #                     ]
    #                 },
    #                 "overall-configuration-status": "fail"
    #             }
    #         },
    #         "response_code": 200,
    #         "url": "http://localhost:8181/restconf/operations/dryrun-manager:dryrun-commit"
    #     },
    #     "status": "COMPLETED"
    # }

    return {'status': 'COMPLETED', 'output': {'response_device1_interface': ifc_put_response1,
                                              'response_device2_interface': ifc_put_response2,
                                              'response_network_instance': response,
                                              'response_dryrun': response_dryrun,
                                              'logs': ['VLL instance: %s dry-run successful' % service_id]}}


def service_delete_vll_commit(task):
    # FIXME
    raise NotImplementedError

def service_create_vll_commit(task):
    service_id, devices, _ = parse_service(task)
    device_1_id, device_1_ifc = parse_device_local(devices, 0)
    device_2_id, device_2_ifc = parse_device_local(devices, 1)

    ifc_response = read_interface(device_1_id, device_1_ifc)
    if ifc_response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                                        % (service_id, device_1_id, device_1_ifc)]}}

    ifc_response = read_interface(device_2_id, device_2_ifc)
    if ifc_response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Interface %s does not exist'
                                                        % (service_id, device_2_id, device_2_ifc)]}}

    ifc_put_response = put_interface(device_1_id, device_1_ifc, service_id)
    if ifc_put_response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_put_response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                                        % (service_id, device_1_id, device_1_ifc)]}}

    ifc_put_response = put_interface(device_2_id, device_2_ifc, service_id)
    if ifc_put_response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': ifc_put_response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                                        % (service_id, device_2_id, device_2_ifc)]}}

    response = service_create_vll(task)
    if response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service_id]}}

    response_commit = uniconfig_worker.commit({'inputData': {
        'devices': [device_2_id, device_2_id],
    }})

    if response_commit['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response,
                                               'response_dryrun': response_commit,
                                               'logs': ['VLL instance: %s commit FAIL' % service_id]}}
        # TODO, replace config with oper here on failure, to get back to previous state ?

    return {'status': 'COMPLETED', 'output': {'response': response,
                                              'response_dryrun': response_commit,
                                              'logs': ['VLL instance: %s commit successful' % service_id]}}


def service_create_vll_remote(task):
    service_id, vccid, devices, service = parse_service_vccid(task)
    device_1_id, device_1_ifc, device_1_remote_ip = parse_device_remote(devices, 0)
    device_2_id, device_2_ifc, device_2_remote_ip = parse_device_remote(devices, 1)

    assert not device_2_id == device_1_id, 'For remote VLL service, 2 different devices are expected. Received: %s, %s' % (device_1_id, device_2_id)

    response1 = device_create_vll_remote({'inputData': {
        'id': device_1_id,
        'service_id': service_id,
        'vccid': vccid,
        'interface': device_1_ifc,
        'remote_ip': device_1_remote_ip,
        'mtu': service['mtu'] if service.has_key('mtu') else 0
    }})
    if response1['status'] is not 'COMPLETED':
        response1_delete = remove_device_vll(device_1_id, service_id)

        return {'status': 'FAILED', 'output': {'response': response1,
                                               'response_for_rollback': response1_delete,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service_id]}}

    response2 = device_create_vll_remote({'inputData': {
        'id': device_2_id,
        'service_id': service_id,
        'vccid': vccid,
        'interface': device_2_ifc,
        'remote_ip': device_2_remote_ip,
        'mtu': service['mtu'] if service.has_key('mtu') else 0
    }})
    if response2['status'] is not 'COMPLETED':
        response1_delete = remove_device_vll(device_1_id, service_id)
        response2_delete = remove_device_vll(device_2_id, service_id)

        return {'status': 'FAILED', 'output': {'response_1': response1,
                                               'response_2': response2,
                                               'response_1_for_rollback': response1_delete,
                                               'response_2_for_rollback': response2_delete,
                                               'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service_id]}}

    return {'status': 'COMPLETED', 'output': {'response_1': response1,
                                              'response_2': response2,
            'logs': ['VLL instance: %s configured in uniconfig successfully' % service_id]}}


def service_delete_vll_remote(task):
    service_id, devices, _ = parse_service(task)
    device_1_id = devices[0]['id']
    device_2_id = devices[1]['id']

    assert not device_2_id == device_1_id, 'For remote VLL service, 2 different devices are expected. Received: %s, %s' % (device_1_id, device_2_id)

    response1 = remove_device_vll(device_1_id, service_id)
    if response1['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response1,
                                               'logs': ['VLL instance: %s removal in uniconfig FAIL' % service_id]}}

    response2 = remove_device_vll(device_2_id, service_id)
    if response2['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response2,
                                               'logs': ['VLL instance: %s removal in uniconfig FAIL' % service_id]}}

    return {'status': 'COMPLETED', 'output': {'response_1': response1,
                                              'response_2': response2,
                                              'logs': ['VLL instance: %s removed in uniconfig successfully' % service_id]}}


def service_delete_vll_local(task):
    service_id, devices, _ = parse_service(task)
    device_1_id = devices[0]['id']
    device_2_id = devices[1]['id']

    assert device_2_id == device_1_id, 'For remote VLL service, 1 device are expected. Received: %s, %s' % (device_1_id, device_2_id)

    response = remove_device_vll(device_1_id, service_id)
    if response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response,
                                               'logs': ['VLL instance: %s removal in uniconfig FAIL' % service_id]}}

    return {'status': 'COMPLETED', 'output': {'response': response,
                                              'logs': ['VLL instance: %s removed in uniconfig successfully' % service_id]}}


def parse_service_vccid(task):
    service_id, devices, service = parse_service(task)
    vccid = service['vccid']
    assert vccid is not None, 'Service VCCID is missing'
    return service_id, vccid, devices, service


def parse_service(task):
    template = task['inputData']['service']
    service = template if isinstance(template, dict) else eval(template)
    service_id = service['id']
    assert service_id is not None, 'Service ID is missing'
    devices = service['devices']
    assert len(devices) is 2, 'For VLL service, 2 devices are expected. Received: %s' % len(devices)
    return service_id, devices, service


def parse_device_remote(devices, index):
    device_id = devices[index]['id']
    device_ifc = devices[index]['interface']
    device_remote_ip = devices[index]['remote_ip']

    assert device_id is not None, 'Device #%s ID is missing' % index + 1
    assert device_ifc is not None, 'Device #%s INTERFACE is missing' % index + 1
    assert device_remote_ip is not None, 'Device #%s REMOTE_IP is missing' % index + 1

    return device_id, device_ifc, device_remote_ip


def parse_device_local(devices, index):
    device_id = devices[index]['id']
    device_ifc = devices[index]['interface']

    assert device_id is not None, 'Device #%s ID is missing' % index + 1
    assert device_ifc is not None, 'Device #%s INTERFACE is missing' % index + 1

    return device_id, device_ifc


def remove_device_vll(device_id, service_id):
    return device_delete_vll({'inputData': {
        'id': device_id,
        'service_id': service_id
    }})


def l2p2p_local_to_service(node_id, l2p2p):
    service = {
        'id': l2p2p.get('name', 'Unable to find name'),
        'devices': [
            {
                'id': node_id,
                'interface':
                    l2p2p['connection-points']['connection-point'][0]['endpoints']['endpoint'][0]['local']['config']['interface'],
            },
            {
                'id': node_id,
                'interface':
                    l2p2p['connection-points']['connection-point'][1]['endpoints']['endpoint'][0]['local']['config']['interface'],
            }
        ]
    }

    vlan1 = l2p2p['connection-points']['connection-point'][0]['endpoints']['endpoint'][0]['local']['config'].get('subinterface', None)
    if vlan1:
        service['devices'][0]['vlan'] = vlan1

    vlan2 = l2p2p['connection-points']['connection-point'][1]['endpoints']['endpoint'][0]['local']['config'].get('subinterface', None)
    if vlan2:
        service['devices'][1]['vlan'] = vlan2

    return service


def l2p2p_remote_to_service(node_id, l2p2p):
    cps = l2p2p.get('connection-points', {}).get('connection-point')
    local = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:LOCAL', cps)[0]
    remote = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:REMOTE', cps)[0]

    service = {
        'id': l2p2p.get('name', 'Unable to find name'),
        'vccid': remote['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'],
        'devices': [
            {
                'id': node_id,
                'interface': local['endpoints']['endpoint'][0]['local']['config']['interface'],
                'remote_ip': remote['endpoints']['endpoint'][0]['remote']['config']['remote-system'],
            }
        ]
    }

    vlan1 = local['endpoints']['endpoint'][0]['local']['config'].get('subinterface', None)
    if vlan1:
        service['devices'][0]['vlan'] = vlan1

    return service


def service_read_all(task):
    # TODO add device filtering
    # TODO add vll-local vs vll selections
    # TODO (low prio) add service name filtering
    # TODO (low prio) add service vccid filtering

    datastore = task['inputData'].get('datastore', 'actual')
    if datastore not in ['intent', 'actual']:
        return {'status': 'FAILED', 'output': {'logs': ['Unable to read uniconfig datastore: %s' % datastore]}}

    response = uniconfig_worker.execute_read_uniconfig_topology_operational(task) if datastore == 'actual' \
        else uniconfig_worker.execute_read_uniconfig_topology_config(task)

    if response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response,
                                               'logs': ['Unable to read uniconfig']}}

    reconciliation = task['inputData'].get('reconciliation', 'name')
    if reconciliation not in ['name', 'vccid']:
        return {'status': 'FAILED', 'output': {'logs': ['Unable to reconcile with strategy: %s' % reconciliation]}}

    uniconfig_nodes = response['output']['response_body']['topology'][0]['node']

    node_2_l2p2p = map(
        lambda n: (n['node-id'], extract_network_instances(n, 'frinx-openconfig-network-instance-types:L2P2P')),
        uniconfig_nodes)

    local_services = []
    remote_services = []
    for node in node_2_l2p2p:

        node_id = node[0]
        l2p2ps = node[1]
        if len(l2p2ps) is 0:
            continue

        for l2p2p in l2p2ps:
            if vll_type(l2p2p) == 'LOCAL':
                local_services.append(l2p2p_local_to_service(node_id, l2p2p))
            elif vll_type(l2p2p) == 'REMOTE':
                remote_services.append(l2p2p_remote_to_service(node_id, l2p2p))
            else:
                # incomplete configuration or unknown flavour of l2p2p
                continue

    remote_services = aggregate_l2p2p_remote(remote_services) if reconciliation == 'name' \
        else aggregate_l2p2p_remote(remote_services, lambda service: service['vccid'])

    services = local_services + remote_services
    return {'status': 'COMPLETED', 'output': {'services': services,
                                              'logs': ['VLL instances found successfully: %s' % len(services)]}}


def aggregate_l2p2p_remote(remote_services, by_key=lambda remote_l2p2p: remote_l2p2p['id']):
    remote_services.sort(key=by_key)
    grouped_by_name = itertools.groupby(remote_services, by_key)
    grouped_by_name_as_list = map(lambda g: list(g[1]), grouped_by_name)
    remote_services_aggregated = map(lambda l: reduce(lambda l1, l2: aggregate_remote(l1, l2), l), grouped_by_name_as_list)
    return remote_services_aggregated


def aggregate_remote(l1, l2):
    # TODO check same name/vccid ?
    l1['devices'] = l1['devices'] + l2['devices']
    return l1


def vll_type(l2p2p):
    cps = l2p2p.get('connection-points', {}).get('connection-point', [])

    if len(cps) is not 2:
        return False

    endpoint1 = cps[0].get('endpoints', {}).get('endpoint', [])
    if len(endpoint1) is not 1:
        return False

    endpoint2 = cps[1].get('endpoints', {}).get('endpoint', [])
    if len(endpoint2) is not 1:
        return False

    e1_type = endpoint1[0].get('config', {}).get('type', '')
    e2_type = endpoint2[0].get('config', {}).get('type', '')
    endpoint_types = [e1_type, e2_type]

    if e1_type == 'frinx-openconfig-network-instance-types:LOCAL' and e2_type == e1_type:
        return 'LOCAL'
    elif 'frinx-openconfig-network-instance-types:REMOTE' in endpoint_types \
            and 'frinx-openconfig-network-instance-types:LOCAL' in endpoint_types:
        return 'REMOTE'
    else:
        return 'UNKNOWN'


def extract_network_instances(node, type):
    networks = node['frinx-uniconfig-topology:configuration']['frinx-openconfig-network-instance:network-instances']['network-instance']
    l2p2p = filter(lambda ni: ni['config']['type'] == type, networks)
    return l2p2p


def start(cc):
    print('Starting VLL workers')

    # Single device level configuration

    cc.register('VLL_device_create_remote')
    cc.start('VLL_device_create_remote', device_create_vll_remote, False)

    cc.register('VLL_device_create_local')
    cc.start('VLL_device_create_local', device_create_vll_local, False)

    cc.register('VLL_device_delete')
    cc.start('VLL_device_delete', device_delete_vll, False)

    cc.register('VLL_device_read')
    cc.start('VLL_device_read', device_read_vll, False)

    # Service level configuration (spanning multiple devices)

    cc.register('VLL_service_create')
    cc.start('VLL_service_create', service_create_vll, False)

    cc.register('VLL_service_delete')
    cc.start('VLL_service_delete', service_delete_vll, False)

    cc.register('VLL_service_create_remote')
    cc.start('VLL_service_create_remote', service_create_vll_remote, False)

    cc.register('VLL_service_delete_remote')
    cc.start('VLL_service_delete_remote', service_delete_vll_remote, False)

    cc.register('VLL_service_create_local')
    cc.start('VLL_service_create_local', service_create_vll_local, False)

    cc.register('VLL_service_delete_local')
    cc.start('VLL_service_delete_local', service_delete_vll_local, False)

    # Batch reconciliation from per device info into service objects

    cc.register('VLL_service_read_all')
    cc.start('VLL_service_read_all', service_read_all, False)

    # Below are higher order workers (which actually implement a more complex workflow)

    cc.register('VLL_service_commit')
    cc.start('VLL_service_commit', service_create_vll_commit, False)

    cc.register('VLL_service_dryrun')
    cc.start('VLL_service_dryrun', service_create_vll_dryrun, False)

    cc.register('VLL_service_delete_commit')
    cc.start('VLL_service_delete_commit', service_delete_vll_commit, False)

    cc.register('VLL_service_delete_dryrun')
    cc.start('VLL_service_delete_dryrun', service_delete_vll_dryrun, False)
