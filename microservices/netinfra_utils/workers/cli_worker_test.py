import json
from unittest.mock import patch
import unittest

import cli_worker
from frinx_rest import odl_url_base

exec_and_read_rpc = {
    "output": {
        "output": "Fri Dec 20 09:33:29.094 UTC\r\nBuilding configuration...\r\n!! IOS XR Configuration 5.3.4\r\n!! Last configuration change at Tue Dec 17 15:18:26 2019 by cisco\r\n!\r\ninterface Loopback666\r\n shutdown\r\n!\r\ninterface MgmtEth0/0/CPU0/0\r\n ipv4 address 192.168.1.215 255.255.255.0\r\n!\r\ninterface GigabitEthernet0/0/0/0\r\n shutdown\r\n!\r\ninterface GigabitEthernet0/0/0/1\r\n shutdown\r\n!\r\ninterface GigabitEthernet0/0/0/2\r\n shutdown\r\n!\r\nroute-policy policy2\r\nend-policy\r\n!\r\nrouter ospf 100\r\n area 0\r\n  interface GigabitEthernet0/0/0/2\r\n   cost 77\r\n  !\r\n !\r\n!\r\nrouter ospf 65535\r\n area 0\r\n  interface Bundle-Ether65535\r\n  !\r\n !\r\n!\r\nrouter bgp 1\r\n neighbor-group nbrgroup1\r\n !\r\n neighbor 8.8.8.8\r\n  remote-as 65000\r\n  use neighbor-group nbrgroup1\r\n !\r\n!\r\nrouter bgp 666 instance second-default\r\n address-family ipv6 unicast\r\n  network 2010:ab8:2::/48 route-policy policy2\r\n !\r\n neighbor-group nbrgroup1\r\n !\r\n neighbor 99.0.0.99\r\n  remote-as 1\r\n  ebgp-multihop 1\r\n  password encrypted 02001652051E5E79080B\r\n  shutdown\r\n  description some text\r\n  update-source Loopback97\r\n  address-family ipv6 unicast\r\n   send-community-ebgp\r\n   route-policy policy2 in\r\n   maximum-prefix 25 75\r\n   default-originate\r\n   next-hop-self\r\n   remove-private-AS\r\n   soft-reconfiguration inbound always\r\n  !\r\n !\r\n!\r\nssh server v2\r\nssh server netconf port 830\r\nnetconf-yang agent\r\n ssh\r\n!\r\nend"
    }
}
exec_and_read_rpc_no_device = {
    "errors": {
        "error": [
            {
                "error-message": "Mount point does not exist.",
                "error-tag": "data-missing",
                "error-type": "protocol"
            }
        ]
    }
}
cli_node_connecting = {
    "node": [
        {
            "cli-topology:default-commit-error-patterns": {},
            "cli-topology:connected-message": "Connecting",
            "node-id": "xr5",
            "cli-topology:default-error-patterns": {
                "error-pattern": [
                    "(^|\\n)% (?i)Incomplete command(?-i).*",
                    "(^|\\n)\\s+\\^.*",
                    "(^|\\n)% (?i)Ambiguous command(?-i).*",
                    "(^|\\n)% (?i)invalid input(?-i).*"
                ]
            },
            "cli-topology:connection-status": "connecting"
        }
    ]
}
cli_node_connected = {
    "node": [
        {
            "cli-topology:default-commit-error-patterns": {
                "commit-error-pattern": [
                    "(^|\\n)% (?i)Failed(?-i).*"
                ]
            },
            "cli-topology:host": "192.168.1.215",
            "cli-topology:default-error-patterns": {
                "error-pattern": [
                    "(^|\\n)% (?i)Incomplete command(?-i).*",
                    "(^|\\n)\\s+\\^.*",
                    "(^|\\n)% (?i)Ambiguous command(?-i).*",
                    "(^|\\n)% (?i)invalid input(?-i).*"
                    ]
                },
            "cli-topology:connection-status": "connected",
            "node-id": "xr5",
            "cli-topology:connected-message": "Success"
        }
    ]
}
cli_node_non_exist = {
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
cli_oper_without_device = {
    "topology": [
        {
            "topology-id": "cli"
        }
    ]
}
cli_oper_with_device = {
    "topology": [
        {
            "topology-id": "cli",
            "node": [
                {
                    "node-id": "xr5",
                    "cli-topology:connection-status": "connected",
                    "cli-topology:connected-message": "Success",
                    "cli-topology:default-commit-error-patterns": {},
                    "cli-topology:default-error-patterns": {},
                    "cli-topology:host": "192.168.1.215",
                    "cli-topology:port": 22,
                    "cli-topology:available-capabilities": {}
                }
            ]
        }
    ]
}
cli_read_journal = {
    "output": {
        "journal": "2020-01-02T11:49:23.574: show configuration commit list | utility egrep \"^1 \"\n2020-01-02T11:49:23.981: show running-config\n2020-01-02T11:56:28.905: show running-config interface | include ^interface\n2020-01-02T11:56:29.465: configure terminal\n2020-01-02T11:56:32.178: interface Loopback66\nshutdown\nroot\n\n2020-01-02T11:56:32.674: commit\n2020-01-02T11:56:39.151: end\n2020-01-02T11:58:41.023: show running-config\n"
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
        with patch('cli_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 201)
            request = cli_worker.execute_mount_cli(
                {"inputData": {"device_id": "xr5", "host": "192.168.1.1", "port": "22", "protocol": "ssh",
                               "type": "ios xr", "version": "5.3.4", "username": "name", "password": "password"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5")
            self.assertEqual(request["output"]["response_code"], 201)
            self.assertEqual(request["output"]["response_body"], {})

    def test_mount_existing_device(self):
        with patch('cli_worker.requests.put') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 204)
            request = cli_worker.execute_mount_cli(
                {"inputData": {"device_id": "xr5", "host": "192.168.1.1", "port": "22", "protocol": "ssh",
                               "type": "ios xr", "version": "5.3.4", "username": "name", "password": "password"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})


class TestUnmount(unittest.TestCase):
    def test_unmount_existing_device(self):
        with patch('cli_worker.requests.delete') as mock:
            mock.return_value = MockResponse(bytes(json.dumps({}), encoding='utf-8'), 204)
            request = cli_worker.execute_unmount_cli(
                {"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5")
            self.assertEqual(request["output"]["response_code"], 204)
            self.assertEqual(request["output"]["response_body"], {})


class TestExecuteAndReadRpcCli(unittest.TestCase):
    def test_execute_and_read_rpc_cli(self):
        with patch('cli_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(exec_and_read_rpc), encoding='utf-8'), 200)
            request = cli_worker.execute_and_read_rpc_cli(
                {"inputData": {"device_id": "xr5", "template": "show running-config", "params": ""}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/operations/network-topology:network-topology/topology=cli/"
                               "node=xr5/yang-ext:mount/cli-unit-generic:execute-and-read")
            self.assertEqual(request["output"]["response_body"], exec_and_read_rpc)

    def test_execute_and_read_rpc_cli_non_existing_device(self):
        with patch('cli_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(exec_and_read_rpc_no_device), encoding='utf-8'), 404)
            request = cli_worker.execute_and_read_rpc_cli(
                {"inputData": {"device_id": "xr5", "template": "show running-config", "params": ""}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/operations/network-topology:network-topology/topology=cli/"
                               "node=xr5/yang-ext:mount/cli-unit-generic:execute-and-read")
            self.assertEqual(request["output"]["response_body"], exec_and_read_rpc_no_device)


class TestCheckCliConnected(unittest.TestCase):
    def test_execute_check_connected_cli_connecting(self):
        with patch('cli_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_node_connecting), encoding='utf-8'), 200)
            request = cli_worker.execute_check_connected_cli({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["node"][0]["cli-topology:connection-status"],
                             "connecting")

    def test_execute_check_connected_cli_connected(self):
        with patch('cli_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_node_connected), encoding='utf-8'), 200)
            request = cli_worker.execute_check_connected_cli({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["node"][0]["cli-topology:connection-status"],
                             "connected")


class TestCheckCliIdAvailable(unittest.TestCase):
    def test_execute_check_cli_id_available_exist(self):
        with patch('cli_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_node_connected), encoding='utf-8'), 200)
            request = cli_worker.execute_check_cli_id_available({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5")

    def test_execute_check_cli_id_available_non_exist(self):
        with patch('cli_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_node_non_exist), encoding='utf-8'), 404)
            request = cli_worker.execute_check_cli_id_available({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli/node=xr5")


class TestExecuteReadCliTopologyOperational(unittest.TestCase):
    def test_execute_read_cli_topology_operational_without_device(self):
        with patch('cli_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_oper_without_device), encoding='utf-8'), 200)
            request = cli_worker.execute_read_cli_topology_operational({})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "cli")

    def test_execute_read_cli_topology_operational_with_device(self):
        with patch('cli_worker.requests.get') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_oper_with_device), encoding='utf-8'), 200)
            request = cli_worker.execute_read_cli_topology_operational({})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/data/network-topology:network-topology/topology=cli?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["topology-id"], "cli")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0]["node-id"], "xr5")
            self.assertEqual(request["output"]["response_body"]["topology"][0]["node"][0][
                                 "cli-topology:connection-status"], "connected")


class TestGetAllDevicesAsDynamicForkTasks(unittest.TestCase):
    def test_get_all_devices_as_dynamic_fork_tasks(self):
        with patch('cli_worker.read_all_devices') as mock:
            mock.return_value = 200, cli_oper_with_device
            request = cli_worker.get_all_devices_as_dynamic_fork_tasks(
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


class TestExecuteGetCliJournal(unittest.TestCase):
    def test_execute_get_cli_journal_existing_device(self):
        with patch('cli_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(cli_read_journal), encoding='utf-8'), 200)
            request = cli_worker.execute_get_cli_journal({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "COMPLETED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/operations/network-topology:network-topology/topology=cli"
                               "/node=xr5/yang-ext:mount/journal:read-journal?content=nonconfig")
            self.assertEqual(request["output"]["response_body"]["output"]["journal"],
                             cli_read_journal["output"]["journal"])

    def test_execute_get_cli_journal_non_existing_device(self):
        with patch('cli_worker.requests.post') as mock:
            mock.return_value = MockResponse(bytes(json.dumps(exec_and_read_rpc_no_device), encoding='utf-8'), 404)
            request = cli_worker.execute_get_cli_journal({"inputData": {"device_id": "xr5"}})
            self.assertEqual(request["status"], "FAILED")
            self.assertEqual(request["output"]["url"], odl_url_base
                             + "/operations/network-topology:network-topology/topology=cli"
                               "/node=xr5/yang-ext:mount/journal:read-journal?content=nonconfig")
            self.assertEqual(request["output"]["response_body"], exec_and_read_rpc_no_device)


if __name__ == "__main__":
    unittest.main()
