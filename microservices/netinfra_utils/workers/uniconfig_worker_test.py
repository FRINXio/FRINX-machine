import json

import uniconfig_worker


def test_create_snapshot():
    request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": "IOS1"}})
    print(request)
    assert request["input"]["name"] == "abcd"
    assert request["input"]["target-nodes"]["node"] == ["IOS1"]

    request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": ", IOS1, IOS2  ,"}})
    print(request)
    assert request["input"]["name"] == "abcd"
    assert request["input"]["target-nodes"]["node"] == ["IOS1", "IOS2"]
    assert "{\"input\": {\"name\": \"abcd\", \"target-nodes\": {\"node\": [\"IOS1\", \"IOS2\"]}}}" == json.dumps(request)


def test_create_snapshot_no_devices():
    try:
        request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": ""}})
    except Exception:
        return
    assert False, "Calling RPC with empty device list is not allowed"


def test_escape():
    uri = uniconfig_worker.apply_functions("interfaces/interface/escape(GigabitEthernet0/0/0/0)/abcd/escape(a/b)")
    print uri
    assert uri == "interfaces/interface/GigabitEthernet0%2F0%2F0%2F0/abcd/a%2Fb"
    uri = uniconfig_worker.apply_functions(None)
    assert uri is None
    uri = uniconfig_worker.apply_functions("")
    assert uri is ""
