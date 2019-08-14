class Device:

    switch_tpid = {
        "0x8100": "frinx-openconfig-vlan-types:TPID_0X8100",
        "0x9100": "frinx-openconfig-vlan-types:TPID_0X9100"
    }

    def __init__(self, device):
        self.id = device['id']
        self.interface = device['interface']
        self.description = device.get("description", None)
        self.auto_negotiate = device.get('auto_negotiate', None)
        self.vlan = device.get('vlan', None)
        self.tpid = device.get('tpid', None)
        if self.tpid is not None:
            assert Device.switch_tpid.get(self.tpid) is not None, \
                "Invalid tpid value: %s, expected one of: %s" % (self.tpid, Device.switch_tpid)
            self.tpid = Device.switch_tpid.get(self.tpid)

    @staticmethod
    def parse(device, index):
        # type: (dict, int) -> Device
        try:
            return Device(device)
        except BaseException as e:
            raise Exception("Unable to parse device at index: %s due to: %s" % (index, e.message))

    def is_same_device(self, other):
        # type: (Device, Device) -> bool
        return self.id == other.id

    def is_same_interface(self, other):
        # type: (Device, Device) -> bool
        return self.interface == other.interface


class LocalDevice(Device):

    @staticmethod
    def parse_from_list(devices, index):
        # type: (list, int) -> LocalDevice
        return LocalDevice.parse(devices[index], index)

    @staticmethod
    def parse(device, index):
        # type: (dict, int) -> LocalDevice
        try:
            return LocalDevice(device)
        except BaseException as e:
            raise Exception("Unable to parse device at index: %s due to: %s" % (index, e.message))


class RemoteDevice(Device):

    def __init__(self, device):
        Device.__init__(self, device)
        self.remote_ip = device['remote_ip']

    @staticmethod
    def parse_from_list(devices, index):
        # type: (list, int) -> RemoteDevice
        return RemoteDevice.parse(devices[index], index)

    @staticmethod
    def parse(device, index):
        # type: (dict, int) -> RemoteDevice
        try:
            return RemoteDevice(device)
        except BaseException as e:
            raise Exception("Unable to parse device at index: %s due to: %s" % (index, e.message))


class Service:

    @property
    def devices(self):
        return self._devices

    @devices.setter
    def devices(self, value):
        self._devices = value

    def __init__(self, service):
        try:
            self.id = service['id']
            self.mtu = service.get('mtu', 0)
            assert len(service['devices']) is 2, 'For VLL service, 2 devices are expected. Received: %s' % len(service['devices'])
            self.devices = self.parse_devices(service['devices'])
        except BaseException as e:
            raise Exception("Unable to parse service: %s due to: %s" % (service, e.message))

    def parse_devices(self, devices):
        # type: (Service, list) -> list[Device]
        return [Device.parse(d, i) for i, d in enumerate(devices)]

    def is_local(self):
        return self.devices[0].is_same_device(self.devices[1])

    @staticmethod
    def parse_from_task(task):
        return Service(Service.extract_from_task(task))

    @staticmethod
    def extract_from_task(task):
        template = task['inputData']['service']
        return template if isinstance(template, dict) else eval(template)

    def device_ids(self):
        return [device.id for device in self.devices]


class LocalService(Service):

    @Service.devices.getter
    def devices(self):
        # type: (Service) -> list[LocalDevice]
        return self.devices

    def parse_devices(self, devices):
        return [LocalDevice.parse(d, i) for i, d in enumerate(devices)]

    @staticmethod
    def parse_from_task(task):
        return LocalService(Service.extract_from_task(task))

    @staticmethod
    def parse_from_openconfig_network(node_id, l2p2p):
        service = {
            'id': l2p2p.get('name', 'Unable to find name'),
            'devices': [
                {
                    'id': node_id,
                    'interface':
                        l2p2p['connection-points']['connection-point'][0]['endpoints']['endpoint'][0]['local']['config']['interface'],
                },
                {
                    'id': node_id,
                    'interface':
                        l2p2p['connection-points']['connection-point'][1]['endpoints']['endpoint'][0]['local']['config']['interface'],
                }
            ]
        }

        vlan1 = l2p2p['connection-points']['connection-point'][0]['endpoints']['endpoint'][0]['local']['config'].get('subinterface', None)
        if vlan1:
            service['devices'][0]['vlan'] = vlan1

        vlan2 = l2p2p['connection-points']['connection-point'][1]['endpoints']['endpoint'][0]['local']['config'].get('subinterface', None)
        if vlan2:
            service['devices'][1]['vlan'] = vlan2

        return LocalService(service)


class RemoteService(Service):

    def __init__(self, service):
        Service.__init__(self, service)
        try:
            self.vccid = service['vccid']
        except BaseException as e:
            raise Exception("Unable to parse remote service: %s due to: %s" % (service, e.message))

    @Service.devices.getter
    def devices(self):
        # type: (Service) -> list[RemoteDevice]
        return self.devices

    def parse_devices(self, devices):
        # type: (Service, list) -> list[RemoteDevice]
        return [RemoteDevice.parse(d, i) for i, d in enumerate(devices)]

    @staticmethod
    def parse_from_task(task):
        return RemoteService(Service.extract_from_task(task))

    @staticmethod
    def parse_from_openconfig_network(node_id, l2p2p):
        cps = l2p2p.get('connection-points', {}).get('connection-point')
        local = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:LOCAL', cps)[0]
        remote = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:REMOTE', cps)[0]

        service = {
            'id': l2p2p.get('name', 'Unable to find name'),
            'vccid': remote['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'],
            'devices': [
                {
                    'id': node_id,
                    'interface': local['endpoints']['endpoint'][0]['local']['config']['interface'],
                    'remote_ip': remote['endpoints']['endpoint'][0]['remote']['config']['remote-system'],
                },
                {
                    'id': "UNKNOWN",
                    'interface': "UNKNOWN",
                    'remote_ip' : "UNKNOWN"
                }
            ]
        }

        vlan1 = local['endpoints']['endpoint'][0]['local']['config'].get('subinterface', None)
        if vlan1:
            service['devices'][0]['vlan'] = vlan1

        return RemoteService(service)

    def merge(self, other):
        # type: (RemoteService, RemoteService) -> RemoteService
        self.devices = filter(lambda device: device.id != "UNKNOWN", self.devices) \
                       + filter(lambda device: device.id != "UNKNOWN", other.devices)
        return self
