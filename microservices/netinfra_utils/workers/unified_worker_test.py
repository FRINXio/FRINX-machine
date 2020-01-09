import json
from unittest.mock import patch
import unittest

import unified_worker
from frinx_rest import odl_url_base


class MockResponse:
    def __init__(self, content, status_code):
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.content


xr5_unified_response = {
    "topology": [
        {
            "topology-id": "unified",
            "node": [
                {
                    "node-id": "xr5",
                    "supporting-node": [
                        {}
                    ],
                    "unified-topology:connection-status": "connected",
                    "unified-topology:available-capabilities": {}
                }
            ]
        }
    ]
}
interface_response = {
    "frinx-openconfig-interfaces:interfaces": {
        "interface": [
            {
                "config": {
                    "enabled": "false",
                    "type": "iana-if-type:ethernetCsmacd",
                    "name": "GigabitEthernet0/0/0/0"
                },
                "name": "GigabitEthernet0/0/0/0"
            },
            {
                "config": {
                    "enabled": "false",
                    "type": "iana-if-type:ethernetCsmacd",
                    "name": "GigabitEthernet0/0/0/1"
                },
                "name": "GigabitEthernet0/0/0/1"
            },
            {
                "config": {
                    "enabled": "false",
                    "type": "iana-if-type:ethernetCsmacd",
                    "name": "GigabitEthernet0/0/0/2"
                },
                "name": "GigabitEthernet0/0/0/2"
            }
        ]
    }
}
bad_request_response = {
    "errors": {
        "error": [
            {
                "error-type": "protocol",
                "error-tag": "data-missing",
                "error-message": "Request could not be completed because the relevant data model content does not exist"
            }
        ]
    }
}
bad_input_response = {
    "errors": {
        "error": [
            {
                "error-type": "protocol",
                "error-message": "Error parsing input: com.google.common.util.concurrent.UncheckedExecutionException: java.lang.IllegalStateException: Schema node with name prefix was not found under (http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config.",
                "error-tag": "malformed-message",
                "error-info": "com.google.common.util.concurrent.UncheckedExecutionException: java.lang.IllegalStateException: Schema node with name prefix was not found under (http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config."
            }
        ]
    }
}


class TestExecuteReadUnifiedTopologyOperational(unittest.TestCase):
    def test_execute_read_unified_topology_operational_no_device(self):
        with patch('unified_worker.read_all_devices') as mock:
            mock.return_value = 200, xr5_unified_response
            request = unified_worker.execute_read_unified_topology_operational({})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=unified?content=nonconfig")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "unified")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0]["node-id"], "xr5")


class TestGetAllDevicesAsDynamicForkTasks(unittest.TestCase):
    def test_get_all_devices_as_dynamic_fork_tasks(self):
        with patch('unified_worker.read_all_devices') as mock:
            mock.return_value = 200, xr5_unified_response
            request = unified_worker.get_all_devices_as_dynamic_fork_tasks(
                {"inputData": {"task": "Create_loopback_interface_uniconfig",
                               "task_params": "{\"loopback_id\": \"${workflow.input.loopback_id}\"}"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["dynamic_tasks_i"]["xr5"]["loopback_id"], "${workflow.input.loopback_id}")
            self.assertEqual(request["output"]["dynamic_tasks_i"]["xr5"]["device_id"], "xr5")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["name"], "sub_task")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["taskReferenceName"], "xr5")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["type"], "SUB_WORKFLOW")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["subWorkflowParam"]["name"],
                             "Create_loopback_interface_uniconfig")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["subWorkflowParam"]["version"], 1)


