from __future__ import print_function

import itertools
from string import Template
from vll_model import Device, Service, LocalService, RemoteService, ServiceDeletion
import uniconfig_worker
import vll_worker
import common_worker

odl_url_uniconfig_ifc_config = '/frinx-openconfig-interfaces:interfaces/interface=escape($ifc)'
odl_url_uniconfig_ifc_policy_config = '/frinx-openconfig-network-instance:network-instances/network-instance=default/policy-forwarding/interfaces/interface=escape($ifc)'
odl_url_uniconfig_ifc_stp_config = '/frinx-stp:stp/interfaces/interface=escape($ifc)'


def default_filter_strategy():
    return common_worker.default_filter_strategy('frinx-openconfig-network-instance-types:L2P2P')


def name_filter_strategy(name):
    return common_worker.name_filter_strategy('frinx-openconfig-network-instance-types:L2P2P', name)


def vccid_filter_strategy(vccid):
    return common_worker.vccid_filter_strategy('frinx-openconfig-network-instance-types:L2P2P', vccid)


# Interface updates


def read_interface(device):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_response = uniconfig_worker.read_structured_data({'inputData': {
        'device_id': device.id,
        'uri': url,
    }})
    return ifc_response


def delete_interface(device):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'device_id': device.id,
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
        ifc_config['frinx-openconfig-interfaces:interface'][0]['config']["frinx-openconfig-vlan:tpid"] = Device.switch_tpid.get(device.tpid)

    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'device_id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


# def put_interface(device, interface, description, auto_negotiate=True):
def put_minimal_interface(device):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_config = {
        "frinx-openconfig-interfaces:interface": [
            {
                "name": device.interface,
                "config": {
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "name": device.interface
                }
            }
        ]
    }

    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'device_id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def read_interface_policy(device):
    url = Template(odl_url_uniconfig_ifc_policy_config).substitute({'ifc': device.interface})
    ifc_response = uniconfig_worker.read_structured_data({'inputData': {
        'device_id': device.id,
        'uri': url,
    }})
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
        'device_id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def delete_interface_policy(device):
    if device.in_policy is None and device.out_policy is None:
        return

    url = Template(odl_url_uniconfig_ifc_policy_config).substitute({'ifc': device.interface})
    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'device_id': device.id,
        'uri': url
    }})
    return ifc_response


def disable_interface_stp(device):
    url = Template(odl_url_uniconfig_ifc_stp_config).substitute({'ifc': device.interface})

    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'device_id': device.id,
        'uri': url
    }})
    return ifc_response


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
    if common_worker.task_failed(response1):
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL' % service.id, response=response1)

    return common_worker.complete('VLL instance: %s configured in uniconfig successfully' % service.id, response=response1)


def service_create_vll(task):
    service = Service.parse_from_task(task)
    return service_create_vll_local(task) if service.is_local() else service_create_vll_remote(task)


def service_delete_vll(task):
    service = ServiceDeletion.parse_from_task(task)
    return service_delete_vll_local(task) if service.is_local() else service_delete_vll_remote(task)


def service_delete_vll_dryrun(task):
    return service_delete_vll_task(task, 'dry-run')


def service_delete_vll_commit(task):
    return service_delete_vll_task(task, 'commit')


def service_delete_vll_task(task, commit_type):
    dryrun = bool("dry-run" == commit_type)
    add_debug_info = task['inputData']['service'].get('debug', False)

    service_id = task['inputData']['service']['id']
    services = service_read_all({'inputData': {
        'datastore': 'actual',
        'reconciliation': 'name',
        'name': service_id
    }})
    number_of_services = len(services['output']['services'])
    if number_of_services < 1:
        return common_worker.fail("VLL instance: %s does not exists" % service_id)
    if number_of_services > 1:
        return common_worker.fail("VLL instance: %s is not unique. It occurs %s times." % (service_id, number_of_services))

    service = Service(services['output']['services'][0])
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    response = service_delete_vll({'inputData': {
        'service': service.to_dict()
    }})
    if common_worker.task_failed(response):
        common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
        return common_worker.fail('VLL instance deletion: %s configuration in uniconfig FAIL' % service.id, response=response)

    if dryrun:
        response_dryrun = common_worker.dryrun_commit([device_1.id, device_2.id])
        return common_worker.dryrun_response('VLL instance deletion: %s dryrun FAIL' % service.id, add_debug_info,
                                             response_create_vpn=response,
                                             response_dryrun=response_dryrun)

    response_commit = common_worker.commit([device_1.id, device_2.id])
    return common_worker.commit_response([device_1.id, device_2.id], 'VLL instance deletion: %s commit FAIL' % service.id, add_debug_info,
                                         response_create_vpn=response,
                                         response_commit=response_commit)


