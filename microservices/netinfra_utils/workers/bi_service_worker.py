from __future__ import print_function

from string import Template

import common_worker
import uniconfig_worker
from bi_model import Service
import vll_service_worker
from vll_model import Device

odl_url_uniconfig_vlan_config = '/frinx-openconfig-network-instance:network-instances/network-instance/default/vlans/vlan/escape($vlan)'
odl_url_uniconfig_isis_config = '/frinx-openconfig-network-instance:network-instances/network-instance/default/protocols/protocol/frinx-openconfig-policy-types:ISIS/default/isis/interfaces/interface/escape($ifc)'


# Vlan updates


def read_vlan(device):
    url = Template(odl_url_uniconfig_vlan_config).substitute({'vlan': device.vlan})
    vlan_response = uniconfig_worker.read_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return vlan_response


def delete_vlan(device):
    url = Template(odl_url_uniconfig_vlan_config).substitute({'vlan': device.vlan})
    vlan_response = uniconfig_worker.delete_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return vlan_response


def put_vlan(service, device):
    url = Template(odl_url_uniconfig_vlan_config).substitute({'vlan': device.vlan})
    vlan_config = {
        "frinx-openconfig-network-instance:vlan": [
            {
                "vlan-id": device.vlan,
                "config": {
                    "vlan-id": device.vlan,
                    "status": "ACTIVE",
                    "name": service.id
                }
            }]
    }

    vlan_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
        "template": vlan_config,
        'params': {}
    }})
    vlan_response.update({'vlan_data': vlan_config})
    return vlan_response


# Interface updates


def read_ve_interface(device):
    url = Template(vll_service_worker.odl_url_uniconfig_ifc_config).substitute({'ifc': device.ve_interface})
    ifc_response = uniconfig_worker.read_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return ifc_response


def delete_ve_interface(device):
    url = Template(vll_service_worker.odl_url_uniconfig_ifc_config).substitute({'ifc': device.ve_interface})
    ifc_response = uniconfig_worker.delete_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
    }})
    return ifc_response


def put_interface(service, device):
    url = Template(vll_service_worker.odl_url_uniconfig_ifc_config).substitute({'ifc': device.interface})
    ifc_config = {
        "frinx-openconfig-interfaces:interface": [
            {
                "name": device.interface,
                "config": {
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "name": device.interface,
                    "description": common_worker.INTERFACE_PREFIX + device.description if device.description else common_worker.INTERFACE_PREFIX_2 + service.id,
                    "frinx-brocade-if-extension:priority": common_worker.INTERFACE_PRIORITY,
                    "frinx-brocade-if-extension:priority-force": common_worker.INTERFACE_PRIORITY_FORCE

                },
                "frinx-openconfig-if-ethernet:ethernet": {
                    "frinx-openconfig-vlan:switched-vlan": {
                        "config": {
                            "interface-mode": "ACCESS" if device.untagged else "TRUNK"
                        }
                    }
                }
            }
        ]
    }

    if device.untagged:
        ifc_config["frinx-openconfig-interfaces:interface"][0]['frinx-openconfig-if-ethernet:ethernet']['frinx-openconfig-vlan:switched-vlan']['config']["access-vlan"] = device.vlan
    else:
        ifc_config["frinx-openconfig-interfaces:interface"][0]['frinx-openconfig-if-ethernet:ethernet']['frinx-openconfig-vlan:switched-vlan']['config']["trunk-vlans"] = [device.vlan]

    if device.auto_negotiate is not None:
        ifc_config['frinx-openconfig-interfaces:interface'][0].update({"frinx-openconfig-if-ethernet:ethernet": {
            "config": {
                "auto-negotiate": device.auto_negotiate
            }
        }})

    if device.tpid is not None:
        ifc_config['frinx-openconfig-interfaces:interface'][0]['config']["frinx-openconfig-vlan:tpid"] = Device.switch_tpid.get(device.tpid)

    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def put_ve_interface(service, device):
    url = Template(vll_service_worker.odl_url_uniconfig_ifc_config).substitute({'ifc': device.ve_interface})
    ifc_config = {
        "frinx-openconfig-interfaces:interface": [
            {
                "name": device.ve_interface,
                "config": {
                    "type": "iana-if-type:l3ipvlan",
                    "enabled": True,
                    "name": device.ve_interface,
                    "description": common_worker.INTERFACE_PREFIX + service.id,
                }
            }
        ]
    }

    if device.ip is not None:
        x = device.ip.split('/')
        ifc_config["frinx-openconfig-interfaces:interface"][0].update({"subinterfaces": {
            "subinterface": [
                {
                    "index": 0,
                    "config": {
                        "index": 0
                    },
                    "frinx-openconfig-if-ip:ipv4": {
                        "addresses": {
                            "address": [
                                {
                                    "ip": x[0],
                                    "config": {
                                        "prefix-length": x[1],
                                        "ip": x[0]
                                    }
                                }
                            ]
                        }
                    }
                }]
        }})

    if device.vlan is not None:
        ifc_config['frinx-openconfig-interfaces:interface'][0].update({"frinx-openconfig-vlan:routed-vlan": {
            "config": {
                "vlan": device.vlan
            }
        }})

    ifc_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
        "template": ifc_config,
        'params': {}
    }})
    ifc_response.update({'ifc_data': ifc_config})
    return ifc_response


