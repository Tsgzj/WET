# -*- coding: utf-8 -*-
"""
Yelp Fusion API code sample.
This program demonstrates the capability of the Yelp Fusion API
by using the Search API to query for businesses by a search term and location,
and the Business API to query additional information about the top result
from the search query.
Please refer to http://www.yelp.com/developers/v3/documentation for the API
documentation.

This program requires the Python requests library, which you can install via:
`pip install -r requirements.txt`.

Modified:
Please modify conf.json to customize


Sample usage of the program:
`python WtET.py`
"""

from __future__ import print_function

import argparse
import json
import pprint
import requests
import sys
import urllib
import json
import random


# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


# OAuth credential placeholders that must be filled in by users.
# You can find them on
# https://www.yelp.com/developers/v3/manage_app
# Reading from config.json
with open('conf.json') as data:
    CONFIG = json.load(data)
CLIENT_ID = CONFIG['client_id']
CLIENT_SECRET = CONFIG['client_secret']
TERM = CONFIG['term']
REPEAT = CONFIG['repeat']
LIMIT = CONFIG['limit']

with open('history') as hdata:
    HISTORY = json.load(hdata)


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'

def obtain_bearer_token(host, path):
    """Given a bearer token, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        str: OAuth bearer token, obtained using client_id and client_secret.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    assert CLIENT_ID, "Please supply your client_id."
    assert CLIENT_SECRET, "Please supply your client_secret."
    data = urlencode({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': GRANT_TYPE,
    })
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    response = requests.request('POST', url, data=data, headers=headers)
    bearer_token = response.json()['access_token']
    return bearer_token


def request(host, path, bearer_token, url_params=None):
    """Given a bearer token, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        bearer_token (str): OAuth bearer token, obtained using client_id and client_secret.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % bearer_token,
    }

    # print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search(bearer_token, term):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """
    url_params = dict()
    for key in term:
        url_params[key] = term[key]

    all_bus = dict()
    times = LIMIT/50
    if LIMIT > 50:
        for i in range(times):
            url_params['limit'] = 50
            url_params['offset'] = 50 * i
            res = request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)
            for b in res.get('businesses'):
                b_info = list()
                b_info.append(b.get('rating'))
                b_info.append(b.get('categories')[0].get('title'))
                b_info.append(b.get('location').get('display_address'))
                all_bus[b.get('name')] = b_info

    # last times
    url_params['limit'] = LIMIT % 50
    url_params['offset'] = 50 * times
    res = request(API_HOST, SEARCH_PATH, bearer_token, url_params=url_params)
    for b in res.get('businesses'):
        b_info = list()
        b_info.append(b.get('rating'))
        b_info.append(b.get('categories')[0].get('title'))
        b_info.append(b.get('location').get('display_address'))
        all_bus[b.get('name')] = b_info

    return all_bus

def query_api(term):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    bearer_token = obtain_bearer_token(API_HOST, TOKEN_PATH)
    return search(bearer_token, term)

def main():
    try:
        potential = query_api(TERM)
    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )

    while True:
        today = random.choice(potential.keys())
        if today not in HISTORY:
            break

    info = potential.get(today)
    HISTORY.append(today)
    if (len(HISTORY) > REPEAT):
        HISTORY.pop(0)

    with open('history', 'w') as hdata:
        json.dump(HISTORY, hdata)
    print("I suggest eating a(an) {2} restaurant called {0} which has a rating of {1}/5. The address is {3}".format(today, info[0], info[1], " ".join(info[2])))

if __name__ == '__main__':
    main()