def service_create_vll_dryrun(task):
    return service_create_vll_task(task, 'dry-run')


def service_create_vll_commit(task):
    return service_create_vll_task(task, 'commit')


def service_create_vll_task(task, commit_type):
    dryrun = bool("dry-run" == commit_type)
    add_debug_info = task['inputData']['service'].get('debug', False)
    service = Service.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    # Check interfaces exist

    ifc_response = read_interface(device_1)
    if common_worker.task_failed(ifc_response):
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                  % (service.id, device_1.id, device_1.interface),
                                  response=ifc_response)

    ifc_response = read_interface(device_2)
    if common_worker.task_failed(ifc_response):
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                  % (service.id, device_2.id, device_2.interface),
                                  response=ifc_response)

    # Reset interfaces if necessary

    ifc_delete_policy_response_1 = ''
    ifc_delete_response_1 = ''
    if not dryrun and device_1.interface_reset:
        policy_1 = read_interface_policy(device_1)
        if not common_worker.task_failed(policy_1):
            ifc_delete_policy_response_1 = delete_interface_policy(device_1)
            if ifc_delete_policy_response_1 is not None and common_worker.task_failed(ifc_delete_policy_response_1):
                common_worker.replace_cfg_with_oper([device_1.id])
                return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policy %s cannot be reset'
                                          % (service.id, device_1.id, device_1.interface),
                                          response=ifc_delete_policy_response_1)

        ifc_delete_response_1 = delete_interface(device_1)
        if common_worker.task_failed(ifc_delete_response_1):
            common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
            return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be reset'
                                      % (service.id, device_1.id, device_1.interface),
                                      response=ifc_delete_response_1)

    ifc_delete_policy_response_2 = ''
    ifc_delete_response_2 = ''
    if not dryrun and device_2.interface_reset:
        policy_2 = read_interface_policy(device_2)
        if not common_worker.task_failed(policy_2):
            ifc_delete_policy_response_2 = delete_interface_policy(device_2)
            if ifc_delete_policy_response_2 is not None and common_worker.task_failed(ifc_delete_policy_response_2):
                common_worker.replace_cfg_with_oper([device_2.id])
                return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policy %s cannot be reset'
                                          % (service.id, device_2.id, device_2.interface),
                                          response=ifc_delete_policy_response_2)

        ifc_delete_response_2 = delete_interface(device_2)
        if common_worker.task_failed(ifc_delete_response_2):
            common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
            return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be reset'
                                      % (service.id, device_2.id, device_2.interface),
                                      response=ifc_delete_response_2)

    if not dryrun and (device_1.interface_reset or device_2.interface_reset):
        response_commit = common_worker.commit([device_1.id, device_2.id])

        # Check response from commit RPC. The RPC always succeeds but the status field needs to be checked
        if common_worker.task_failed(response_commit) or common_worker.uniconfig_task_failed(response_commit):
            common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
            return common_worker.fail('VLL instance: %s commit for interface reset FAIL' % service.id,
                                      response_commit=response_commit)

        response_sync_from_net = common_worker.sync_from_net([device_1.id, device_2.id])

        # Check response from commit RPC. The RPC always succeeds but the status field needs to be checked
        if common_worker.task_failed(response_sync_from_net) or common_worker.uniconfig_task_failed(response_sync_from_net):
            common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
            return common_worker.fail('VLL instance: %s sync_from_network after interface reset FAIL' % service.id,
                                      response_sync_from_net=response_sync_from_net)

    # Configure interface #1

    ifc_put_response1 = put_interface(service, device_1)
    if common_worker.task_failed(ifc_put_response1):
        common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured' % (service.id, device_1.id, device_1.interface),
                                  response=ifc_put_response1)

    ifc_policy_put_response1 = put_interface_policy(device_1)
    if ifc_policy_put_response1 is not None and common_worker.task_failed(ifc_policy_put_response1):
        common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured' % (service.id, device_1.id, device_1.interface),
                                  response=ifc_policy_put_response1)

    ifc_stp_delete_response1 = disable_interface_stp(device_1)

    # Configure interface #2

    ifc_put_response2 = put_interface(service, device_2)
    if common_worker.task_failed(ifc_put_response2):
        common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured' % (service.id, device_2.id, device_2.interface),
                                  response=ifc_put_response2)

    ifc_policy_put_response2 = put_interface_policy(device_2)
    if ifc_policy_put_response2 is not None and common_worker.task_failed(ifc_policy_put_response2):
        common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured' % (service.id, device_2.id, device_2.interface),
                                  response=ifc_policy_put_response2)

    ifc_stp_delete_response2 = disable_interface_stp(device_2)

    # Configure service

    response = service_create_vll(task)
    if common_worker.task_failed(response):
        common_worker.replace_cfg_with_oper([device_1.id, device_2.id])
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL' % service.id, response=response)

    if dryrun:
        response_dryrun = common_worker.dryrun_commit([device_1.id, device_2.id])
        return common_worker.dryrun_response('VLL instance: %s dryrun FAIL' % service.id, add_debug_info,
                                             response_device1_interface=ifc_put_response1,
                                             response_device1_interface_policy=ifc_policy_put_response1,
                                             response_device1_stp_interface=ifc_stp_delete_response1,
                                             response_device2_interface=ifc_put_response2,
                                             response_device2_interface_policy=ifc_policy_put_response2,
                                             response_device2_stp_interface_policy=ifc_stp_delete_response2,
                                             response_create_vpn=response,
                                             response_dryrun=response_dryrun)

    response_commit = common_worker.commit([device_1.id, device_2.id])
    return common_worker.commit_response([device_1.id, device_2.id], 'VLL instance: %s commit FAIL' % service.id, add_debug_info,
                                         response_device1_interface_reset=ifc_delete_response_1,
                                         response_device1_interface_policy_delete=ifc_delete_policy_response_1,
                                         response_device1_interface=ifc_put_response1,
                                         response_device1_interface_policy=ifc_policy_put_response1,
                                         response_device1_stp_interface=ifc_stp_delete_response1,
                                         response_device2_interface_reset=ifc_delete_response_2,
                                         response_device2_interface_policy_delete=ifc_delete_policy_response_2,
                                         response_device2_interface=ifc_put_response2,
                                         response_device2_interface_policy=ifc_policy_put_response2,
                                         response_device2_stp_interface_policy=ifc_stp_delete_response2,
                                         response_create_vpn=response,
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
    if common_worker.task_failed(response1):
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL' % service.id, response=response1)

    response2 = vll_worker.device_create_vll_remote({'inputData': {
        'id': device_2.id,
        'service_id': service.id,
        'vccid': service.vccid,
        'interface': device_2.interface,
        'vlan': device_2.vlan,
        'remote_ip': device_1.remote_ip,
        'mtu': service.mtu if service.mtu is not None else 0
    }})
    if common_worker.task_failed(response2):
        return common_worker.fail('VLL instance: %s configuration in uniconfig FAIL' % service.id, response1=response1, response2=response2)

    return common_worker.complete('VLL instance: %s configured in uniconfig successfully' % service.id, response1=response1, response2=response2)


def service_delete_vll_remote(task):
    service = Service.parse_from_task(task)

    if service.is_local():
        raise Exception('For remote VLL service, 2 different devices are expected. Received: %s' % (service.device_ids()))

    response1 = remove_device_vll(service.devices[0].id, service.id)
    if common_worker.task_failed(response1):
        return common_worker.fail('VLL instance: %s removal in uniconfig FAIL' % service.id, response=response1)

    response2 = remove_device_vll(service.devices[1].id, service.id)
    if common_worker.task_failed(response2):
        return common_worker.fail('VLL instance: %s removal in uniconfig FAIL' % service.id, response=response2)

    return common_worker.complete('VLL instance: %s removed in uniconfig successfully' % service.id, response1=response1, response2=response2)


def service_delete_vll_local(task):
    service = Service.parse_from_task(task)

    if not service.is_local():
        raise Exception('For remote VLL service, 1 device are expected. Received: %s' % service.device_ids())

    response = remove_device_vll(service.devices[0].id, service.id)
    if common_worker.task_failed(response):
        return common_worker.fail('VLL instance: %s removal in uniconfig FAIL' % service.id, response=response)

    return common_worker.complete('VLL instance: %s removed in uniconfig successfully' % service.id, response=response)


def remove_device_vll(device_id, service_id):
    return vll_worker.device_delete_vll({'inputData': {
        'id': device_id,
        'service_id': service_id
    }})


def service_read_all(task):
    # TODO add vll-local vs vll selections

    datastore = task['inputData'].get('datastore', 'actual')
    strategy, reconciliation = get_filter_strategy(task)
    if datastore not in ['intent', 'actual']:
        return common_worker.fail('Unable to read uniconfig datastore: %s' % datastore)

    response = uniconfig_worker.execute_read_uniconfig_topology_operational(task) if datastore == 'actual' \
        else uniconfig_worker.execute_read_uniconfig_topology_config(task)

    if common_worker.task_failed(response):
        return common_worker.fail('Unable to read uniconfig', response=response)

    if reconciliation not in ['name', 'vccid']:
        return common_worker.fail('Unable to reconcile with strategy: %s' % reconciliation)

    if 'node' not in response['output']['response_body']['topology'][0]:
        raise Exception("Uniconfig topology is empty.")

    uniconfig_nodes = response['output']['response_body']['topology'][0]['node']

    node_2_l2p2p = map(
        lambda n: (n['node-id'], extract_network_instances(n, strategy)),
        uniconfig_nodes)

    local_services = []
    remote_services = []
    for node in node_2_l2p2p:

        node_id = node[0]
        l2p2ps = node[1][0]
        default_ni = node[1][1]
        ifcs = node[1][2]
        if len(l2p2ps) is 0:
            continue

        for l2p2p in l2p2ps:
            if vll_type(l2p2p) == 'LOCAL':
                local_services.append(LocalService.parse_from_openconfig_network(node_id, l2p2p, default_ni, ifcs))
            elif vll_type(l2p2p) == 'REMOTE':
                remote_services.append(RemoteService.parse_from_openconfig_network(node_id, l2p2p, default_ni, ifcs))
            else:
                # incomplete configuration or unknown flavour of l2p2p
                continue

    remote_services = aggregate_l2p2p_remote(remote_services) if reconciliation == 'name' \
        else aggregate_l2p2p_remote(remote_services, lambda service: service.vccid)

    services = local_services + remote_services
    services = map(lambda service: service.to_dict(), services)
    return common_worker.complete('VLL instances found successfully: %s' % len(services), services=services)


def get_filter_strategy(task):
    reconciliation = task['inputData'].get('reconciliation', 'name')
    filter_by = task['inputData'].get(reconciliation, '')
    strategy = default_filter_strategy() if filter_by == '' \
        else (name_filter_strategy(filter_by) if reconciliation == 'name' else vccid_filter_strategy(filter_by))
    return strategy, reconciliation


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


def extract_network_instances(node, strategy):
    networks = node['frinx-uniconfig-topology:configuration']['frinx-openconfig-network-instance:network-instances']['network-instance']
    l2p2p = filter(strategy, networks)
    default_ni = filter(lambda ni: ni['name'] == 'default', networks)[0]
    interfaces = filter(lambda i: i['config']['type'] == 'iana-if-type:ethernetCsmacd', node['frinx-uniconfig-topology:configuration']['frinx-openconfig-interfaces:interfaces']['interface'])
    return l2p2p, default_ni, interfaces


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
