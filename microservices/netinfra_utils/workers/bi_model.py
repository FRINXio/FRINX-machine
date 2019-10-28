from vll_model import Device
import vll_model
import copy


class BiDevice(Device):

    def __init__(self, device):
        Device.__init__(self, device)
        self.ve_interface = device.get('ve_interface', None)
        self.ip = device.get('ip', None)
        self.untagged = device.get('untagged', None)

    @staticmethod
    def parser(device, index):
        # type: (dict, int) -> BiDevice
        try:
            return BiDevice(device)
        except BaseException as e:
            raise Exception("Unable to parse device at index: %s due to: %s" % (index, e.message))


class Service:

    def __init__(self, service):
        self.id = service['id']
        self.devices = Service.parse_devices(service['devices'])

    @staticmethod
    def parse(device, index):
        # type: (dict, int) -> Service
        try:
            return Service(device)
        except BaseException as e:
            raise Exception("Unable to parse service at index: %s due to: %s" % (index, e.message))

    @staticmethod
    def parse_devices(devices):
        # type: (list) -> list[BiDevice]
        return [BiDevice.parser(d, i) for i, d in enumerate(devices)]

    def device_ids(self):
        return list(set([device.id for device in self.devices]))

    @staticmethod
    def parse_from_task(task):
        return Service(Service.extract_from_task(task))

    @staticmethod
    def extract_from_task(task):
        template = task['inputData']['service']
        return template if isinstance(template, dict) else eval(template)

    def to_dict(self):
        ifcs = []
        for ifc in self.devices:
            ifcs.append(dict(filter(lambda x: x[1], vars(ifc).items())))

        device = dict(filter(lambda x: x[1], vars(self).items()))
        device['devices'] = ifcs
        return device

    @staticmethod
    def parse_from_openconfig_network(node_id, nis, ph_ifcs, ve_ifcs):
        services = []
        for vl in nis['vlans']['vlan']:
            if 'name' in vl['config'] and vl['vlan-id'] != 1:
                service = {
                    "id": vl['config']['name'],
                    "devices": []
                }
                device = {
                    "interface": "UNKNOWN",
                    "id": node_id,
                    "vlan": vl['vlan-id']
                }

                ve_ifc = filter(lambda i: i.get('frinx-openconfig-vlan:routed-vlan', {}).get('config', {}).get('vlan', {}) == vl['vlan-id'], ve_ifcs)
                if len(ve_ifc) == 1:
                    device['ve_interface'] = ve_ifc[0]['name']
                    if 'subinterfaces' in ve_ifc[0]:
                        subinterface_ = ve_ifc[0]['subinterfaces']['subinterface'][0]
                        if 'frinx-openconfig-if-ip:ipv4' in subinterface_:
                            ip = subinterface_['frinx-openconfig-if-ip:ipv4']['addresses']['address'][0]
                            device['ip'] = ip['ip'] + "/" + str(ip['config']['prefix-length'])

                ph_ifc = filter(lambda i: Service.is_in_vlan(i, vl['vlan-id']), ph_ifcs)
                if len(ph_ifc) > 0:
                    for ifc in ph_ifc:
                        dev = copy.deepcopy(device)
                        vlan = ifc['frinx-openconfig-if-ethernet:ethernet']['frinx-openconfig-vlan:switched-vlan']['config']
                        if vlan['interface-mode'] == "ACCESS" or (vlan['interface-mode'] == "TRUNK" and 'native-vlan' in vlan):
                            dev['untagged'] = True

                        dev['interface'] = ifc['name']
                        vll_model.Service.set_attributes(nis, [ifc], dev)

                        service['devices'].append(dev)
                else:
                    service['devices'].append(device)

                services.append(Service(service))

        return services

    @staticmethod
    def is_in_vlan(vlans, id):
        vlan = vlans.get('frinx-openconfig-if-ethernet:ethernet', {}).get('frinx-openconfig-vlan:switched-vlan', {}).get('config', {})

        if 'access-vlan' in vlan and vlan['access-vlan'] == id:
            return True
        if 'native-vlan' in vlan and vlan['native-vlan'] == id:
            return True
        if 'trunk-vlans' in vlan:
            for tv in vlan['trunk-vlans']:
                if isinstance(tv, int):
                    if tv == id:
                        return True
                else:
                    tvs = tv.split('..')
                    if len(tvs) > 1 and int(tvs[0]) <= id <= int(tvs[1]):
                        return True
        return False