def put_isis(device):
    url = Template(odl_url_uniconfig_isis_config).substitute({'ifc': device.ve_interface})
    isis_config = {
        "frinx-openconfig-network-instance:interface": [
            {
                "interface-id": device.ve_interface,
                "config": {
                    "interface-id": device.ve_interface,
                    "passive": common_worker.INTERFACE_ISIS_PASSIVE
                }
            }
        ]
    }

    isis_response = uniconfig_worker.write_structured_data({'inputData': {
        'id': device.id,
        'uri': url,
        "template": isis_config,
        'params': {}
    }})
    isis_response.update({'isis_data': isis_config})
    return isis_response


def service_delete_bi_commit(task):
    return service_delete_bi(task, "commit")


def service_delete_bi_dryrun(task):
    return service_delete_bi(task, "dry-run")


def service_delete_bi(task, commit_type):
    dryrun = bool("dry-run" == commit_type)
    add_debug_info = task['inputData']['service'].get('debug', False)
    service = Service.parse_from_task(task)

    device_ids = service.device_ids()
    response_del = device_delete_bi_instance(task)
    if common_worker.task_failed(response_del):
        common_worker.replace_cfg_with_oper(device_ids)
        return common_worker.fail('BI instance: %s deletion configuration in uniconfig FAIL' % service.id, response=response_del)

    if dryrun:
        response = common_worker.dryrun_commit(device_ids)
        return common_worker.dryrun_response('BI instance: %s deletion dry-run FAIL' % service.id, add_debug_info,
                                             response_delete=response_del,
                                             response_dryrun=response)
    else:
        response = common_worker.commit(device_ids)
        return common_worker.commit_response(device_ids, 'BI instance: %s deletion commit FAIL' % service.id, add_debug_info,
                                             response_delete=response_del,
                                             response_commit=response)


def service_create_bi_commit(task):
    return service_create_bi(task, "commit")


def service_create_bi_dryrun(task):
    return service_create_bi(task, "dry-run")


