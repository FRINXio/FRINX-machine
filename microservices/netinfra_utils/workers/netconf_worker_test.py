import json
from unittest.mock import patch
import unittest

import netconf_worker
from frinx_rest import odl_url_base

netconf_node_connecting = {
    "node": [
        {
            "node-id": "xr6",
            "netconf-node-topology:host": "192.168.1.213",
            "netconf-node-topology:connected-message": "Connecting",
            "netconf-node-topology:connection-status": "connecting",
            "netconf-node-topology:port": 830
        }
    ]
}

netconf_node_connected = {
    "node": [
        {
            "node-id": "xr6",
            "netconf-node-topology:unavailable-capabilities": {
                "unavailable-capability": []
            },
            "netconf-node-topology:available-capabilities": {
                "available-capability": []
            },
            "netconf-node-topology:host": "192.168.1.213",
            "netconf-node-topology:connected-message": "Success",
            "netconf-node-topology:connection-status": "connected",
            "netconf-node-topology:port": 830,
            "topology-node-extension:node-type-fingerprint": "1319530689"
        }
    ]
}

netconf_node_non_exist = {
    "errors": {
        "error": [
            {
                "error-message": "Request could not be completed because the relevant data model content does not exist",
                "error-tag": "data-missing",
                "error-type": "protocol"
            }
        ]
    }
}


class MockResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.content


class TestMount(unittest.TestCase):
    def test_mount_new_device(self):
        with patch('netconf_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 201)
            request = netconf_worker.execute_mount_netconf(
                {"inputData": {"device_id": "xr6", "host": "192.168.1.1", "port": "830", "keepalive-delay": "1000",
                               "tcp-only": "false", "username": "name", "password": "password"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf/node=xr6")
            self.assertEqual(request["output"]["response_code"], 201)
            self.assertEqual(request["output"]["response_body"], {})

    def test_mount_existing_device(self):
        with patch('netconf_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 204)
            request = netconf_worker.execute_mount_netconf(
                {"inputData": {"device_id": "xr6", "host": "192.168.1.1", "port": "830", "keepalive-delay": "1000",
                               "tcp-only": "false", "username": "name", "password": "password"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf/node=xr6")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})


class TestUnmount(unittest.TestCase):
    def test_unmount_existing_device(self):
        with patch('netconf_worker.requests.delete') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 204)
            request = netconf_worker.execute_unmount_netconf({"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf/node=xr6")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})


class TestCheckCliConnected(unittest.TestCase):
    def test_execute_check_connected_netconf_connecting(self):
        with patch('netconf_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(netconf_node_connecting), encoding='utf-8'), 200)
            request = netconf_worker.execute_check_connected_netconf({"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf"
                               "/node=xr6?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["node"][0]["netconf-node-topology:connection-status"],
                             "connecting")

    def test_execute_check_connected_netconf_connected(self):
        with patch('netconf_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(netconf_node_connected), encoding='utf-8'), 200)
            request = netconf_worker.execute_check_connected_netconf({"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf"
                               "/node=xr6?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["node"][0]["netconf-node-topology:connection-status"],
                             "connected")


class TestCheckNetconfIdAvailable(unittest.TestCase):
    def test_execute_check_netconf_id_available_exist(self):
        with patch('netconf_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(netconf_node_connected), encoding='utf-8'), 200)
            request = netconf_worker.execute_check_netconf_id_available({"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf/node=xr6")

    def test_execute_check_netconf_id_available_non_exist(self):
        with patch('netconf_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(netconf_node_non_exist), encoding='utf-8'), 404)
            request = netconf_worker.execute_check_netconf_id_available({"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=topology-netconf/node=xr6")


if __name__ == "__main__":
    unittest.main()
