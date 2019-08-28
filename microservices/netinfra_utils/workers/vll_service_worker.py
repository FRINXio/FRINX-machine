from __future__ import print_function

import itertools
from string import Template
from vll_model import Service, LocalService, RemoteService, ServiceDeletion
import uniconfig_worker
import vll_worker

odl_url_uniconfig_ifc_config = '/frinx-openconfig-interfaces:interfaces/interface/escape($ifc)'
odl_url_uniconfig_ifc_policy_config = '/frinx-openconfig-network-instance:network-instances/network-instance/default/policy-forwarding/interfaces/interface/escape($ifc)'
odl_url_uniconfig_ifc_stp_config = '/frinx-stp:stp/interfaces/interface/escape($ifc)'


# Interface updates


def read_interface(device):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_response = uniconfig_worker.read_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return ifc_response


def delete_interface(device):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return ifc_response


# def put_interface(device, interface, description, auto_negotiate=True):
def put_interface(service, device):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_config = {
        "frinx-openconfig-interfaces:interface": [
            {
                "name": device.interface,
                "config": {
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "name": device.interface,
                    "description": device.description if device.description else service.id,
                    "frinx-brocade-if-extension:priority": 3,
                    "frinx-brocade-if-extension:priority-force": True

                }
            }
        ]
    }

    if device.auto_negotiate is not None:
        ifc_config['frinx-openconfig-interfaces:interface'][0].update({"frinx-openconfig-if-ethernet:ethernet": {
            "config": {
                "auto-negotiate": device.auto_negotiate
            }
        }})

    if device.tpid is not None:
        ifc_config['frinx-openconfig-interfaces:interface'][0]['config']["frinx-openconfig-vlan:tpid"] = device.tpid

    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def put_interface_policy(device):
    if device.in_policy is None and device.out_policy is None:
        return

    url = Template(odl_url_uniconfig_ifc_policy_config).substitute({'ifc': device.interface})
    ifc_config = {
        "frinx-openconfig-network-instance:interface": [
            {
                "interface-id": device.interface,
                "config": {
                    "interface-id": device.interface
                }
            }
        ]
    }

    if device.in_policy is not None:
        ifc_config['frinx-openconfig-network-instance:interface'][0]['config']['frinx-brocade-pf-interfaces-extension:input-service-policy'] = device.in_policy
    if device.out_policy is not None:
        ifc_config['frinx-openconfig-network-instance:interface'][0]['config']['frinx-brocade-pf-interfaces-extension:output-service-policy'] = device.out_policy

    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def disable_interface_stp(device):
    url = Template(odl_url_uniconfig_ifc_stp_config).substitute({'ifc': device.interface})

    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'id': device.id,
        'uri': url
    }})
    return ifc_response


# Uniconfig RPCs