class TestReadStructuredData(unittest.TestCase):
    def test_read_structured_data_with_device(self):
        with patch('unified_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(interface_response), encoding='utf-8'), 200)
            request = unified_worker.read_structured_data(
                {"inputData": {"device_id": "xr5", "uri": "/frinx-openconfig-interfaces:interfaces"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"],
                             odl_url_base + "/data/network-topology:network-topology/topology=unified/node=xr5/"
                                            "yang-ext:mount/frinx-openconfig-interfaces:interfaces?content=config")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"]["interface"]
                             [0]['config']['name'], "GigabitEthernet0/0/0/0")
            self.assertEqual(request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"]["interface"]
                             [1]['config']['name'], "GigabitEthernet0/0/0/1")
            self.assertEqual(request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"]["interface"]
                             [2]['config']['name'], "GigabitEthernet0/0/0/2")

    def test_read_structured_data_no_device(self):
        with patch('unified_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_request_response), encoding='utf-8'), 404)
            request = unified_worker.read_structured_data(
                {"inputData": {"device_id": "", "uri": "/frinx-openconfig-interfaces:interfaces"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Request could not be completed because the relevant data model content does not exist")


class TestWriteStructuredData(unittest.TestCase):
    def test_write_structured_data_with_device(self):
        with patch('unified_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 201)
            request = unified_worker.write_structured_data(
                {"inputData": {"device_id": "xr6",
                               "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                               "template": "{\"interface\":[{\"name\":\"Loopback01\","
                                           "\"config\":{"
                                           "\"type\":\"iana-if-type:softwareLoopback\","
                                           "\"enabled\":false,"
                                           "\"name\":\"Loopback01\"}}]}",
                               "params": {}}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"],
                             odl_url_base + "/data/network-topology:network-topology/topology=unified/node=xr6/"
                                            "yang-ext:mount/frinx-openconfig-interfaces:interfaces/interface=Loopback01")
            self.assertEqual(request["output"]["response_code"], 201)

    def test_write_structured_data_with_no_device(self):
        with patch('unified_worker.requests.put') as mock:
            mock.return_value = mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 404)
            request = unified_worker.write_structured_data(
                {"inputData": {"device_id": "",
                               "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                               "template": "{\"interface\":[{\"name\":\"Loopback01\","
                                           "\"config\":{"
                                           "\"type\":\"iana-if-type:softwareLoopback\","
                                           "\"enabled\":false,"
                                           "\"name\":\"Loopback01\"}}]}",
                               "params": {}}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"],
                             odl_url_base + "/data/network-topology:network-topology/topology=unified/node=/"
                                            "yang-ext:mount/frinx-openconfig-interfaces:interfaces/interface=Loopback01")
            self.assertEqual(request["output"]["response_code"], 404)

    def test_write_structured_data_with_bad_template(self):
        with patch('unified_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_input_response), encoding='utf-8'), 400)
            request = unified_worker.write_structured_data(
                {"inputData": {"device_id": "xr6",
                               "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                               "template": "{\"interface\":[{\"name\":\"Loopback01\","
                                           "\"config\":{"
                                           "\"type\":\"iana-if-type:softwareLoopback\","
                                           "\"enabled\":false,"
                                           "\"name\":\"Loopback01\","
                                           "\"prefix\": \"aaa\"}}]}",
                               "params": {}}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"],
                             odl_url_base + "/data/network-topology:network-topology/topology=unified/node=xr6/"
                                            "yang-ext:mount/frinx-openconfig-interfaces:interfaces/interface=Loopback01")
            self.assertEqual(request["output"]["response_code"], 400)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Error parsing input: com.google.common.util.concurrent.UncheckedExecutionException: "
                             "java.lang.IllegalStateException: Schema node with name prefix was not found under "
                             "(http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config.")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-tag"], "malformed-message")


class TestDeleteStructuredData(unittest.TestCase):
    def test_delete_structured_data_with_device(self):
        with patch('unified_worker.requests.delete') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 204)
            request = unified_worker.delete_structured_data(
                {"inputData": {"device_id": "xr6", "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})

    def test_delete_structured_data_with_bad_template(self):
        with patch('unified_worker.requests.delete') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_request_response), encoding='utf-8'), 404)
            request = unified_worker.delete_structured_data({
                "inputData": {
                    "device_id": "xr6",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                }})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Request could not be completed because the relevant data model content does not exist")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-tag"], "data-missing")


class TestExecuteCheckUnifiedNodeExists(unittest.TestCase):
    def test_execute_check_unified_node_exists_with_existing_device(self):
        with patch('unified_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({"node-id": "xr6"}), encoding='utf-8'), 200)
            request = unified_worker.execute_check_unified_node_exists(
                {"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["node-id"], "xr6")

    def test_execute_check_uniconfig_node_exists_with_non_existing_device(self):
        with patch('unified_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_request_response), encoding='utf-8'), 404)
            request = unified_worker.execute_check_unified_node_exists(
                {"inputData": {"device_id": "xr6"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Request could not be completed because the relevant data model content does not exist")


if __name__ == "__main__":
    unittest.main()