def service_create_bi(task, commit_type):
    dryrun = bool("dry-run" == commit_type)
    add_debug_info = task['inputData']['service'].get('debug', False)
    service = Service.parse_from_task(task)

    vlan_put_responses = []
    ve_ifc_put_responses = []
    ifc_put_responses = []
    isis_put_responses = []
    ifc_policy_put_responses = []
    for device in service.devices:

        if not dryrun and device.interface_reset:
            policy = vll_service_worker.read_interface_policy(device)
            if not common_worker.task_failed(policy):
                ifc_delete_policy = vll_service_worker.delete_interface_policy(device)
                if ifc_delete_policy is not None and common_worker.task_failed(ifc_delete_policy):
                    common_worker.replace_cfg_with_oper([device.id])
                    return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s interface policy %s cannot be reset'
                                              % (service.id, device.id, device.interface),
                                              response=ifc_delete_policy)

            ifc_delete_response = vll_service_worker.delete_interface(device)
            if common_worker.task_failed(ifc_delete_response):
                common_worker.replace_cfg_with_oper(service.device_ids())
                return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be reset'
                                          % (service.id, device.id, device.interface),
                                          response=ifc_delete_response)

            response_commit = common_worker.commit([device.id])

            # Check response from commit RPC. The RPC always succeeds but the status field needs to be checked
            if common_worker.task_failed(response_commit) or common_worker.uniconfig_task_failed(response_commit):
                common_worker.replace_cfg_with_oper(service.device_ids())
                return common_worker.fail('BI commit for device %s reset FAIL' % device.id, response_commit=response_commit)

            response_sync_from_net = common_worker.sync_from_net([device.id])

            # Check response from commit RPC. The RPC always succeeds but the status field needs to be checked
            if common_worker.task_failed(response_sync_from_net) or common_worker.uniconfig_task_failed(response_sync_from_net):
                common_worker.replace_cfg_with_oper(service.device_ids())
                return common_worker.fail('BI sync_from_network after device %s reset FAIL' % device.id,
                                          response_sync_from_net=response_sync_from_net)

        vlan_put_response = put_vlan(service, device)
        if common_worker.task_failed(vlan_put_response):
            common_worker.replace_cfg_with_oper(service.device_ids())
            return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s vlan %s cannot be configured'
                                      % (service.id, device.id, device.vlan), response=vlan_put_response)
        vlan_put_responses.append(vlan_put_response)

        ifc_put_response = put_interface(service, device)
        if common_worker.task_failed(ifc_put_response):
            common_worker.replace_cfg_with_oper(service.device_ids())
            return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                      % (service.id, device.id, device.interface), response=ifc_put_response)
        ifc_put_responses.append(ifc_put_response)

        ifc_policy_put_response = vll_service_worker.put_interface_policy(device)
        if ifc_policy_put_response is not None and common_worker.task_failed(ifc_policy_put_response):
            common_worker.replace_cfg_with_oper(service.device_ids())
            return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s interface policies %s cannot be configured'
                                      % (service.id, device.id, device.interface),
                                      response=ifc_policy_put_response)
        ifc_policy_put_responses.append(ifc_policy_put_response)

        vll_service_worker.disable_interface_stp(device)

        ve_ifc_put_response = put_ve_interface(service, device)
        if common_worker.task_failed(ve_ifc_put_response):
            common_worker.replace_cfg_with_oper(service.device_ids())
            return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s interface %s cannot be configured'
                                      % (service.id, device.id, device.ve_interface), response=ve_ifc_put_response)
        ve_ifc_put_responses.append(ve_ifc_put_response)

        isis_put_response = put_isis(device)
        if common_worker.task_failed(isis_put_response):
            common_worker.replace_cfg_with_oper(service.device_ids())
            return common_worker.fail('BI instance: %s configuration in uniconfig FAIL. Device: %s isis interface %s cannot be configured'
                                      % (service.id, device.id, device.interface), response=isis_put_response)
        isis_put_responses.append(isis_put_response)

    device_ids = service.device_ids()
    # Check response from dryrun RPC. The RPC always succeeds but the status field needs to be checked
    if dryrun:
        response = common_worker.dryrun_commit(device_ids)
        return common_worker.dryrun_response('BI instance: %s dry-run FAIL' % service.id, add_debug_info,
                                             response_interface=ifc_put_responses,
                                             response_ifc_policy=ifc_policy_put_responses,
                                             response_ve_interface=ve_ifc_put_responses,
                                             response_interface_isis=isis_put_responses,
                                             response_vlans=vlan_put_responses,
                                             response_dryrun=response)
    else:
        response = common_worker.commit(device_ids)
        return common_worker.commit_response(device_ids, 'BI instance: %s commit FAIL' % service.id, add_debug_info,
                                             response_interface=ifc_put_responses,
                                             response_ifc_policy=ifc_policy_put_responses,
                                             response_ve_interface=ve_ifc_put_responses,
                                             response_interface_isis=isis_put_responses,
                                             response_vlans=vlan_put_responses,
                                             response_commit=response)