def replace_cfg_with_oper(device_1, device_2):
    return uniconfig_worker.replace_config_with_oper({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


def sync_from_net(device_1, device_2):
    return uniconfig_worker.sync_from_network({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


def dryrun_commit(device_1, device_2):
    return uniconfig_worker.dryrun_commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


def commit(device_1, device_2):
    return uniconfig_worker.commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


# Retval Macros


def fail(log, **kwargs):
    output = {}
    output.update(kwargs)
    return {'status': 'FAILED', 'output': output, 'logs': [log]}


def complete(log, **kwargs):
    output = {}
    output.update(kwargs)
    return {'status': 'COMPLETED', 'output': output, 'logs': [log]}


def task_failed(task_response):
    return task_response['status'] is not 'COMPLETED'


def uniconfig_task_failed(task_response):
    config_status = task_response.get('output', {}).get('response_body', {}).get('output', {}).get('overall-configuration-status', 'fail')
    sync_status = task_response.get('output', {}).get('response_body', {}).get('output', {}).get('overall-sync-status', 'fail')
    return config_status == "fail" and sync_status == "fail"


# Workers


def service_create_vll_local(task):
    service = LocalService.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    if not service.is_local():
        'For local VLL service, 1 device is expected. Received: %s' % (service.device_ids())

    response1 = vll_worker.device_create_vll_local({'inputData': {
        'id': device_1.id,
        'service_id': service.id,
        'interface_1': device_1.interface,
        'vlan_1': device_1.vlan,
        'interface_2': device_2.interface,
        'vlan_2': device_2.vlan,
        'mtu': service.mtu if service.mtu is not None else 0
    }})
    if response1['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response1},
                'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service.id]}

    return {'status': 'COMPLETED', 'output': {'response': response1},
            'logs': ['VLL instance: %s configured in uniconfig successfully' % service.id]}


def service_create_vll(task):
    service = Service.parse_from_task(task)
    return service_create_vll_local(task) if service.is_local() else service_create_vll_remote(task)


def service_delete_vll(task):
    service = ServiceDeletion.parse_from_task(task)
    return service_delete_vll_local(task) if service.is_local() else service_delete_vll_remote(task)


def service_delete_vll_dryrun(task):
    service = ServiceDeletion.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    response = service_delete_vll(task)
    if task_failed(response):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance deletion: %s configuration in uniconfig FAIL' % service.id, response=response)

    response_dryrun = dryrun_commit(device_1, device_2)

    if task_failed(response_dryrun) or uniconfig_task_failed(response_dryrun):
        return fail('VLL instance deletion: %s dryrun FAIL' % service.id,
                    response_create_vpn=response,
                    response_dryrun=response_dryrun)

    return complete('VLL instance deletion: %s dryrun SUCCESS' % service.id,
                    response_dryrun=response_dryrun)


def service_delete_vll_commit(task):
    service = ServiceDeletion.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    response = service_delete_vll(task)
    if task_failed(response):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance deletion: %s configuration in uniconfig FAIL' % service.id, response=response)

    response_commit = uniconfig_worker.commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})

    if task_failed(response_commit) or uniconfig_task_failed(response_commit):
        return fail('VLL instance deletion: %s commit FAIL' % service.id,
                    response_create_vpn=response,
                    response_commit=response_commit)

    return complete('VLL instance deletion: %s commit SUCCESS' % service.id,
                    response_commit=response_commit)


def service_create_vll_dryrun(task):
    service = Service.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]
    add_debug_info = task['inputData']['service'].get('debug', False)

    # Check interfaces exist

    ifc_response = read_interface(device_1)
    if task_failed(ifc_response):
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist' % (service.id, device_1.id, device_1.interface),
                    response=ifc_response)

    ifc_response = read_interface(device_2)
    if task_failed(ifc_response):
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist' % (service.id, device_2.id, device_2.interface),
                    response=ifc_response)

    # Configure interface #1

    ifc_put_response1 = put_interface(service, device_1)
    if task_failed(ifc_put_response1):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured' % (service.id, device_1.id, device_1.interface),
                    response=ifc_put_response1)

    ifc_policy_put_response1 = put_interface_policy(device_1)
    if ifc_policy_put_response1 is not None and task_failed(ifc_policy_put_response1):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured' % (service.id, device_1.id, device_1.interface),
                    response=ifc_policy_put_response1)

    ifc_stp_delete_response1 = disable_interface_stp(device_1)

    # Configure interface #2

    ifc_put_response2 = put_interface(service, device_2)
    if task_failed(ifc_put_response2):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured' % (service.id, device_2.id, device_2.interface),
                    response=ifc_put_response2)

    ifc_policy_put_response2 = put_interface_policy(device_2)
    if ifc_policy_put_response2 is not None and task_failed(ifc_policy_put_response2):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured' % (service.id, device_2.id, device_2.interface),
                    response=ifc_policy_put_response2)

    ifc_stp_delete_response2 = disable_interface_stp(device_2)

    # Configure service

    response = service_create_vll(task)
    if task_failed(response):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL' % service.id, response=response)

    response_dryrun = dryrun_commit(device_1, device_2)

    replace_cfg_with_oper(device_1, device_2)

    # dryrun FAIL
    if task_failed(response_dryrun) or uniconfig_task_failed(response_dryrun):
        if add_debug_info:
            return fail('VLL instance: %s dryrun FAIL' % service.id,
                        response_device1_interface=ifc_put_response1,
                        response_device1_interface_policy=ifc_policy_put_response1,
                        response_device1_stp_interface=ifc_stp_delete_response1,
                        response_device2_interface=ifc_put_response2,
                        response_device2_interface_policy=ifc_policy_put_response2,
                        response_device2_stp_interface_policy=ifc_stp_delete_response2,
                        response_create_vpn=response,
                        response_dryrun=response_dryrun)
        else:
            return fail('VLL instance: %s dryrun FAIL' % service.id,
                        response_dryrun=response_dryrun)

    if add_debug_info:
        # TODO attach journal
        return complete('VLL instance: %s dryrun SUCCESS' % service.id,
                        response_device1_interface=ifc_put_response1,
                        response_device1_interface_policy=ifc_policy_put_response1,
                        response_device1_stp_interface=ifc_stp_delete_response1,
                        response_device2_interface=ifc_put_response2,
                        response_device2_interface_policy=ifc_policy_put_response2,
                        response_device2_stp_interface_policy=ifc_stp_delete_response2,
                        response_create_vpn=response,
                        response_dryrun=response_dryrun)
    else:
        return complete('VLL instance: %s dryrun SUCCESS' % service.id,
                        response_dryrun=response_dryrun)


