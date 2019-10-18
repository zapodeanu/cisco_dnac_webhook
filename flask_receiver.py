#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Cisco DNA Center Client Information using the MAC Address

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
from flask import Flask, request, abort
import sys
import json
import datetime
import os
import time
from flask_basicauth import BasicAuth

import pagerduty_apis
import jira_apis
import webex_teams_apis

from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings

from config import WEBEX_TEAMS_AUTH, WEBEX_TEAMS_URL, WEBEX_TEAMS_ROOM
from config import WEBHOOK_USERNAME, WEBHOOK_PASSWORD, WEBHOOK_URL
from config import DNAC_URL, SDWAN_URL
from config import PAGERDUTY_EVENTS_URL, PAGERDUTY_INTEGRATION_KEY
from config import JIRA_URL, JIRA_API_KEY, JIRA_EMAIL, JIRA_PROJECT

os.environ['TZ'] = 'America/Los_Angeles'  # define the timezone for PST
time.tzset()  # adjust the timezone, more info https://help.pythonanywhere.com/pages/SettingTheTimezone/

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings


app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = WEBHOOK_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = WEBHOOK_PASSWORD
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)


@app.route('/')  # create a page for testing the flask framework
@basic_auth.required
def index():
    return '<h1>Flask Receiver App is Up!</h1>', 200


@app.route('/dashboard')  # create a page for the dashboard
def dashboard():
    return '<h1>Dashboard To DO!</h1>', 200


