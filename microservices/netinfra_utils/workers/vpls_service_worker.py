from __future__ import print_function

import itertools
import urllib
from string import Template

import common_worker
import uniconfig_worker
import vpls_worker
from vpls_model import Service, RemoteService

odl_url_uniconfig_ifc_config = '/frinx-openconfig-interfaces:interfaces/interface/escape($ifc)'
odl_url_uniconfig_ifc_policy_config = '/frinx-openconfig-network-instance:network-instances/network-instance/default/policy-forwarding/interfaces/interface/escape($ifc)'
odl_url_uniconfig_ifc_stp_config = '/frinx-stp:stp/interfaces/interface/escape($ifc)'


def read_interface(device, interface):
    ifc = urllib.quote(interface, safe='')
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': ifc})
    ifc_response = uniconfig_worker.read_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return ifc_response


def delete_interface(device, interface):
    url = Template(odl_url_uniconfig_ifc_config).substitute({'ifc': interface})
    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return ifc_response


# def put_interface(device, interface, description, auto_negotiate=True):
def put_interface(service, device, interface):
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


def put_interface_policy(device, interface):
    if device.in_policy is None and device.out_policy is None:
        return

    url = Template(odl_url_uniconfig_ifc_policy_config).substitute({'ifc': interface})
    ifc_config = {
        "frinx-openconfig-network-instance:interface": [
            {
                "interface-id": interface,
                "config": {
                    "interface-id": interface
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


def disable_interface_stp(device, interface):

    url = Template(odl_url_uniconfig_ifc_stp_config).substitute({'ifc': interface})

    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'id': device.id,
        'uri': url
    }})
    return ifc_response


def service_create_vpls(task):
    service = Service.parse_from_task(task)
    # TODO check if service already exists on one of the devices, if so, fail
    # TODO add update vpls so that it finds existing service, removes it and creates a new one
    return service_create_vpls_remote(task)


def service_delete_vpls(task):
    return service_delete_vpls_remote(task)


def service_delete_vpls_dryrun(task):
    service = Service.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    response = service_delete_vpls(task)
    if common_worker.task_failed(response):
        common_worker.replace_cfg_with_oper(device_1, device_2)
        return common_worker.fail('VPLS instance deletion: %s configuration in uniconfig FAIL' % service.id, response=response)

    response_dryrun = common_worker.dryrun_commit(device_1, device_2)

    if common_worker.task_failed(response_dryrun) or common_worker.uniconfig_task_failed(response_dryrun):
        return common_worker.fail('VPLS instance deletion: %s dryrun FAIL' % service.id,
                    response_create_vpn=response,
                    response_dryrun=response_dryrun)

    return common_worker.complete('VPLS instance deletion: %s dryrun SUCCESS' % service.id,
                    response_dryrun=response_dryrun)


def service_create_vpls_dryrun(task):
    service = Service.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    dev1_ifc_responses = []
    dev1_ifc_put_responses = []
    dev1_ifc_policy_put_responses = []
    dev1_ifc_disable_stp_responses = []
    for ifc in device_1.locals:
        ifc_response = read_interface(device_1, ifc.interface)
        if common_worker.task_failed(ifc_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                                            % (service.id, device_1.id, ifc.interface), response=ifc_response)
        dev1_ifc_responses.append(ifc_response)

        ifc_put_response1 = put_interface(service, device_1, ifc.interface)
        if common_worker.task_failed(ifc_put_response1):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                                            % (service.id, device_1.id, ifc.interface), response=ifc_put_response1)
        dev1_ifc_put_responses.append(ifc_put_response1)

        ifc_policy_put_response1 = put_interface_policy(device_1, ifc.interface)
        if ifc_policy_put_response1 is not None and common_worker.task_failed(ifc_policy_put_response1):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured'
                                                            % (service.id, device_1.id, ifc.interface), response=ifc_policy_put_response1)
        if (ifc_policy_put_response1 is not None):
            dev1_ifc_policy_put_responses.append(ifc_policy_put_response1)

        ifc_stp_delete_response1 = disable_interface_stp(device_1, ifc.interface)
        # dev1_ifc_disable_stp_responses.append(ifc_stp_delete_response1)

    dev2_ifc_responses = []
    dev2_ifc_put_responses = []
    dev2_ifc_policy_put_responses = []
    dev2_ifc_disable_stp_responses = []
    for ifc in device_2.locals:
        ifc_response = read_interface(device_2, ifc.interface)
        if common_worker.task_failed(ifc_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                                            % (service.id, device_2.id, ifc.interface), response=ifc_response)
        dev2_ifc_responses.append(ifc_response)

        ifc_put_response2 = put_interface(service, device_2, ifc.interface)
        if common_worker.task_failed(ifc_put_response2):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                                            % (service.id, device_2.id, ifc.interface), response=ifc_put_response2)
        dev2_ifc_put_responses.append(ifc_put_response2)

        ifc_policy_put_response2 = put_interface_policy(device_2, ifc.interface)
        if ifc_policy_put_response2 is not None and common_worker.task_failed(ifc_policy_put_response2):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured'
                                                            % (service.id, device_2.id, ifc.interface), response=ifc_policy_put_response2)
        if (ifc_policy_put_response2 is not None):
            dev2_ifc_policy_put_responses.append(ifc_policy_put_response2)

        ifc_stp_delete_response2 = disable_interface_stp(device_2, ifc.interface)
        # dev2_ifc_disable_stp_responses.append(ifc_stp_delete_response2)

    # TODO refactor, too much duplicate code especially dryrun vs commit

    response = service_create_vpls(task)
    if common_worker.task_failed(response):
        return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL' % service.id, response=response)

    response_dryrun = uniconfig_worker.dryrun_commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})

    if common_worker.task_failed(response_dryrun):
        return common_worker.fail('VPLS instance: %s dry-run FAIL' % service.id, response=response,
                                               response_dryrun=response_dryrun)

    # Check response from dryrun RPC. The RPC always succeeds but the status field needs to be checked
    if response_dryrun.get('output', {}).get('response_body', {}).get('output', {}).get('overall-configuration-status', 'fail') == "fail":
        return common_worker.fail('VPLS instance: %s dry-run FAIL' % service.id, response_device1_interface=dev1_ifc_put_responses,
                                               response_device1_interface_policy=dev1_ifc_policy_put_responses,
                                               response_device1_stp_interface_policy=dev1_ifc_disable_stp_responses,
                                               response_device2_interface=dev2_ifc_put_responses,
                                               response_device2_interface_policy=dev2_ifc_policy_put_responses,
                                               response_device2_stp_interface_policy=dev2_ifc_disable_stp_responses,
                                               response_network_instance=response,
                                               response_dryrun=response_dryrun)

    return common_worker.complete('VPLS instance: %s dry-run successful' % service.id, response_device1_interface=dev1_ifc_put_responses,
                                              response_device1_interface_policy=dev1_ifc_policy_put_responses,
                                              response_device1_stp_interface_policy=dev1_ifc_disable_stp_responses,
                                              response_device2_interface=dev2_ifc_put_responses,
                                              response_device2_interface_policy=dev2_ifc_policy_put_responses,
                                              response_device2_stp_interface_policy=dev2_ifc_disable_stp_responses,
                                              response_network_instance=response,
                                              response_dryrun=response_dryrun)