def service_create_vll_commit(task):
    service = Service.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]
    add_debug_info = task['inputData']['service'].get('debug', False)

    # Check interfaces exist

    ifc_response = read_interface(device_1)
    if task_failed(ifc_response):
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist' % (service.id, device_1.id, device_1.interface),
                    response=ifc_response)

    ifc_response = read_interface(device_2)
    if task_failed(ifc_response):
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist' % (service.id, device_2.id, device_2.interface),
                    response=ifc_response)

    # Reset interfaces if necessary

    if device_1.interface_reset:
        ifc_delete_response_1 = delete_interface(device_1)
        if task_failed(ifc_response):
            replace_cfg_with_oper(device_1, device_2)
            return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be reset' % (service.id, device_1.id, device_1.interface),
                        response=ifc_response)

    if device_2.interface_reset:
        ifc_delete_response_2 = delete_interface(device_2)
        if task_failed(ifc_response):
            replace_cfg_with_oper(device_1, device_2)
            return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be reset' % (service.id, device_2.id, device_2.interface),
                        response=ifc_response)

    if device_1.interface_reset or device_2.interface_reset:
        response_commit = commit(device_1, device_2)

        # Check response from commit RPC. The RPC always succeeds but the status field needs to be checked
        if task_failed(response_commit) or uniconfig_task_failed(response_commit):
            replace_cfg_with_oper(device_1, device_2)
            return fail('VLL instance: %s commit for interface reset FAIL' % service.id,
                        response_commit=response_commit)

        response_sync_from_net = sync_from_net(device_1, device_2)

        # Check response from commit RPC. The RPC always succeeds but the status field needs to be checked
        if task_failed(response_sync_from_net) or uniconfig_task_failed(response_sync_from_net):
            replace_cfg_with_oper(device_1, device_2)
            return fail('VLL instance: %s sync_from_network after interface reset FAIL' % service.id,
                        response_sync_from_net=response_sync_from_net)

    # Configure interface #1

    ifc_put_response1 = put_interface(service, device_1)
    if task_failed(ifc_put_response1):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured' % (service.id, device_1.id, device_1.interface),
                    response=ifc_put_response1)

    ifc_policy_put_response1 = put_interface_policy(device_1)
    if ifc_policy_put_response1 is not None and task_failed(ifc_policy_put_response1):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured' % (service.id, device_1.id, device_1.interface),
                    response=ifc_policy_put_response1)
    
    ifc_stp_delete_response1 = disable_interface_stp(device_1)

    # Configure interface #2

    ifc_put_response2 = put_interface(service, device_2)
    if task_failed(ifc_put_response2):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured' % (service.id, device_2.id, device_2.interface),
                    response=ifc_put_response2)

    ifc_policy_put_response2 = put_interface_policy(device_2)
    if ifc_policy_put_response2 is not None and task_failed(ifc_policy_put_response2):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured' % (service.id, device_2.id, device_2.interface),
                    response=ifc_policy_put_response2)

    ifc_stp_delete_response2 = disable_interface_stp(device_2)
    
    # TODO refactor, too much duplicate code especially commit vs commit

    # Configure service

    response = service_create_vll(task)
    if task_failed(response):
        replace_cfg_with_oper(device_1, device_2)
        return fail('VLL instance: %s configuration in uniconfig FAIL' % service.id, response=response)
    
    response_commit = commit(device_1, device_2)

    # COMMIT FAIL
    if task_failed(response_commit) or uniconfig_task_failed(response_commit):
        replace_cfg_with_oper(device_1, device_2)

        if add_debug_info:
            return fail('VLL instance: %s commit FAIL' % service.id,
                        response_device1_interface=ifc_put_response1,
                        response_device1_interface_policy=ifc_policy_put_response1,
                        response_device1_interface_reset=ifc_delete_response_1,
                        response_device1_stp_interface=ifc_stp_delete_response1,
                        response_device2_interface=ifc_put_response2,
                        response_device2_interface_policy=ifc_policy_put_response2,
                        response_device2_interface_reset=ifc_delete_response_2,
                        response_device2_stp_interface_policy=ifc_stp_delete_response2,
                        response_create_vpn=response,
                        response_commit=response_commit)
        else:
            return fail('VLL instance: %s commit FAIL' % service.id,
                        response_commit=response_commit)

    # COMMIT SUCCESS
    if add_debug_info:
        # TODO attach journal
        return complete('VLL instance: %s commit SUCCESS' % service.id,
                        response_device1_interface=ifc_put_response1,
                        response_device1_interface_policy=ifc_policy_put_response1,
                        response_device1_interface_reset=ifc_delete_response_1,
                        response_device1_stp_interface=ifc_stp_delete_response1,
                        response_device2_interface=ifc_put_response2,
                        response_device2_interface_policy=ifc_policy_put_response2,
                        response_device2_interface_reset=ifc_delete_response_2,
                        response_device2_stp_interface_policy=ifc_stp_delete_response2,
                        response_create_vpn=response,
                        response_commit=response_commit)
    else:
        return complete('VLL instance: %s commit SUCCESS' % service.id,
                        response_commit=response_commit)


