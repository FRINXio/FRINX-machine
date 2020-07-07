#!/usr/bin/env/python3
import json
from http.cookies import SimpleCookie
from unittest.mock import patch
import unittest

import uniconfig_worker
from frinx_rest import odl_url_base

xr5_response = {
    'topology': [{
        'node': [{
            "node-id": "xr5"
        }],
        'topology-id': 'uniconfig',
        'topology-types': {
            'frinx-uniconfig-topology:uniconfig': {}
        }
    }]
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
commit_output = {
    "output": {
        "overall-status": "complete",
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "configuration-status": "complete"
                },
                {
                    "node-id": "xr6",
                    "configuration-status": "complete"
                }
            ]
        }
    }
}
dry_run_output = {
    "output": {
        "overall-status": "complete",
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "configuration": "2019-09-13T08:37:28.331: configure terminal\n2019-09-13T08:37:28.536: interface GigabitEthernet0/0/0/1\nshutdown\nroot\n\n2019-09-13T08:37:28.536: commit\n2019-09-13T08:37:28.536: end\n",
                    "configuration-status": "complete"
                }
            ]
        }
    }
}
calculate_diff_output = {
    "output": {
        "overall-status": "complete",
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "updated-data": [
                        {
                            "path": "network-topology:network-topology/topology=uniconfig/node=xr5/frinx-uniconfig-topology:configuration/frinx-openconfig-interfaces:interfaces/interface=GigabitEthernet0%2F0%2F0%2F0/config",
                            "data-actual": "{\n  \"frinx-openconfig-interfaces:config\": {\n    \"type\": \"iana-if-type:ethernetCsmacd\",\n    \"enabled\": false,\n    \"name\": \"GigabitEthernet0/0/0/0\"\n  }\n}",
                            "data-intended": "{\n  \"frinx-openconfig-interfaces:config\": {\n    \"type\": \"iana-if-type:ethernetCsmacd\",\n    \"enabled\": false,\n    \"name\": \"GigabitEthernet0/0/0/0dfhdfghd\"\n  }\n}"
                        }
                    ],
                    "status": "complete"
                }
            ]
        }
    }
}
RPC_output_multiple_devices = {
    "output": {
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "status": "complete"
                },
                {
                    "node-id": "xr6",
                    "status": "complete"
                }
            ]
        },
        "overall-status": "complete"
    }
}
RPC_output_one_device = {
    "output": {
        "node-results": {
            "node-result": [
                {
                    "node-id": "xr5",
                    "status": "complete"
                }
            ]
        },
        "overall-status": "complete"
    }
}


class MockResponse:
    def __init__(self, content, status_code, cookies):
        self.content = content
        self.status_code = status_code
        self.cookies = cookies

    def json(self):
        return self.content


