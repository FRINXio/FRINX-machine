from __future__ import print_function

import copy
from string import Template

import uniconfig_worker

odl_url_uniconfig_network_instance_config = '/frinx-openconfig-network-instance:network-instances/network-instance/$vll'


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
                'type': 'frinx-openconfig-network-instance-types:L2P2P'
            }
        }
    ]
}

vlan_template = {
    "vlans": {
        "vlan": [
            {
                "vlan-id": 0
            }
        ]
    }
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
                'type': 'frinx-openconfig-network-instance-types:L2P2P'
            }
        }
    ]
}


def device_create_vll_remote(task):
    vll_config = create_vll_remote_request(task)
    response = uniconfig_worker.write_structured_data({'inputData': {
        'id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vll': (task['inputData']['service_id'])})),
        'template': vll_config, 'params': {}}})
    response.update({'vll_data': vll_config})
    return response


def device_create_vll_local(task):
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
    if task['inputData'].get('vlan') is not None:
        cp1['endpoints']['endpoint'][0]['local']['config']['subinterface'] = task['inputData']['vlan']
        vlans = copy.deepcopy(vlan_template)
        vlans['vlans']['vlan'][0]['vlan-id'] = task['inputData']['vlan']
        instance.update(vlans)

    cp2 = instance['connection-points']['connection-point'][1]
    cp2['endpoints']['endpoint'][0]['remote']['config']['remote-system'] = task['inputData']['remote_ip']
    cp2['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'] = task['inputData']['vccid']
    return vll_body


def create_vll_base_request(task, template):
    vll_body = copy.deepcopy(template)
    instance = vll_body['network-instance'][0]
    instance['name'] = task['inputData']['service_id']
    instance['config']['name'] = task['inputData']['service_id']
    mtu = task['inputData'].get('mtu')
    if mtu:
        instance['config']['mtu'] = mtu
    return instance, vll_body


def create_vll_local_request(task):
    instance, vll_body = create_vll_base_request(task, vll_local_template)

    cp1 = instance['connection-points']['connection-point'][0]
    instance['interfaces']['interface'][0]['id'] = task['inputData']['interface_1']
    cp1['endpoints']['endpoint'][0]['local']['config']['interface'] = task['inputData']['interface_1']
    cp1['endpoints']['endpoint'][0]['local']['config']['interface'] = task['inputData']['interface_1']
    if task['inputData'].get('vlan_1') is not None:
        cp1['endpoints']['endpoint'][0]['local']['config']['subinterface'] = task['inputData']['vlan_1']
        vlans = copy.deepcopy(vlan_template)
        vlans['vlans']['vlan'][0]['vlan-id'] = task['inputData']['vlan_1']
        instance.update(vlans)

    cp2 = instance['connection-points']['connection-point'][1]

    if not task['inputData']['interface_2'] == task['inputData']['interface_1']:
        instance['interfaces']['interface'][1]['id'] = task['inputData']['interface_2']
    else:
        instance['interfaces']['interface'].pop(1)

    cp2['endpoints']['endpoint'][0]['local']['config']['interface'] = task['inputData']['interface_2']
    if task['inputData'].get('vlan_2') is not None:
        cp2['endpoints']['endpoint'][0]['local']['config']['subinterface'] = task['inputData']['vlan_2']
        vlans = copy.deepcopy(vlan_template)
        vlans['vlans']['vlan'][0]['vlan-id'] = task['inputData']['vlan_2']
        instance.update(vlans)

    return vll_body


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