def service_delete_vpls_commit(task):
    service = Service.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    response = service_delete_vpls(task)
    if common_worker.task_failed(response):
        common_worker.replace_cfg_with_oper(device_1, device_2)
        return common_worker.fail('VPLS instance deletion: %s configuration in uniconfig FAIL' % service.id, response=response)

    response_commit = uniconfig_worker.commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})

    if common_worker.task_failed(response_commit) or common_worker.uniconfig_task_failed(response_commit):
        return common_worker.fail('VPLS instance deletion: %s commit FAIL' % service.id,
                    response_create_vpn=response,
                    response_commit=response_commit)

    return common_worker.complete('VPLS instance deletion: %s commit SUCCESS' % service.id,
                    response_commit=response_commit)


def service_create_vpls_commit(task):
    service = RemoteService.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    for ifc in device_1.locals:
        ifc_response = read_interface(device_1, ifc.interface)
        if common_worker.task_failed(ifc_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                           % (service.id, device_1.id, ifc.interface), response_read=ifc_response)
        ifc_put_response1 = put_interface(service, device_1, ifc.interface)
        if common_worker.task_failed(ifc_put_response1):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                            % (service.id, device_1.id, ifc.interface), response_put=ifc_put_response1)
        ifc_policy_put_response1 = put_interface_policy(device_1, ifc.interface)
        if common_worker.task_failed(ifc_policy_put_response1):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured'
                                           % (service.id, device_1.id, ifc.interface), response_policy=ifc_policy_put_response1)
        ifc_stp_delete_response1 = disable_interface_stp(ifc.interface)
        if common_worker.task_failed(ifc_stp_delete_response1):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface STP %s cannot be configured'
                                           % (service.id, device_1.id, ifc.interface), response_delete_stp=ifc_stp_delete_response1)

    for ifc in device_2.locals:
        ifc_response = read_interface(device_2, ifc.interface)
        if common_worker.task_failed(ifc_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s does not exist'
                                           % (service.id, device_2.id, ifc.interface), response_read=ifc_response)
        ifc_put_response = put_interface(service, device_2, ifc.interface)
        if common_worker.task_failed(ifc_put_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                           % (service.id, device_2.id, ifc.interface), response_put=ifc_put_response)
        ifc_policy_put_response = put_interface_policy(device_2, ifc.interface)
        if common_worker.task_failed(ifc_policy_put_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured'
                                           % (service.id, device_2.id, ifc.interface), response_policy=ifc_policy_put_response)
        ifc_stp_delete_response = disable_interface_stp(ifc.interface)
        if common_worker.task_failed(ifc_stp_delete_response):
            return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL. Device: %s interface STP %s cannot be configured'
                                           % (service.id, device_2.id, ifc.interface), response_delete_stp=ifc_stp_delete_response)

    response = service_create_vpls(task)
    if common_worker.task_failed(response):
        return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL' % service.id, response_commit=response)

    response_commit = uniconfig_worker.commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})

    if common_worker.task_failed(response_commit):
        return common_worker.fail('VPLS instance: %s commit FAIL' % service.id, response=response, response_dryrun=response_commit)
        # TODO, replace config with oper here on failure, to get back to previous state ?

    return common_worker.complete('VPLS instance: %s commit successful' % service.id, response=response, response_dryrun=response_commit)


