#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""



Copyright (c) 2019 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

"""

__author__ = "Gabriel Zapodeanu TME, ENB"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

import requests
import urllib3
import json

from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings

from config import WEBEX_TEAMS_URL, WEBEX_TEAMS_AUTH, WEBEX_TEAMS_ROOM

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings


def get_space_id(space_name):
    """
    This function will find the Webex Teams space id based on the {space_name}
    Call to Webex Teams - /rooms
    :param space_name: The Webex Teams space name
    :return: the Webex Teams space Id
    """
    payload = {'title': space_name}
    space_number = None
    url = WEBEX_TEAMS_URL + '/rooms'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    space_response = requests.get(url, data=json.dumps(payload), headers=header, verify=False)
    space_list_json = space_response.json()
    space_list = space_list_json['items']
    for spaces in space_list:
        if spaces['title'] == space_name:
            space_number = spaces['id']
    return space_number


def post_space_message(space_name, message):
    """
    This function will post the {message} to the Webex Teams space with the {space_name}
    Call to function get_space_id(space_name) to find the space_id
    Followed by API call /messages
    :param space_name: the Webex Teams space name
    :param message: the text of the message to be posted in the space
    :return: none
    """
    space_id = get_space_id(space_name)
    payload = {'roomId': space_id, 'text': message}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    requests.post(url, data=json.dumps(payload), headers=header, verify=False)


def post_space_markdown_message(space_name, message):
    """
    This function will post a markdown {message} to the Webex Teams space with the {space_name}
    Call to function get_space_id(space_name) to find the space_id
    Followed by API call /messages
    :param space_name: the Webex Teams space name
    :param message: the text of the markdown message to be posted in the space
    :return: none
    """
    space_id = get_space_id(space_name)
    payload = {'roomId': space_id, 'markdown': ('**' + message + '**')}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    requests.post(url, data=json.dumps(payload), headers=header, verify=False)


def post_space_url_message(space_name, message, url):
    """
    This function will post an URL to the Webex Teams space with the {space_name}
    Call to function get_space_id(space_name) to find the space_id
    Followed by API call /messages
    :param space_name: the Webex Teams space name
    :param message: the text of the markdown message to be posted in the space
    :param url: URL for the text message
    :return: none
    """
    space_id = get_space_id(space_name)
    payload = {'roomId': space_id, 'markdown': ('[' + message + '](' + url + ')')}
    url = WEBEX_TEAMS_URL + '/messages'
    header = {'content-type': 'application/json', 'authorization': WEBEX_TEAMS_AUTH}
    requests.post(url, data=json.dumps(payload), headers=header, verify=False)