def service_create_vll_remote(task):
    service = RemoteService.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    if service.is_local():
        raise Exception('For remote VLL service, 2 different devices are expected. Received: %s' % (service.device_ids()))

    response1 = vll_worker.device_create_vll_remote({'inputData': {
        'id': device_1.id,
        'service_id': service.id,
        'vccid': service.vccid,
        'interface': device_1.interface,
        'vlan': device_1.vlan,
        'remote_ip': device_2.remote_ip,
        'mtu': service.mtu if service.mtu is not None else 0
    }})
    if response1['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response1},
                'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service.id]}

    response2 = vll_worker.device_create_vll_remote({'inputData': {
        'id': device_2.id,
        'service_id': service.id,
        'vccid': service.vccid,
        'interface': device_2.interface,
        'vlan': device_2.vlan,
        'remote_ip': device_1.remote_ip,
        'mtu': service.mtu if service.mtu is not None else 0
    }})
    if response2['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response_1': response1,
                                               'response_2': response2},
                'logs': ['VLL instance: %s configuration in uniconfig FAIL' % service.id]}

    return {'status': 'COMPLETED', 'output': {'response_1': response1,
                                              'response_2': response2},
            'logs': ['VLL instance: %s configured in uniconfig successfully' % service.id]}


def service_delete_vll_remote(task):
    service = Service.parse_from_task(task)

    if service.is_local():
        raise Exception('For remote VLL service, 2 different devices are expected. Received: %s' % (service.device_ids()))

    response1 = remove_device_vll(service.devices[0].id, service.id)
    if response1['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response1},
                'logs': ['VLL instance: %s removal in uniconfig FAIL' % service.id]}

    response2 = remove_device_vll(service.devices[1].id, service.id)
    if response2['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response2},
                'logs': ['VLL instance: %s removal in uniconfig FAIL' % service.id]}

    return {'status': 'COMPLETED', 'output': {'response_1': response1,
                                              'response_2': response2},
            'logs': ['VLL instance: %s removed in uniconfig successfully' % service.id]}