def service_create_vpls_remote(task):
    service = RemoteService.parse_from_task(task)
    device_1 = service.devices[0]
    device_2 = service.devices[1]

    assert not service.is_local(), \
        'For remote VPLS service, 2 different devices are expected. Received: %s' % (service.device_ids())

    response1 = vpls_worker.device_create_vpls_remote({'inputData': {
        'id': device_1.id,
        'service_id': service.id,
        'vccid': service.vccid,
        'interface': device_1.locals,
        'remote_ip': device_1.remotes,
        'mtu': service.mtu if service.mtu is not None else 0
    }})
    if common_worker.task_failed(response1):
        response1_delete = remove_device_vpls(device_1.id, service.id)

        return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL' % service.id, response_for_rollback=response1_delete, response=response1)

    response2 = vpls_worker.device_create_vpls_remote({'inputData': {
        'id': device_2.id,
        'service_id': service.id,
        'vccid': service.vccid,
        'interface': device_2.locals,
        'remote_ip': device_2.remotes,
        'mtu': service.mtu if service.mtu is not None else 0
    }})
    if common_worker.task_failed(response2):
        response1_delete = remove_device_vpls(device_1.id, service.id)
        response2_delete = remove_device_vpls(device_2.id, service.id)

        return common_worker.fail('VPLS instance: %s configuration in uniconfig FAIL' % service.id,
                                       response_1_for_rollback=response1_delete, response_2_for_rollback=response2_delete,
                                       response_1=response1, response_2=response2)

    return common_worker.complete('VPLS instance: %s configured in uniconfig successfully' % service.id, response_1=response1, response_2=response2)


def service_delete_vpls_remote(task):
    service = Service.parse_from_task(task)

    response1 = remove_device_vpls(service.devices[0].id, service.id)
    if common_worker.task_failed(response1):
        return common_worker.fail('VPLS instance: %s removal in uniconfig FAIL' % service.id, response=response1)

    response2 = remove_device_vpls(service.devices[1].id, service.id)
    if common_worker.task_failed(response2):
        return common_worker.fail('VPLS instance: %s removal in uniconfig FAIL' % service.id, response=response2)

    return common_worker.complete('VPLS instance: %s removed in uniconfig successfully' % service.id, response_1=response1, response_2=response2)


