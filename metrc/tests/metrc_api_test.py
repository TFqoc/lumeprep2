import pprint
import requests
import json
from datetime import datetime, time
from dateutil import tz
from requests.auth import HTTPBasicAuth
REQUEST_TIMEOUT = 60

software_api_key = 'lfnVBCpoe2-beRSQseEwSWqMWkxQMZtq6oiQ9N1ttEZt2c2X'
user_api_key = 'FusVbe4Yv6W1DGNuxKNhByXU6RO6jSUPcbRCoRDD98VNXc4D'
pp = pprint.PrettyPrinter(indent=4)

KNOW_ERROR_CODES = {
    401: 'Unauthorized ! Invalid or no authentication provided.',
    403: 'Forbidden ! The authenticated user does not have access to the requested resource.',
    404: 'Not Found ! The requested resource could not be found (incorrect or invalid URI).',
    429: 'Too Many Requests ! The limit of API calls allowed has been exceeded. Please pace the usage rate of the API more apart.',
    500: 'Internal Server Error ! An error has occurred while executing your request. The error message is typically included in the body of the response.',
}

def fetch(http_method, service_endpoint,  headers=None, params=None, data=None):
    if params == None:
        params = {}
    if data == None:
        data = {}
    if not service_endpoint:
        return False
    if headers == None:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    # base_url = 'https://api-ca.metrc.com'
    base_url = 'https://sandbox-api-ca.metrc.com'
    service_url = '{}{}'.format(base_url, service_endpoint)
    basic_auth=HTTPBasicAuth(software_api_key, user_api_key)
    resp = {}
    try:
        resp = requests.request (http_method, service_url, headers=headers, auth=basic_auth, params=params, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
        print (resp.url)
    except requests.exceptions.Timeout as ex:
        raise ex
    except Exception as ex:
        raise ex
    # This part for clean error habndling and logging.
    # https://api-ca.metrc.com/Documentation#getting-started_server_responses
    if resp.status_code != 200:
        level = 'warning'
        if resp.status_code == 400:
            json_resp = resp.json()
            message =  '.\n'.join([json_line.get('message') for json_line in json_resp])
        elif resp.status_code in KNOW_ERROR_CODES:
            message = KNOW_ERROR_CODES[resp.status_code]
        else:
            message = 'Unepxected error ! please report this to your administrator.'
            level = 'error'
        print("{} : {} {} {} {}".format(level, http_method, service_url, resp.status_code, message))
        return {}
    else:
        try:
            return resp.json()
        except:
            return {}

# pp.pprint(fetch('GET', '/items/v1/categories'))
# pp.pprint(fetch('GET', '/strains/v1/active', params={'licenseNumber': 'A12-0000015-LIC'}))
# pp.pprint(fetch('GET', '/strains/v1/active', params={'licenseNumber': 'CDPH-0000003'}))
strain_val =  {
    "Id": 33609,
    "Name": "OdooTest: TN Orange Dream",
    "TestingStatus": "InHouse",
    "ThcLevel": 0.1865,
    "CbdLevel": 0.1075,
    "IndicaPercentage": 25.0,
    "SativaPercentage": 75.0
}
pp.pprint(fetch('POST', '/strains/v1/update', params={'licenseNumber': 'CDPH-0000003'}, data=[strain_val]))
# pp.pprint(fetch('POST', '/strains/v1/create', params={'licenseNumber': 'CDPH-0000003'}, data=[strain_val]))
# pp.pprint(fetch('POST', '/strains/v1/create', params={'licenseNumber': 'A12-0000015-LIC'}, data=[strain_val]))