def device_delete_bi_instance(task):
    service = Service.parse_from_task(task)

    ifc_responses = []
    ve_ifc_responses = []
    vlan_responses = []
    for device in service.devices:
        response = delete_ve_interface(device)
        if common_worker.task_failed(response):
            return common_worker.fail('BI interface %s removal in uniconfig FAIL' % device.ve_interface, response=response)
        ve_ifc_responses.append(response)

        if device.interface_reset:
            response = vll_service_worker.put_minimal_interface(device)
            if common_worker.task_failed(response):
                return common_worker.fail('BI interface %s removal in uniconfig FAIL' % device.interface, response=response)
            ifc_responses.append(response)
        else:
            response = vll_service_worker.delete_interface(device)
            if common_worker.task_failed(response):
                return common_worker.fail('BI interface %s removal in uniconfig FAIL' % device.interface, response=response)
            ifc_responses.append(response)

        response = delete_vlan(device)
        if common_worker.task_failed(response):
            return common_worker.fail('BI vlan %s removal in uniconfig FAIL' % device.vlan, response=response)
        vlan_responses.append(response)

    return common_worker.complete('BI instance: %s removed in uniconfig successfully' % service.id,
                                  ifc_response=ifc_responses,
                                  ve_ifc_response=ve_ifc_responses,
                                  vlan_response=vlan_responses)


def service_read_all(task):
    datastore = task['inputData'].get('datastore', 'actual')
    if datastore not in ['intent', 'actual']:
        return common_worker.fail('Unable to read uniconfig datastore: %s' % datastore)

    response = uniconfig_worker.execute_read_uniconfig_topology_operational(task) if datastore == 'actual' \
        else uniconfig_worker.execute_read_uniconfig_topology_config(task)

    if common_worker.task_failed(response):
        return common_worker.fail('Unable to read uniconfig', response=response)

    if 'node' not in response['output']['response_body']['topology'][0]:
        raise Exception("Uniconfig topology is empty.")

    uniconfig_nodes = response['output']['response_body']['topology'][0]['node']

    devices = []
    for node in map(lambda n: (n['node-id'], extract_network_instances(n)), uniconfig_nodes):

        node_id = node[0]
        bis = node[1]
        dev = Service.parse_from_openconfig_network(node_id, bis[0], bis[1], bis[2])
        if dev is not None:
            devices.extend(dev)

    device_final = [dev.to_dict() for dev in devices]
    return common_worker.complete('BI instances found successfully', services=device_final)


def extract_network_instances(node):
    networks = node['frinx-uniconfig-topology:configuration']['frinx-openconfig-network-instance:network-instances']['network-instance']
    ni = filter(lambda ni: ni['name'] == 'default', networks)[0]
    interfaces = node['frinx-uniconfig-topology:configuration']['frinx-openconfig-interfaces:interfaces']['interface']
    ve_ifcs = filter(lambda ifc: ifc['config']['type'] == 'iana-if-type:l3ipvlan', interfaces)
    ph_ifcs = filter(lambda ifc: ifc['config']['type'] == 'iana-if-type:ethernetCsmacd', interfaces)
    return ni, ph_ifcs, ve_ifcs


def start(cc):
    print('Starting bi service workers')

    cc.register('bi_service_delete')
    cc.start('bi_service_delete', device_delete_bi_instance, False)

    cc.register('bi_service_read_all')
    cc.start('bi_service_read_all', service_read_all, False)

    # Below are higher order workers (which actually implement a workflow)

    cc.register('bi_service_commit')
    cc.start('bi_service_commit', service_create_bi_commit, False)

    cc.register('bi_service_dryrun')
    cc.start('bi_service_dryrun', service_create_bi_dryrun, False)

    cc.register('bi_service_delete_commit')
    cc.start('bi_service_delete_commit', service_delete_bi_commit, False)

    cc.register('bi_service_delete_dryrun')
    cc.start('bi_service_delete_dryrun', service_delete_bi_dryrun, False)