def remove_device_vpls(device_id, service_id):
    return vpls_worker.device_delete_vpls({'inputData': {
        'id': device_id,
        'service_id': service_id
    }})


def service_read_all(task):
    # TODO add device filtering
    # TODO (low prio) add service name filtering
    # TODO (low prio) add service vccid filtering

    datastore = task['inputData'].get('datastore', 'actual')
    if datastore not in ['intent', 'actual']:
        return common_worker.fail('Unable to read uniconfig datastore: %s' % datastore)

    response = uniconfig_worker.execute_read_uniconfig_topology_operational(task) if datastore == 'actual' \
        else uniconfig_worker.execute_read_uniconfig_topology_config(task)

    if common_worker.task_failed(response):
        return common_worker.fail('Unable to read uniconfig', response=response)
    reconciliation = task['inputData'].get('reconciliation', 'name')
    if reconciliation not in ['name', 'vccid']:
        return common_worker.fail('Unable to reconcile with strategy: %s' % reconciliation)

    uniconfig_nodes = response['output']['response_body']['topology'][0]['node']

    node_2_l2vsi = map(
        lambda n: (n['node-id'], extract_network_instances(n, 'frinx-openconfig-network-instance-types:L2VSI')),
        uniconfig_nodes)

    remote_services = []
    for node in node_2_l2vsi:

        node_id = node[0]
        l2vsis = node[1]
        if len(l2vsis) is 0:
            continue

        for l2vsi in l2vsis:
            service = RemoteService.parse_from_openconfig_network(node_id, l2vsi)
            if service is not None:
                remote_services.append(service)

    remote_services = aggregate_l2vsi_remote(remote_services) if reconciliation == 'name' \
        else aggregate_l2vsi_remote(remote_services, lambda service: service['vccid'])

    services = map(lambda service: to_dict(service), remote_services)
    return common_worker.complete('VPLS instances found successfully: %s' % len(services), services=services)


def to_dict(service):
    devs = []
    for dev in service.devices:
        aDev = vars(dev)
        locals = []
        for local in dev.locals:
            locals.append(vars(local))
        aDev['locals'] = locals

        remotes = []
        for remote in dev.remotes:
            remotes.append(vars(remote))
        aDev['remotes'] = remotes

        devs.append(aDev)

    serv = vars(service)
    serv['devices'] = devs
    return serv


def aggregate_l2vsi_remote(remote_services, by_key=lambda remote_service: remote_service.id):
    remote_services.sort(key=by_key)
    grouped_by_name = itertools.groupby(remote_services, by_key)
    grouped_by_name_as_list = map(lambda g: list(g[1]), grouped_by_name)
    remote_services_aggregated = map(lambda l: reduce(lambda l1, l2: l1.merge(l2), l), grouped_by_name_as_list)
    return remote_services_aggregated


def extract_network_instances(node, network_type):
    networks = node['frinx-uniconfig-topology:configuration']['frinx-openconfig-network-instance:network-instances']['network-instance']
    l2vsi = filter(lambda ni: ni['config']['type'] == network_type, networks)
    return l2vsi


def start(cc):
    print('Starting VPLS service workers')

    # Service level configuration (spanning multiple devices)

    cc.register('VPLS_service_create')
    cc.start('VPLS_service_create', service_create_vpls, False)

    cc.register('VPLS_service_delete')
    cc.start('VPLS_service_delete', service_delete_vpls, False)

    cc.register('VPLS_service_create_remote')
    cc.start('VPLS_service_create_remote', service_create_vpls_remote, False)

    cc.register('VPLS_service_delete_remote')
    cc.start('VPLS_service_delete_remote', service_delete_vpls_remote, False)

    # Batch reconciliation from per device info into service objects

    cc.register('VPLS_service_read_all')
    cc.start('VPLS_service_read_all', service_read_all, False)

    # Below are higher order workers (which actually implement a workflow)

    cc.register('VPLS_service_commit')
    cc.start('VPLS_service_commit', service_create_vpls_commit, False)

    cc.register('VPLS_service_dryrun')
    cc.start('VPLS_service_dryrun', service_create_vpls_dryrun, False)

    cc.register('VPLS_service_delete_commit')
    cc.start('VPLS_service_delete_commit', service_delete_vpls_commit, False)

    cc.register('VPLS_service_delete_dryrun')
    cc.start('VPLS_service_delete_dryrun', service_delete_vpls_dryrun, False)
