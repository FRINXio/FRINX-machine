import vpls_worker
import vpls_model
import vpls_service_worker


def test_create_snapshot():
    request = vpls_worker.create_vpls_request(
        {"inputData": {"service_id": "abcd", "interface": [{"interface": "ethernet 1/2", "vlan": 100, "untagged": True}], "remote_ip": ["14.14.14.14"], "vccid": 194545}})
    print(request)
    assert request["network-instance"][0]["name"] == "abcd"
    assert request["network-instance"][0]["name"] == "abcd"
    assert request["network-instance"][0]["interfaces"]["interface"][0]["id"] == "ethernet 1/2"

    assert request["network-instance"][0] \
               ["connection-points"]["connection-point"][0] \
               ["endpoints"]["endpoint"][0] \
               ["local"]["config"]["interface"] == "ethernet 1/2"

    assert request["network-instance"][0] \
               ["connection-points"]["connection-point"][1] \
               ["endpoints"]["endpoint"][0] \
               ["remote"]["config"]["virtual-circuit-identifier"] == 194545

    assert request["network-instance"][0] \
               ["connection-points"]["connection-point"][1] \
               ["endpoints"]["endpoint"][0] \
               ["remote"]["config"]["remote-system"] == "14.14.14.14"


def test_parse_device():
    device = vpls_model.Device.parse({"id": "B21", "interface": "ethernet 3/4", "remote_ip": "1.1.1.1", "vlan": 100}, 0)
    print(device)
    assert True


def test_aggregate_remote_l2vsi():
    partial_services = [vpls_model.Service({'id': 'abcd', 'vccid': 1254, 'remotes': [], 'devices': [{'id': 'B21', 'interface': 'e 1/3', 'remote_ip': '1.1.1.1', 'vlan': 100}]}),
            vpls_model.Service({'id': 'abcd', 'vccid': 1255, 'remotes': [], 'devices': [{'id': 'B28', 'interface': 'e 3/3', 'remote_ip': '1.1.1.2', 'vlan': 100}]}),
            vpls_model.Service({'id': 'abcd2', 'vccid': 1255, 'remotes': [], 'devices': [{'id': 'B29', 'interface': 'e 2/3', 'remote_ip': '1.1.1.3', 'vlan': 100}]})]

    aggregated = vpls_service_worker.aggregate_l2vsi_remote(partial_services)
    print(aggregated)
    assert len(aggregated) is 2

    aggregated = vpls_service_worker.aggregate_l2vsi_remote(partial_services, lambda x: x.vccid)
    print(aggregated)
    assert len(aggregated) is 2

    aggregated = vpls_service_worker.aggregate_l2vsi_remote(partial_services, lambda x: x)
    print(aggregated)
    assert len(aggregated) is 3


def test_aggregate_remote_l2vsi_unknown_remotes():
    partial_services2 = [vpls_model.Service({'id': 'abcd', 'vccid': 1255, 'remotes': ['1.1.1.2','1.1.1.3','1.1.1.4'], 'devices': [{'id': 'B21', 'interface': 'e 1/3', 'remote_ip': 'UNKNOWN', 'vlan': 100},
                                                                                                     {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.2', 'vlan': 'UNKNOWN'},
                                                                                                     {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.3', 'vlan': 'UNKNOWN'},
                                                                                                     {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.4', 'vlan': 'UNKNOWN'}]}),
            vpls_model.Service({'id': 'abcd', 'vccid': 1255, 'remotes': ['1.1.1.1','1.1.1.3','1.1.1.4'], 'devices': [{'id': 'B28', 'interface': 'e 3/3', 'remote_ip': 'UNKNOWN', 'vlan': 100},
                                                                                        {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.1', 'vlan': 'UNKNOWN'},
                                                                                        {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.3', 'vlan': 'UNKNOWN'},
                                                                                        {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.4', 'vlan': 'UNKNOWN'}]}),
            vpls_model.Service({'id': 'abcd2', 'vccid': 1255, 'remotes': ['1.1.1.1','1.1.1.2','1.1.1.4'], 'devices': [{'id': 'B29', 'interface': 'e 2/3', 'remote_ip': 'UNKNOWN', 'vlan': 100},
                                                                                         {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.1', 'vlan': 'UNKNOWN'},
                                                                                         {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.2', 'vlan': 'UNKNOWN'},
                                                                                         {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.4', 'vlan': 'UNKNOWN'}]}),
            vpls_model.Service({'id': 'abcd2', 'vccid': 1255, 'remotes': ['1.1.1.1','1.1.1.2','1.1.1.3'], 'devices': [{'id': 'B30', 'interface': 'e 4/3', 'remote_ip': 'UNKNOWN', 'vlan': 100},
                                                                                         {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.1', 'vlan': 'UNKNOWN'},
                                                                                         {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.2', 'vlan': 'UNKNOWN'},
                                                                                         {'id': 'UNKNOWN', 'interface': 'UNKNOWN', 'remote_ip': '1.1.1.3', 'vlan': 'UNKNOWN'}]})]

    aggregated = vpls_service_worker.aggregate_l2vsi_remote(partial_services2)
    for s in aggregated:
        print(s.to_dict())
    assert len(aggregated) is 2

    aggregated = vpls_service_worker.aggregate_l2vsi_remote(partial_services2, lambda x: x.vccid)
    for s in aggregated:
        print(s.to_dict())
    assert len(aggregated) is 1
    assert len(aggregated[0].devices) is 4

    aggregated = vpls_service_worker.aggregate_l2vsi_remote(partial_services2, lambda x: x)
    print(aggregated)
    assert len(aggregated) is 4
