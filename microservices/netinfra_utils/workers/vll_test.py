import vll_worker
import vll_model
import vll_service_worker


def test_create_snapshot():
    request = vll_worker.create_vll_remote_request(
        {"inputData": {"service_id": "abcd", "interface": "ethernet 1/2", "remote_ip": "14.14.14.14", "vccid": 194545}})
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
    device = vll_model.LocalDevice.parse({"id": "B21", "interface": "ethernet 3/4", "auto_negotiate": False}, 0)
    print(device)
    assert False


# def test_parse_service_remote():
#     service_id, vccid, devices = vll_service_worker.parse_service_vccid({"inputData": {
#         "service": {"id": "abcd", "vccid": 1234, "devices": [
#             {"id": "B21", "interface": "ethernet 3/4", "remote_ip": "100.10.10.100"},
#             {"id": "B28", "interface": "ethernet 3/5", "remote_ip": "100.10.10.101"}
#         ]}}})
#     assert service_id is "abcd"
#     assert vccid is 1234
#     assert len(devices) is 2
#
#     device = vll_worker.parse_device_remote(devices, 0)
#     assert device[0] is "B21"
#     assert device[1] is "ethernet 3/4"
#     assert device[2] is "100.10.10.100"
#
#     device = vll_worker.parse_device_remote(devices, 1)
#     assert device[0] is "B28"
#     assert device[1] is "ethernet 3/5"
#     assert device[2] is "100.10.10.101"


def test_aggregate_remote_l2p2p():
    partial_services = [{'id': 'abcd', 'vccid': 1254, 'devices': [{'id': 'B21', 'interface': 'e 1/3'}]},
          {'id': 'abcd', 'vccid': 1255, 'devices': [{'id': 'B28', 'interface': 'e 3/3'}]},
          {'id': 'abcd2', 'vccid': 1255, 'devices': [{'id': 'B29', 'interface': 'e 2/3'}]}]

    aggregated = vll_service_worker.aggregate_l2p2p_remote(partial_services)
    print(aggregated)
    assert len(aggregated) is 2

    aggregated = vll_service_worker.aggregate_l2p2p_remote(partial_services, lambda x: x['vccid'])
    print(aggregated)
    assert len(aggregated) is 2

    aggregated = vll_service_worker.aggregate_l2p2p_remote(partial_services, lambda x: x)
    print(aggregated)
    assert len(aggregated) is 3