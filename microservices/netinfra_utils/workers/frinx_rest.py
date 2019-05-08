import json

odl_url_base = "http://odl:8181/restconf"
elastic_url_base = "http://elasticsearch:9200"
conductor_url_base = "http://conductor-server:8080/api"

odl_credentials = ("admin", "admin")
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