class TestExecuteReadUniconfigTopologyOperational(unittest.TestCase):
    def test_execute_read_uniconfig_topology_operational_no_device(self):
        with patch('uniconfig_worker.read_all_devices') as mock:
            mock.return_value = 200, xr5_response
            request = uniconfig_worker.execute_read_uniconfig_topology_operational({"inputData": {"devices": ""}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=uniconfig?content=nonconfig")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "uniconfig")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0]["node-id"], "xr5")

    def test_execute_read_uniconfig_topology_operational_one_device(self):
        with patch('uniconfig_worker.read_selected_devices') as mock:
            mock.return_value = 200, xr5_response
            request = uniconfig_worker.execute_read_uniconfig_topology_operational({"inputData": {"devices": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=uniconfig?content=nonconfig")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "uniconfig")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0]["node-id"], "xr5")


class TestExecuteReadUniconfigTopologyConfig(unittest.TestCase):
    def test_execute_read_uniconfig_topology_config_no_device(self):
        with patch('uniconfig_worker.read_all_devices') as mock:
            mock.return_value = 200, xr5_response
            request = uniconfig_worker.execute_read_uniconfig_topology_config({"inputData": {"devices": ""}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=uniconfig?content=config")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "uniconfig")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0]["node-id"], "xr5")

    def test_execute_read_uniconfig_topology_config_one_device(self):
        with patch('uniconfig_worker.read_selected_devices') as mock:
            mock.return_value = 200, xr5_response
            request = uniconfig_worker.execute_read_uniconfig_topology_config({"inputData": {"devices": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=uniconfig?content=config")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "uniconfig")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0]["node-id"], "xr5")


class TestGetAllDevicesAsDynamicForkTasks(unittest.TestCase):
    def test_get_all_devices_as_dynamic_fork_tasks(self):
        with patch('uniconfig_worker.read_all_devices') as mock:
            mock.return_value = 200, xr5_response
            request = uniconfig_worker.get_all_devices_as_dynamic_fork_tasks(
                {"inputData": {"task": "Create_loopback_interface_uniconfig",
                               "task_params": "{\"loopback_id\": \"${workflow.input.loopback_id}\"}"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["dynamic_tasks_i"]["xr5"]["loopback_id"],
                             "${workflow.input.loopback_id}")
            self.assertEqual(request["output"]["dynamic_tasks_i"]["xr5"]["device_id"], "xr5")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["name"], "sub_task")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["taskReferenceName"], "xr5")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["type"], "SUB_WORKFLOW")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["subWorkflowParam"]["name"],
                             "Create_loopback_interface_uniconfig")
            self.assertEqual(request["output"]["dynamic_tasks"][0]["subWorkflowParam"]["version"], 1)


class TestReadStructuredData(unittest.TestCase):
    def test_read_structured_data_with_device(self):
        with patch('uniconfig_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(interface_response), encoding='utf-8'), 200, "")
            request = uniconfig_worker.read_structured_data(
                {"inputData": {"device_id": "xr5", "uri": "/frinx-openconfig-interfaces:interfaces"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"],
                             odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=xr5"
                                            "/frinx-uniconfig-topology:configuration"
                                            "/frinx-openconfig-interfaces:interfaces")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"]["interface"]
                             [0]['config']['name'], "GigabitEthernet0/0/0/0")
            self.assertEqual(request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"]["interface"]
                             [1]['config']['name'], "GigabitEthernet0/0/0/1")
            self.assertEqual(request["output"]["response_body"]["frinx-openconfig-interfaces:interfaces"]["interface"]
                             [2]['config']['name'], "GigabitEthernet0/0/0/2")

    def test_read_structured_data_no_device(self):
        with patch('uniconfig_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_request_response), encoding='utf-8'), 404, "")
            request = uniconfig_worker.read_structured_data(
                {"inputData": {"device_id": "", "uri": "/frinx-openconfig-interfaces:interfaces"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Request could not be completed because the relevant data model content does not exist")


class TestWriteStructuredData(unittest.TestCase):
    def test_write_structured_data_with_device(self):
        with patch('uniconfig_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 201, "")
            request = uniconfig_worker.write_structured_data(
                {"inputData": {"device_id": "xr5",
                               "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                               "template": "{\"interface\":[{\"name\":\"Loopback01\","
                                           "\"config\":{"
                                           "\"type\":\"iana-if-type:softwareLoopback\","
                                           "\"enabled\":false,"
                                           "\"name\":\"Loopback01\","
                                           "\"prefix\": \"aaa\"}}]}",
                               "params": {}}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"],
                             odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                                            "frinx-uniconfig-topology:configuration/"
                                            "frinx-openconfig-interfaces:interfaces/interface=Loopback01")
            self.assertEqual(request["output"]["response_code"], 201)

    def test_write_structured_data_with_no_device(self):
        with patch('uniconfig_worker.requests.put') as mock:
            mock.return_value = mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 404, "")
            request = uniconfig_worker.write_structured_data(
                {"inputData": {"device_id": "",
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
                             odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=/"
                                            "frinx-uniconfig-topology:configuration/"
                                            "frinx-openconfig-interfaces:interfaces/interface=Loopback01")
            self.assertEqual(request["output"]["response_code"], 404)

    def test_write_structured_data_with_bad_template(self):
        with patch('uniconfig_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_input_response), encoding='utf-8'), 400, "")
            request = uniconfig_worker.write_structured_data(
                {"inputData": {"device_id": "xr5",
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
                             odl_url_base + "/data/network-topology:network-topology/topology=uniconfig/node=xr5/"
                                            "frinx-uniconfig-topology:configuration/"
                                            "frinx-openconfig-interfaces:interfaces/interface=Loopback01")
            self.assertEqual(request["output"]["response_code"], 400)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Error parsing input: com.google.common.util.concurrent.UncheckedExecutionException: "
                             "java.lang.IllegalStateException: Schema node with name prefix was not found under "
                             "(http://frinx.openconfig.net/yang/interfaces?revision=2016-12-22)config.")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-tag"], "malformed-message")


class TestWriteStructuredDataAsDynamicForkTasks(unittest.TestCase):
    def test_write_structured_data_as_dynamic_fork_tasks(self):
        request = uniconfig_worker.write_structured_data_as_dynamic_fork_tasks(
            {"inputData": {"device_id": "XR01",
                           "uri": "/frinx-openconfig-interfaces:interfaces/interface=$iface",
                           "template": "{\"interface\":[{\"name\":\"$iface\","
                                       "\"config\":{\"type\":\"iana-if-type:ethernetCsmacd\","
                                       "\"name\":\"$iface\"},"
                                       "\"frinx-openconfig-if-ethernet:ethernet\":{"
                                       "\"config\":{\"frinx-openconfig-if-aggregate:aggregate-id\": "
                                       "\"Bundle-Ether3\"}}}]}",
                           "task_params": "GigabitEthernet0/0/0/0, GigabitEthernet0/0/0/1"
                           }})
        self.assertEqual(request["status"], "COMPLETED")
        self.assertEqual(request["output"]["dynamic_tasks_i"]["XR01GigabitEthernet0/0/0/0"]["device_id"], "XR01")
        self.assertEqual(request["output"]["dynamic_tasks_i"]["XR01GigabitEthernet0/0/0/0"]["template"],
                         "{\"interface\":[{\"name\":\"GigabitEthernet0/0/0/0\",\"config\":"
                         "{\"type\":\"iana-if-type:ethernetCsmacd\",\"name\":\"GigabitEthernet0/0/0/0\"},"
                         "\"frinx-openconfig-if-ethernet:ethernet\":{\"config\":"
                         "{\"frinx-openconfig-if-aggregate:aggregate-id\": \"Bundle-Ether3\"}}}]}",)
        self.assertEqual(request["output"]["dynamic_tasks_i"]["XR01GigabitEthernet0/0/0/0"]["uri"],
                         "/frinx-openconfig-interfaces:interfaces/interface=GigabitEthernet0%2F0%2F0%2F0")
        self.assertEqual(request["output"]["dynamic_tasks_i"]["XR01GigabitEthernet0/0/0/1"]["device_id"], "XR01")
        self.assertEqual(request["output"]["dynamic_tasks_i"]["XR01GigabitEthernet0/0/0/1"]["template"],
                         "{\"interface\":[{\"name\":\"GigabitEthernet0/0/0/1\",\"config\":"
                         "{\"type\":\"iana-if-type:ethernetCsmacd\",\"name\":\"GigabitEthernet0/0/0/1\"},"
                         "\"frinx-openconfig-if-ethernet:ethernet\":{\"config\":"
                         "{\"frinx-openconfig-if-aggregate:aggregate-id\": \"Bundle-Ether3\"}}}]}")
        self.assertEqual(request["output"]["dynamic_tasks"][0]["name"], "UNICONFIG_write_structured_device_data")
        self.assertEqual(request["output"]["dynamic_tasks"][0]["taskReferenceName"], "XR01GigabitEthernet0/0/0/0")
        self.assertEqual(request["output"]["dynamic_tasks"][0]["type"], "SIMPLE")
        self.assertEqual(request["output"]["dynamic_tasks"][1]["name"], "UNICONFIG_write_structured_device_data")
        self.assertEqual(request["output"]["dynamic_tasks"][1]["taskReferenceName"], "XR01GigabitEthernet0/0/0/1")
        self.assertEqual(request["output"]["dynamic_tasks"][1]["type"], "SIMPLE")


class TestDeleteStructuredData(unittest.TestCase):
    def test_delete_structured_data_with_device(self):
        with patch('uniconfig_worker.requests.delete') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 204, "")
            request = uniconfig_worker.delete_structured_data(
                {"inputData": {"device_id": "xr5",
                               "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})

    def test_delete_structured_data_with_bad_template(self):
        with patch('uniconfig_worker.requests.delete') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_request_response), encoding='utf-8'), 404, "")
            request = uniconfig_worker.delete_structured_data({
                "inputData": {
                    "device_id": "xr5",
                    "uri": "/frinx-openconfig-interfaces:interfaces/interface=Loopback01",
                }})

            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Request could not be completed because the relevant data model content does not exist")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-tag"], "data-missing")


class TestExecuteCheckUniconfigNodeExists(unittest.TestCase):
    def test_execute_check_uniconfig_node_exists_with_existing_device_installed(self):
        with patch('uniconfig_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(
                {"frinx-uniconfig-topology:connection-status": "installed"}), encoding='utf-8'), 200, "")
            request = uniconfig_worker.execute_check_uniconfig_node_exists({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["frinx-uniconfig-topology:connection-status"],
                             "installed")

    def test_execute_check_uniconfig_node_exists_with_existing_device_installing(self):
        with patch('uniconfig_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(
                {"frinx-uniconfig-topology:connection-status": "installing"}), encoding='utf-8'), 200, "")
            request = uniconfig_worker.execute_check_uniconfig_node_exists({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["frinx-uniconfig-topology:connection-status"],
                             "installing")

    def test_execute_check_uniconfig_node_exists_with_non_existing_device(self):
        with patch('uniconfig_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(bad_request_response), encoding='utf-8'), 404, "")
            request = uniconfig_worker.execute_check_uniconfig_node_exists({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 404)
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-type"], "protocol")
            self.assertEqual(request["output"]["response_body"]['errors']['error'][0]["error-message"],
                             "Request could not be completed because the relevant data model content does not exist")


class TestCommit(unittest.TestCase):
    def test_commit_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(commit_output), encoding='utf-8'), 200, "")
            request = uniconfig_worker.commit({"inputData": {"devices": "xr5, xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "configuration-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1]["node-id"],
                             "xr6")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1][
                                 "configuration-status"], "complete")

    def test_commit_with_non_existing_device(self):
        try:
            uniconfig_worker.commit({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestDryRun(unittest.TestCase):
    def test_dry_run_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(dry_run_output), encoding='utf-8'), 200, "")
            request = uniconfig_worker.dryrun_commit({"inputData": {"devices": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "configuration-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "configuration"], "2019-09-13T08:37:28.331: configure terminal\n"
                                                   "2019-09-13T08:37:28.536: interface GigabitEthernet0/0/0/1\n"
                                                   "shutdown\nroot\n\n"
                                                   "2019-09-13T08:37:28.536: commit\n2019-09-13T08:37:28.536: end\n")

    def test_dry_run_with_non_existing_device(self):
        try:
            uniconfig_worker.dryrun_commit({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestCheckCommit(unittest.TestCase):
    def test_check_commit_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(commit_output), encoding='utf-8'), 200, "")
            request = uniconfig_worker.checked_commit({"inputData": {"devices": "xr5, xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "configuration-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1]["node-id"],
                             "xr6")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1][
                                 "configuration-status"], "complete")

    def test_commit_with_non_existing_device(self):
        try:
            uniconfig_worker.checked_commit({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestCalculateDiff(unittest.TestCase):
    def test_calculate_diff_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(calculate_diff_output), encoding='utf-8'), 200, "")
            request = uniconfig_worker.calc_diff({"inputData": {"devices": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                "updated-data"][0]["path"], "network-topology:network-topology/topology=uniconfig/"
                                                            "node=xr5/frinx-uniconfig-topology:configuration/"
                                                            "frinx-openconfig-interfaces:interfaces/"
                                                            "interface=GigabitEthernet0%2F0%2F0%2F0/config")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "updated-data"][0]["data-actual"], "{\n  \"frinx-openconfig-interfaces:config\": {\n"
                                                                    "    \"type\": \"iana-if-type:ethernetCsmacd\",\n"
                                                                    "    \"enabled\": false,\n"
                                                                    "    \"name\": \"GigabitEthernet0/0/0/0\"\n  }\n}")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "updated-data"][0]["data-intended"],
                             "{\n  \"frinx-openconfig-interfaces:config\": {\n"
                             "    \"type\": \"iana-if-type:ethernetCsmacd\",\n"
                             "    \"enabled\": false,\n"
                             "    \"name\": \"GigabitEthernet0/0/0/0dfhdfghd\"\n  }\n}")

    def test_calculate_diff_with_non_existing_device(self):
        try:
            uniconfig_worker.calc_diff({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestSyncFromNetwork(unittest.TestCase):
    def test_sync_from_network_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(RPC_output_multiple_devices), encoding='utf-8'), 200, "")
            request = uniconfig_worker.sync_from_network({"inputData": {"devices": "xr5, xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1]["node-id"],
                             "xr6")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1][
                                 "status"], "complete")

    def test_sync_from_network_with_non_existing_device(self):
        try:
            uniconfig_worker.sync_from_network({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestReplaceConfigWithOper(unittest.TestCase):
    def test_replace_config_with_oper_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(RPC_output_multiple_devices), encoding='utf-8'), 200, "")
            request = uniconfig_worker.replace_config_with_oper({"inputData": {"devices": "xr5, xr6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1]["node-id"],
                             "xr6")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][1][
                                 "status"], "complete")

    def test_replace_config_with_oper_with_non_existing_device(self):
        try:
            uniconfig_worker.replace_config_with_oper({"inputData": {"devices": ""}})
        except Exception:
            return
        self.assertFalse("Calling RPC with empty device list is not allowed")


class TestSnapshot(unittest.TestCase):
    def test_create_snapshot_with_existing_devices(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(RPC_output_one_device), encoding='utf-8'), 200, "")
            request = uniconfig_worker.create_snapshot({"inputData": {"devices": "xr5", "name": "xr5_snapshot"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"]["output"]["overall-status"], "complete")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0]["node-id"],
                             "xr5")
            self.assertEqual(request["output"]["response_body"]["output"]["node-results"]["node-result"][0][
                                 "status"], "complete")


class TestUtilityFunction(unittest.TestCase):
    def test_create_snapshot_request(self):
        request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": "IOS1"}})
        assert request["input"]["name"] == "abcd"
        assert request["input"]["target-nodes"]["node"] == ["IOS1"]
        request = uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": ", IOS1, IOS2 ,"}})
        assert request["input"]["name"] == "abcd"
        assert request["input"]["target-nodes"]["node"] == ["IOS1", "IOS2"]
        assert "{\"input\": {\"name\": \"abcd\", \"target-nodes\": {\"node\": [\"IOS1\", \"IOS2\"]}}}" == json.dumps(
            request)

    def test_create_snapshot_no_devices(self):
        try:
            uniconfig_worker.create_snapshot_request({"inputData": {"name": "abcd", "devices": ""}})
        except Exception:
            return
        assert False, "Calling RPC with empty device list is not allowed"

    def test_escape(self):
        uri = uniconfig_worker.apply_functions("interfaces/interface=escape(GigabitEthernet0/0/0/0)/abcd/escape(a/b)")
        assert uri == "interfaces/interface=GigabitEthernet0%2F0%2F0%2F0/abcd/a%2Fb"
        uri = uniconfig_worker.apply_functions(None)
        assert uri is None
        uri = uniconfig_worker.apply_functions("")
        assert uri is ""


class TestCreateTransaction(unittest.TestCase):
    def test_create_transaction(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 201,
                                             SimpleCookie(r'UNICONFIGTXID=92a26bac-d623-407e-9a76-3fad3e7cc698'
                                                          r' JSESSIONID=1g82dajs6marv18scrdabpgc3m'))
            request = uniconfig_worker.create_transaction({"inputData": {"maxAgeSec": "30"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 201)
            self.assertEqual(request["output"]["response_body"],
                             {"UNICONFIGTXID": "92a26bac-d623-407e-9a76-3fad3e7cc698"})


class TestCloseTransaction(unittest.TestCase):
    def test_close_transaction_successful(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 200,
                                             SimpleCookie(r'UNICONFIGTXID=92a26bac-d623-407e-9a76-3fad3e7cc698'
                                                          r' JSESSIONID=1g82dajs6marv18scrdabpgc3m'))
            request = uniconfig_worker.close_transaction({
                "inputData": {"uniconfig_tx_id": "882ce396-1235-43eb-9596-bad0b25c81d6"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["response_code"], 200)
            self.assertEqual(request["output"]["response_body"], {})

    def test_close_transaction_closed_trans(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes("Unknown uniconfig transaction 92a26bac-d623-407e-9a76-3fad3e7cc698",
                                                   encoding='utf-8'), 403, "")
            request = uniconfig_worker.close_transaction({
                "inputData": {"uniconfig_tx_id": "92a26bac-d623-407e-9a76-3fad3e7cc698"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 403)
            self.assertEqual(request["output"]["response_body"], {})

    def test_close_transaction_no_uniconfig_tx_id(self):
        with patch('uniconfig_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 400, "")
            request = uniconfig_worker.close_transaction({"inputData": {"uniconfig_tx_id": ""}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["response_code"], 400)
            self.assertEqual(request["output"]["response_body"], {})


if __name__ == "__main__":
    unittest.main()
