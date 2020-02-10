import json
from http.cookies import SimpleCookie

odl_url_base = "http://uniconfig:8181/rests"
elastic_url_base = "http://elasticsearch:9200"
conductor_url_base = "http://conductor-server:8080/api"

# username = ''
# password = ''
#
# with open('/opt/odl_pass/db-credentials.txt', 'r') as f:
#     lines = f.readlines()
#     username = lines[0].split(':')[1].rstrip('\n')
#     password = lines[1].split(':')[1].rstrip('\n')

odl_credentials = ('admin', 'admin')
# odl_credentials = (username, password)
odl_headers = {"Content-Type": "application/json"}
elastic_headers = {"Content-Type": "application/json"}


def parse_response(r):
    decode = r.content.decode('utf8')
    try:
        response_json = json.loads(decode if decode else "{}")
    except ValueError as e:
        response_json = json.loads("{}")

    response_code = r.status_code
    return response_code, response_json


def parse_header(r):
    cookie = SimpleCookie()
    cookie.load(r.cookies)
    cookies = {}
    for key, val in cookie.items():
        if key == "UNICONFIGTXID":
            cookies[key] = val.value
    return cookies


def add_uniconfig_tx_cookie(uniconfig_tx_id):
    header = odl_headers
    if uniconfig_tx_id and uniconfig_tx_id != "":
        header["Cookie"] = "UNICONFIGTXID=" + uniconfig_tx_id
    return header
