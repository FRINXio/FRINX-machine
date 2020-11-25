from __future__ import print_function

import json
import copy
from string import Template

import requests

from frinx_rest import parse_response


# Example 1: simple GET request returning HTML
# {
#     "name": "HTTP_task",
#     "taskReferenceName": "google_worker",
#     "type": "SIMPLE",
#     "inputParameters": {
#         "http_request": {
#             "uri": "http://www.google.com",
#             "method": "GET",
#             "timeout": 60,
#             "verifyCertificate": true
#         }
#     }
# }
# Example 2: Get request to uniconfig providing basic auth
# {
#     "name": "HTTP_task",
#     "taskReferenceName": "topo",
#     "type": "SIMPLE",
#     "inputParameters": {
#         "http_request": {
#             "uri": "http://uniconfig:8181/rests/data/network-topology:network-topology?content=nonconfig",
#             "method": "GET",
#             "headers": {
#                 "ContentType": "application/json",
#                 "Accept": "application/json"
#             },
#             "basicAuth": {
#                 "username": "admin",
#                 "password": "admin"
#             },
#             "timeout": 60,
#             "verifyCertificate": true
#         }
#     }
# }
# Example 3: sequence of requests carrying over cookies from 1st to 2nd
#            also providing credentials as x-www-form-urlencoded
#            also turning off certificate validation
# {
#     "name": "HTTP_task",
#     "taskReferenceName": "login",
#     "type": "SIMPLE",
#     "inputParameters": {
#         "http_request": {
#             "uri": "https://1.1.1.1:43301/login",
#             "method": "POST",
#             "contentType": "application/x-www-form-urlencoded",
#             "body": "username=admin&password=passwd",
#             "headers": {
#                 "a": "test"
#             },
#             "timeout": 60,
#             "verifyCertificate": false
#         }
#     }
# },
# {
#     "name": "HTTP_task",
#     "taskReferenceName": "get",
#     "type": "SIMPLE",
#     "inputParameters": {
#         "http_request": {
#             "uri": "https://1.1.1.1:43301/rest/v1/system/",
#             "method": "GET",
#             "contentType": "application/json",
#             "timeout": 60,
#             "verifyCertificate": false,
#             "cookies" : "${login.output.cookies}"
#         }
#     }
# }
def http_task(task):
    http_request = task['inputData']['http_request'] if 'http_request' in task['inputData'] else {}

    uri = http_request["uri"]
    if uri is None:
        return {'status': 'FAILED', 'output': {},
                'logs': ["URI is empty"]}

    method = http_request["method"]
    if method is None or method.upper() not in ["GET", "PUT", "POST", "DELETE", "HEAD", "PATCH"]:
        return {'status': 'FAILED', 'output': {'url': uri},
                'logs': ["Method %s unsupported for %s" % (method, uri)]}

    headers = {}
    if 'contentType' in http_request:
        headers['Content-Type'] = http_request['contentType']
    if 'accept' in http_request:
        headers['Accept'] = http_request['accept']

    additional_headers = http_request['headers'] if 'headers' in http_request else {}
    headers.update(additional_headers)

    body = http_request['body'] if 'body' in http_request else ""

    timeout = http_request['timeout'] if 'timeout' in http_request else 60.0
    verify_cert = http_request['verifyCertificate'] if 'verifyCertificate' in http_request else True

    cookies = http_request['cookies'] if 'cookies' in http_request else {}

    auth = None
    if 'basicAuth' in http_request:
        if 'username' not in http_request['basicAuth']:
            return {'status': 'FAILED', 'output': {'url': uri},
                    'logs': ["Basic auth without username for %s" % uri]}
        if 'password' not in http_request['basicAuth']:
            return {'status': 'FAILED', 'output': {'url': uri},
                    'logs': ["Basic auth without password for %s" % uri]}
        auth = requests.auth.HTTPBasicAuth(http_request['basicAuth']['username'],
                                           http_request['basicAuth']['password'])

    r = requests.request(method, uri,
                         headers=headers,
                         data=body,
                         cookies=cookies,
                         timeout=timeout,
                         auth=auth,
                         verify=verify_cert)

    if 400 <= r.status_code < 600:
        return {'status': 'FAILED', 'output': {'statusCode': r.status_code,
                                               'response': {'headers': dict(r.headers)},
                                               'body': r.content.decode("utf-8", "ignore")},
                'logs': ["HTTP %s request to %s failed. Headers: %s"
                         % (r.request.method, r.request.url, r.request.headers.items())]}

    return {'status': 'COMPLETED', 'output': {'statusCode': r.status_code,
                                              'response': {'headers': dict(r.headers)},
                                              'body': r.content.decode("utf-8", "ignore"),
                                              'cookies': requests.utils.dict_from_cookiejar(r.cookies)},
            'logs': ["HTTP %s request to %s succeeded. Headers: %s"
                     % (r.request.method, r.request.url, r.request.headers.items())]}


def start(cc):
    print('Starting HTTP workers')

    cc.register('HTTP_task', {
        "name": "HTTP_task",
        "description": "{\"description\": \"Generic http task\", \"labels\": [\"BASICS\",\"HTTP\"]}",
        "retryCount": 0,
        "ownerEmail":"example@example.com",
        "timeoutSeconds": 360,
        "timeoutPolicy": "TIME_OUT_WF",
        "retryLogic": "FIXED",
        "retryDelaySeconds": 0,
        "responseTimeoutSeconds": 360,
        "inputKeys": [
            "http_request"
        ],
        "outputKeys": [
            "response",
            "body",
            "statusCode",
            "cookies"
        ]
    })
    cc.start('HTTP_task', http_task, False)