def service_delete_vll_local(task):
    service = Service.parse_from_task(task)

    if not service.is_local():
        raise Exception('For remote VLL service, 1 device are expected. Received: %s' % service.device_ids())

    response = remove_device_vll(service.devices[0].id, service.id)
    if response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response},
                'logs': ['VLL instance: %s removal in uniconfig FAIL' % service.id]}

    return {'status': 'COMPLETED', 'output': {'response': response},
            'logs': ['VLL instance: %s removed in uniconfig successfully' % service.id]}


def remove_device_vll(device_id, service_id):
    return vll_worker.device_delete_vll({'inputData': {
        'id': device_id,
        'service_id': service_id
    }})


def service_read_all(task):
    # TODO add device filtering
    # TODO add vll-local vs vll selections
    # TODO (low prio) add service name filtering
    # TODO (low prio) add service vccid filtering

    datastore = task['inputData'].get('datastore', 'actual')
    if datastore not in ['intent', 'actual']:
        return {'status': 'FAILED', 'output': {}, 'logs': ['Unable to read uniconfig datastore: %s' % datastore]}

    response = uniconfig_worker.execute_read_uniconfig_topology_operational(task) if datastore == 'actual' \
        else uniconfig_worker.execute_read_uniconfig_topology_config(task)

    if response['status'] is not 'COMPLETED':
        return {'status': 'FAILED', 'output': {'response': response},
                                               'logs': ['Unable to read uniconfig']}

    reconciliation = task['inputData'].get('reconciliation', 'name')
    if reconciliation not in ['name', 'vccid']:
        return {'status': 'FAILED', 'output': {}, 'logs': ['Unable to reconcile with strategy: %s' % reconciliation]}

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
                local_services.append(LocalService.parse_from_openconfig_network(node_id, l2p2p))
            elif vll_type(l2p2p) == 'REMOTE':
                remote_services.append(RemoteService.parse_from_openconfig_network(node_id, l2p2p))
            else:
                # incomplete configuration or unknown flavour of l2p2p
                continue

    remote_services = aggregate_l2p2p_remote(remote_services) if reconciliation == 'name' \
        else aggregate_l2p2p_remote(remote_services, lambda service: service['vccid'])

    services = local_services + remote_services
    services = map(lambda service: service.to_dict(), services)
    return {'status': 'COMPLETED', 'output': {'services': services},
            'logs': ['VLL instances found successfully: %s' % len(services)]}


def aggregate_l2p2p_remote(remote_services, by_key=lambda remote_service: remote_service.id):
    remote_services.sort(key=by_key)
    grouped_by_name = itertools.groupby(remote_services, by_key)
    grouped_by_name_as_list = map(lambda g: list(g[1]), grouped_by_name)
    remote_services_aggregated = map(lambda l: reduce(lambda l1, l2: l1.merge(l2), l), grouped_by_name_as_list)
    return remote_services_aggregated


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


def extract_network_instances(node, network_type):
    networks = node['frinx-uniconfig-topology:configuration']['frinx-openconfig-network-instance:network-instances']['network-instance']
    l2p2p = filter(lambda ni: ni['config']['type'] == network_type, networks)
    return l2p2p


def start(cc):
    print('Starting VLL service workers')

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

    # Below are higher order workers (which actually implement a workflow)

    cc.register('VLL_service_commit')
    cc.start('VLL_service_commit', service_create_vll_commit, False)

    cc.register('VLL_service_dryrun')
    cc.start('VLL_service_dryrun', service_create_vll_dryrun, False)

    cc.register('VLL_service_delete_commit')
    cc.start('VLL_service_delete_commit', service_delete_vll_commit, False)

    cc.register('VLL_service_delete_dryrun')
    cc.start('VLL_service_delete_dryrun', service_delete_vll_dryrun, False)