@app.route('/webhook', methods=['POST'])  # create a route for /webhook, method POST
@basic_auth.required
def webhook():
    if request.method == 'POST':
        print('Webhook Received')
        request_json = request.json

        # print the received notification
        print('Payload: ')
        pprint(request_json)

        # save as a file, create new file if not existing, append to existing file, full details of each notification
        with open('all_webhooks_detailed.log', 'a') as filehandle:
            filehandle.write('%s\n' % json.dumps(request_json))
        try:
            if 'NETWORK-' in request_json['eventId']:  # this will select the Cisco DNA Center notifications
                dnac_notification = request_json

                # save all info to variables, prepare to save to file
                severity = str(dnac_notification['severity'])
                category = dnac_notification['category']
                timestamp = str(datetime.datetime.fromtimestamp(int(dnac_notification['timestamp'] / 1000)).strftime(
                    '%Y-%m-%d %H:%M:%S'))
                issue_name = dnac_notification['details']['Assurance Issue Name']
                issue_description = dnac_notification['details']['Assurance Issue Details']
                issue_status = dnac_notification['details']['Assurance Issue Status']
                url = DNAC_URL + '/dna/assurance/issueDetails?issueId=' + dnac_notification['instanceId']

                # create the summary DNAC log
                new_info = {'severity': severity, 'category': category, 'timestamp': dnac_notification['timestamp']}
                new_info.update({'Assurance Issue Name': issue_name, 'Assurance Issue Details': issue_description})
                new_info.update({'Assurance Issue Status': issue_status, 'Assurance Issue URL': url})

                # append, or create, the dnac_webhooks.log - Cisco DNA C summary logs
                with open('dnac_webhooks.log', 'a') as filehandle:
                    filehandle.write('%s\n' % json.dumps(new_info))

                # append, or create, the all_webhooks.log - Summary all logs
                with open('all_webhooks.log', 'a') as filehandle:
                    filehandle.write('%s\n' % json.dumps(new_info))

                # construct the team message
                teams_message = 'Severity:       ' + severity
                teams_message += '\nCategory:       ' + category
                teams_message += '\nTimestamp:      ' + str(timestamp)
                teams_message += '\nIssue Name:     ' + issue_name
                teams_message += '\nIssue Description:  ' + issue_description
                teams_message += '\nIssue Status:   ' + issue_status
                print('New DNAC Webex Teams_Message\n', teams_message)

                teams_message_title = 'Cisco DNA Center Notification'

                # create PagerDuty incident if status is active
                # format message using the Common Event Format (PD-CEF)
                if issue_status != 'resolved':
                    summary = issue_name
                    source = teams_message_title
                    component = issue_description
                    if severity == '1':
                        sev = 'critical'
                    else:
                        sev = 'warning'
                    group = 'Network'
                    # convert time from epoch to iso 8601
                    time_iso = datetime.datetime.fromtimestamp(int(dnac_notification['timestamp'] / 1000)).isoformat()
                    pagerduty_apis.trigger_incident(summary, source, component, sev, time_iso, group)

                # create Jira Issue
                jira_project = JIRA_PROJECT
                jira_component = '10016'  # Component id for Cisco DNA Center Notification, as created in Jira
                jira_apis.create_customer_issue(jira_project, jira_component, issue_name, issue_description, severity,
                                                JIRA_EMAIL)

                # post markdown message in teams space, with title of the message
                webex_teams_apis.post_space_markdown_message(WEBEX_TEAMS_ROOM, teams_message_title)

                # post message in teams space
                webex_teams_apis.post_space_message(WEBEX_TEAMS_ROOM, teams_message)
                teams_message_url = 'Issue Details:  Click Here\n'

                # post message in teams space, with url for the issue
                webex_teams_apis.post_space_url_message(WEBEX_TEAMS_ROOM, teams_message_url, url)

        finally:
            pass

        try:
            if 'values' in request_json:
                sdwan_notification = request_json

                # save all info to variables, prepare to save to file
                severity = sdwan_notification['severity']
                timestamp = str(datetime.datetime.fromtimestamp(int(sdwan_notification['entry_time'] / 1000)).strftime(
                    '%Y-%m-%d %H:%M:%S'))
                try:
                    site_id = str(sdwan_notification['values'][0]['site-id'])
                finally:
                    site_id = ' '
                system_ip = sdwan_notification['values'][0]['system-ip']
                host_name = sdwan_notification['values'][0]['host-name']
                message = sdwan_notification['message']
                issue_status = str(sdwan_notification['active'])
                url = SDWAN_URL + '/index.html#/app/monitor/alarms/details/' + sdwan_notification['uuid']

                # create the summary SD-WAN log - Cisco SD-WAN summary logs
                new_info = {'severity': severity, 'entry_time': sdwan_notification['entry_time']}
                new_info.update({'site-id': site_id, 'system_ip': system_ip, 'host-name': host_name})
                new_info.update({'message': message, 'active': issue_status, 'alarm details': url})

                # append, or create, the sdwan_webhooks.log
                with open('sdwan_webhooks.log', 'a') as filehandle:
                    filehandle.write('%s\n' % json.dumps(new_info))

                # append, or create, the all_webhooks.log - Summary all logs
                with open('all_webhooks.log', 'a') as filehandle:
                    filehandle.write('%s\n' % json.dumps(new_info))

                # construct the team message
                teams_message = 'Severity:           ' + severity
                teams_message += '\nTimestamp:          ' + timestamp
                teams_message += '\nSite Id:            ' + site_id
                teams_message += '\nSystem IP:          ' + system_ip
                teams_message += '\nHost Name:          ' + host_name
                teams_message += '\nIssue Description:  ' + message
                teams_message += '\nIssue Status:       ' + issue_status
                print('New SD-WAN Webex Teams_Message\n', teams_message)

                teams_message_title = 'Cisco SD-WAN Notification'

                # create PagerDuty incident
                # format message using the Common Event Format (PD-CEF)
                summary = host_name
                source = teams_message_title
                component = message
                if severity == '1':
                    sev = 'critical'
                else:
                    sev = 'warning'
                group = 'WAN'
                # convert time from epoch to iso 8601
                time_iso = datetime.datetime.fromtimestamp(int(sdwan_notification['timestamp'] / 1000)).isoformat()
                pagerduty_apis.trigger_incident(summary, source, component, sev, time_iso, group)

                # post markdown message in teams space, with title of the message
                webex_teams_apis.post_space_markdown_message(WEBEX_TEAMS_ROOM, teams_message_title)

                # post message in teams space
                webex_teams_apis.post_space_message(WEBEX_TEAMS_ROOM, teams_message)

                # post message in teams space, with url for the issue
                teams_message_url = 'Issue Details:  Click Here\n'
                webex_teams_apis.post_space_url_message(WEBEX_TEAMS_ROOM, teams_message_url, url)

        finally:
            pass
        return {'response': 'Notification Received'}, 200
    else:
        abort(400)


def pprint(json_data):
    """
    Pretty print JSON formatted data
    :param json_data:
    :return:
    """
    print(json.dumps(json_data, indent=4, separators=(' , ', ' : ')))


if __name__ == '__main__':
    app.run(debug=True)
