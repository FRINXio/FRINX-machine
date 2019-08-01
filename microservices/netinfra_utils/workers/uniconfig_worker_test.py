import json

import uniconfig_worker


def test_create_snapshot():
    request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": "IOS1"}})
    print(request)
    assert request["input"]["name"] == "abcd"
    assert request["input"]["target-nodes"]["node"] == ["IOS1"]

    request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": ""}})
    print(request)
    assert request["input"]["name"] == "abcd"
    assert "node" not in request["input"]["target-nodes"]

    request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": ", IOS1, IOS2  ,"}})
    print(request)
    assert request["input"]["name"] == "abcd"
    assert request["input"]["target-nodes"]["node"] == ["IOS1", "IOS2"]
    assert "{\"input\": {\"name\": \"abcd\", \"target-nodes\": {\"node\": [\"IOS1\", \"IOS2\"]}}}" == json.dumps(request)
