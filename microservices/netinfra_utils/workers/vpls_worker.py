from __future__ import print_function

import copy
from string import Template

import uniconfig_worker

odl_url_uniconfig_network_instance_config = '/frinx-openconfig-network-instance:network-instances/network-instance=$vpls'


vpls_response_template = {
    'network-instance': [
        {
            'name': '',
            'interfaces': {
                'interface': [
                ]
            },
            'vlans': {
                'vlan': [
                ]
            },
            'connection-points': {
                'connection-point': [
                ]
            },
            'config': {
                'name': '',
                'type': 'frinx-openconfig-network-instance-types:L2VSI'
            }
        }
    ]
}

vpls_local_cp_template = {
    'connection-point-id': '',
    'config': {
        'connection-point-id': ''
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

vpls_remote_cp_template = {
    'connection-point-id': '',
    'config': {
        'connection-point-id': ''
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


def device_create_vpls(task):
    vpls_config = create_vpls_request(task)
    response = uniconfig_worker.write_structured_data({'inputData': {
        'device_id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vpls': (task['inputData']['service_id'])})),
        'template': vpls_config, 'params': {}}})
    response.update({'vpls_data': vpls_config})
    return response


def device_delete_vpls(task):
    return uniconfig_worker.delete_structured_data({'inputData': {
        'device_id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vpls': (task['inputData']['service_id'])})),
    }})


def device_read_vpls(task):
    return uniconfig_worker.read_structured_data({'inputData': {
        'device_id': task['inputData']['id'],
        'uri': (Template(odl_url_uniconfig_network_instance_config).substitute({'vpls': (task['inputData']['service_id'])})),
    }})


def create_vpls_request(task):
    instance, vpls_body = create_vpls_base_request(task, vpls_response_template)

    for ifc in task['inputData']['interface']:
        size = str(len(instance['connection-points']['connection-point']) + 1)
        cp1 = copy.deepcopy(vpls_local_cp_template)
        cp1['connection-point-id'] = size
        cp1['config']['connection-point-id'] = size
        ifc_cfg = {
            'id': ifc['interface']
        }
        instance['interfaces']['interface'].append(ifc_cfg)
        vlan_cfg = {
            'vlan-id': ifc['vlan']
        }
        if vlan_cfg not in instance['vlans']['vlan']:
            instance['vlans']['vlan'].append(vlan_cfg)

        cp1['endpoints']['endpoint'][0]['local']['config']['interface'] = ifc['interface']
        cp1['endpoints']['endpoint'][0]['local']['config']['subinterface'] = ifc['vlan']
        if ifc['untagged']:
            cp1['endpoints']['endpoint'][0]['local']['config']['frinx-brocade-cp-extension:subinterface-untagged'] = ifc['untagged']
        instance['connection-points']['connection-point'].append(cp1)

    for r in task['inputData']['remote_ip']:
        size = str(len(instance['connection-points']['connection-point']) + 1)
        cp2 = copy.deepcopy(vpls_remote_cp_template)
        cp2['connection-point-id'] = size
        cp2['config']['connection-point-id'] = size
        cp2['endpoints']['endpoint'][0]['remote']['config']['remote-system'] = r
        cp2['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'] = task['inputData']['vccid']
        instance['connection-points']['connection-point'].append(cp2)
    return vpls_body


def create_vpls_base_request(task, template):
    vpls_body = copy.deepcopy(template)
    instance = vpls_body['network-instance'][0]
    instance['name'] = task['inputData']['service_id']
    instance['config']['name'] = task['inputData']['service_id']
    mtu = task['inputData'].get('mtu')
    if mtu:
        instance['config']['mtu'] = mtu
    return instance, vpls_body


def start(cc):
    print('Start VPLS workers')

    # Single device level configuration

    cc.register('VPLS_device_create')
    cc.start('VPLS_device_create', device_create_vpls, False)

    cc.register('VPLS_device_delete')
    cc.start('VPLS_device_delete', device_delete_vpls, False)

    cc.register('VPLS_device_read')
    cc.start('VPLS_device_read', device_read_vpls, False)
