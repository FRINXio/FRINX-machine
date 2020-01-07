#!/usr/bin/env python3

from collections import namedtuple
from sys import argv
import subprocess
import json


def main():

    DEVICE_DATA_CSV = argv[1]
    DEVICE_DATA_JSON = argv[2]
    HOSTNAME = 'elasticsearch'
    PORT = '9200'
    PATH = 'inventory-device/device/{{device_id}}'
    HOST = 'http://{}:{}/{}'.format(HOSTNAME, PORT, PATH)

    # definition of replacements in the DEVICE_DATA_JSON file
    json_replacements = {}

    with open(DEVICE_DATA_JSON) as json_file:
        device_import_json = json_file.read()

    with open(DEVICE_DATA_CSV) as data_file:
        all_device_data = data_file.readlines()

    # set header and remove space characters from all elements
    device_data_header = all_device_data[0].split(',')
    for i in enumerate(device_data_header):
        device_data_header[i[0]] = i[1].strip()

    # create a device_data_def suitable for both cli and netconf device types
    device_data_def = namedtuple('device_data_def', device_data_header)

    # create replacements
    for i in device_data_header:
        key = '{{%s}}' % i
        json_replacements[key] = i

    # skip the first line in csv
    all_device_data = all_device_data[1:]

    for device in all_device_data:

        # prepare a list with device data
        data_list = device.strip().split(',')

        # create a dict for easier use
        device_data_tuple = device_data_def(*data_list)
        device_data = dict(device_data_tuple._asdict())

        # copy the postman collections json
        device_json = device_import_json

        # replace the relevant parts for each device to create a JSON file
        # to send to elasticsearch
        for k in json_replacements.keys():
            val = json_replacements[k]
            device_json = device_json.replace(k, device_data[val])

        # preparation for subprocess execution
        device_json = json.loads(device_json)
        host = HOST
        host = host.replace('{{device_id}}', device_data['device_id'])
        args = ['curl', '-X', 'PUT',
                '-H', 'Content-Type: application/json',
                '-d', '{}'.format(json.dumps(device_json)),
                '{}'.format(host)
                ]

        subprocess.call(args)


if __name__ == '__main__':
    main()
