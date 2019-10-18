from vll_model import RemoteDevice
import vll_model


class Device(RemoteDevice):

    def __init__(self, device):
        RemoteDevice.__init__(self, device)
        self.untagged = device.get('untagged', None)

    @staticmethod
    def parse(device, index):
        # type: (dict, int) -> Device
        try:
            return Device(device)
        except BaseException as e:
            raise Exception("Unable to parse device at index: %s due to: %s" % (index, e.message))

    def __eq__(self, other):
        return self.id == other.id and self.interface == other.interface and self.remote_ip == other.remote_ip and self.vlan == other.vlan

    def __hash__(self):
        return hash(self.id) & hash(self.interface) & hash(self.remote_ip) & hash(self.vlan)


class Service:

    def __init__(self, service):
        try:
            self.id = service['id']
            self.mtu = service.get('mtu', 0)
            self.devices = self.parse_devices(service['devices'])
            if 'remotes' in service:
                self.remotes = service['remotes']
            self.vccid = service['vccid']
        except BaseException as e:
            raise Exception("Unable to parse service: %s due to: %s" % (service, e.message))

    @staticmethod
    def parse_devices(devices):
        # type: (list) -> list[Device]
        return [Device.parse(d, i) for i, d in enumerate(devices)]

    @staticmethod
    def parse_from_task(task):
        return Service(Service.extract_from_task(task))

    @staticmethod
    def extract_from_task(task):
        template = task['inputData']['service']
        return template if isinstance(template, dict) else eval(template)

    def device_ids(self):
        return [device.id for device in filter(lambda d: d.id != "UNKNOWN", self.devices)]

    def to_dict(self):
        devs = []
        for dev in self.devices:
            devs.append(dict(filter(lambda x: x[1], vars(dev).items())))

        self.remotes = []
        serv = dict(filter(lambda x: x[1], vars(self).items()))
        serv['devices'] = devs
        return serv

    @staticmethod
    def parse_from_openconfig_network(node_id, l2vsi, default_ni, ifcs):
        cps = l2vsi.get('connection-points', {}).get('connection-point')
        if cps is None:
            return

        local = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:LOCAL', cps)
        remote = filter(lambda cp: cp['endpoints']['endpoint'][0]['config']['type'] == 'frinx-openconfig-network-instance-types:REMOTE', cps)

        service = {
            'id': l2vsi.get('name', 'Unable to find name'),
            'vccid': remote[0]['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'],
            'devices': [],
            'remotes': []
        }

        mtu = l2vsi['config'].get('mtu', None)
        if mtu:
            service['mtu'] = mtu

        for l in local:
            tmp_conn = {
                'id': node_id,
                'interface': l['endpoints']['endpoint'][0]['local']['config']['interface'],
                'vlan': l['endpoints']['endpoint'][0]['local']['config']['subinterface'],
                'untagged': l['endpoints']['endpoint'][0]['local']['config'].get('frinx-brocade-cp-extension:subinterface-untagged', None),
                'remote_ip': "UNKNOWN"
            }
            vll_model.Service.set_attributes(default_ni, ifcs, tmp_conn)
            service['devices'].append(tmp_conn)

        for r in remote:
            tmp_conn = {
                'id': "UNKNOWN",
                'interface': "UNKNOWN",
                'vlan': "UNKNOWN",
                'untagged': "UNKNOWN",
                'remote_ip': r['endpoints']['endpoint'][0]['remote']['config']['remote-system']
            }
            service['devices'].append(tmp_conn)
            service['remotes'].append(r['endpoints']['endpoint'][0]['remote']['config']['remote-system'])

        return Service(service)

    def merge(self, other):
        # type: (Service, Service) -> Service
        self_unknown_ifcs = filter(lambda device: device.remote_ip == "UNKNOWN", self.devices)
        other_unknown_ifcs = filter(lambda device: device.remote_ip == "UNKNOWN", other.devices)

        self_has_one_id = len(set(device.id for device in self_unknown_ifcs)) == 1
        other_has_one_id = len(set(device.id for device in other_unknown_ifcs)) == 1

        self_remoteip = list(set(self.remotes) - set(other.remotes))
        other_remoteip = list(set(other.remotes) - set(self.remotes))

        self_remotes = filter(lambda device: device.remote_ip in self_remoteip and device.id == "UNKNOWN", self.devices)
        other_remotes = filter(lambda device: device.remote_ip in other_remoteip and device.id == "UNKNOWN", other.devices)

        is_one_remote_other = other_remoteip and len(other_remoteip) == 1
        if is_one_remote_other and self_has_one_id:
            Service.set_remotes(other, self_unknown_ifcs, other_remoteip[0], other_remotes)

        is_one_remote_self = self_remoteip and len(self_remoteip) == 1
        if is_one_remote_self and other_has_one_id:
            Service.set_remotes(self, other_unknown_ifcs, self_remoteip[0], self_remotes)

        self.remotes = list(set(self.remotes) | set(other.remotes))
        if is_one_remote_self and is_one_remote_other:
            self.remotes = filter(lambda remote: remote not in set(other_remoteip + self_remoteip), self.remotes)

        self.devices = list(set(set(self.devices) | (set(other.devices))))

        ifcs_with_ip = set([d.remote_ip for d in filter(lambda de: de.remote_ip != "UNKNOWN" and de.id != "UNKNOWN", self.devices)])
        for d in filter(lambda de: de.id == "UNKNOWN", self.devices):
            if d.remote_ip in ifcs_with_ip:
                self.devices.remove(d)

        return self

    @staticmethod
    def set_remotes(service, interfaces, remote_ip, remotes):
        for d in interfaces:
            d.remote_ip = remote_ip
        for d in remotes:
            if d.remote_ip == remote_ip:
                service.devices.remove(d)


class ServiceDeletion(Service):

    def __init__(self, service):
        Service.__init__(self, service)

    def parse_devices(self, devices):
        # type: (Service, list) -> list[Device]
        for d in devices:
            d.update({"remote_ip": "UNKNOWN"})
            if 'interface' not in d:
                d.update({"interface": "UNKNOWN"})
        return [Device.parse(d, i) for i, d in enumerate(devices)]

    @staticmethod
    def parse_from_task(task):
        if task['inputData']['service'].get('vccid') is None:
            task['inputData']['service'].update({'vccid':'UNKNOWN'})
        return ServiceDeletion(Service.extract_from_task(task))