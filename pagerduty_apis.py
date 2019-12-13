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

from config import PAGERDUTY_INTEGRATION_KEY, PAGERDUTY_EVENTS_URL

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings


def trigger_incident(summary, source, component, severity, timestamp, group):
    """
    This function will send a PagerDuty notification using the Common Event Format (PD-CEF)
    :param summary: A high-level, text summary message of the event. Will be used to construct an alert's description
    :param source: Specific human-readable unique identifier, such as a hostname, for the system having the problem.
    :param component: The part or component of the affected system that is broken.
    :param severity: must be one of: Info, Warning, Error, Critical.
     How impacted the affected system is. Displayed to users in lists and influences the priority of any created incidents.
    :param timestamp: IOS 8601 timestamp
    :param group: A cluster or grouping of sources. For example, {Network} or {WAN}
    :return:
    """
    # Triggers a PagerDuty incident without a previously generated incident key
    # Uses Events V2 API - documentation: https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2
    # format message using the Common Event Format (PD-CEF)

    payload = {  # Payload is built with the least amount of fields required to trigger an incident
        'routing_key': PAGERDUTY_INTEGRATION_KEY,
        'event_action': 'trigger',
        'payload': {
            'summary': summary,
            'source': source,
            'component': component,
            'severity': severity,
            'timestamp': timestamp,
            'group': group
        }
    }

    url = PAGERDUTY_EVENTS_URL
    header = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=header)

    if response.json()['status'] == 'success':
        print('Incident created with with dedup key (also known as incident / alert key) of ' + '"' + response.json()[
            'dedup_key'] + '"')
    else:
        print(response.text)  # print error message if not successful
