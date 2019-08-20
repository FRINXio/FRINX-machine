class Local:

    switch_tpid = {
        "0x8100": "frinx-openconfig-vlan-types:TPID_0X8100",
        "0x9100": "frinx-openconfig-vlan-types:TPID_0X9100"
    }

    def __init__(self, ifc):
        self.interface = ifc['interface']
        self.vlan = ifc['vlan']
        self.untagged = ifc.get('untagged', None)

    @staticmethod
    def parse_from_list(device, index):
        # type: (Device, int) -> Local
        return [Local.parse(local) for local in device[index]] if len(device[index]) > 0 else {}

    @staticmethod
    def parse(ifc):
        # type: (dict) -> Local
        try:
            return Local(ifc)
        except BaseException as e:
            raise Exception("Unable to parse local at index: %s due to: %s" % (0, e.message))


class Remote:

    def __init__(self, r):
        self.remote_ip = r

    @staticmethod
    def parse_from_list(device, index):
        # type: (dict, int) -> Remote
        return [Remote.parse(r, index) for r in device[index]] if len(device[index]) > 0 else {}

    @staticmethod
    def parse(remote, index):
        # type: (str, int) -> Remote
        try:
            return Remote(remote)
        except BaseException as e:
            raise Exception("Unable to parse remote at index: %s due to: %s" % (index, e.message))


class Device:

    def __init__(self, device):
        self.id = device['id']
        self.remotes = Remote.parse_from_list(device, 'remote_ip')
        self.locals = Local.parse_from_list(device, 'interface')
        self.description = device.get("description", None)
        self.auto_negotiate = device.get('auto_negotiate', None)
        self.tpid = device.get('tpid', None)
        self.in_policy = device.get('in_policy', None)
        self.out_policy = device.get('out_policy', None)
        if self.tpid is not None:
            if Local.switch_tpid.get(self.tpid) is  None:
                raise ("Invalid tpid value: %s, expected one of: %s" % (self.tpid, Local.switch_tpid))
            self.tpid = Local.switch_tpid.get(self.tpid)

    @staticmethod
    def parse_from_list(devices, index):
        # type: (list, int) -> Device
        return Device.parse(devices[index], index)

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


class RemoteService(Service):

    def __init__(self, service):
        Service.__init__(self, service)
        try:
            self.vccid = service['vccid']
        except BaseException as e:
            raise Exception("Unable to parse remote service: %s due to: %s" % (service, e.message))

    @Service.devices.getter
    def devices(self):
        # type: (Service) -> list[Device]
        return self.devices

    def parse_devices(self, devices):
        # type: (Service, list) -> list[Device]
        return [Device.parse(d, i) for i, d in enumerate(devices)]

    @staticmethod
    def parse_from_task(task):
        return RemoteService(Service.extract_from_task(task))

    @staticmethod
    def parse_from_openconfig_network(node_id, l2vsi):
        cps = l2vsi.get('connection-points', {}).get('connection-point')
        if cps is None:
            return

        local = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:LOCAL', cps)
        remote = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:REMOTE', cps)

        service = {
            'id': l2vsi.get('name', 'Unable to find name'),
            'vccid': remote[0]['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'],
            'devices': [
                {
                    'id': node_id,
                    'interface': [{
                                    "interface": l['endpoints']['endpoint'][0]['local']['config']['interface'],
                                    "vlan": l['endpoints']['endpoint'][0]['local']['config']['subinterface'],
                                    "untagged": l['endpoints']['endpoint'][0]['local']['config'].get('frinx-brocade-cp-extension:subinterface-untagged', None)
                                } for i, l in enumerate(local)],
                    'remote_ip': [r['endpoints']['endpoint'][0]['remote']['config']['remote-system'] for i, r in enumerate(remote)],
                },
                {
                    'id': "UNKNOWN",
                    'interface': [],
                    'remote_ip' : []
                }
            ]
        }

        return RemoteService(service)

    def merge(self, other):
        # type: (RemoteService, RemoteService) -> RemoteService
        self.devices = filter(lambda device: device.id != "UNKNOWN", self.devices) \
                       + filter(lambda device: device.id != "UNKNOWN", other.devices)
        return self
