import json
import requests
import datetime
from .userAuth import *
from django.contrib.auth.models import User
from .models import Mouse


def get_token():

    login_url = 'https://labfolder.mpdl.mpg.de/api/v2/auth/login'
    headers = {'Content-Type': 'application/json'}
    r = requests.post(login_url,
                      data=json.dumps(credentials),
                      headers=headers)
    return r.json()['token']


def create_entry(token):

    entry_url = 'https://labfolder.mpdl.mpg.de/api/v2/entries'
    # token = get_token()
    headers = {'Content-Type': 'application/json', 'Authorization': 'Token '+token}
    data = {'title': 'bonDjango entry', 'project_id': project_id}

    r = requests.post(entry_url,
                      data=json.dumps(data),
                      headers=headers)
    return r


def create_table(form, log_type):

    element_url = 'https://labfolder.mpdl.mpg.de/api/v2/elements/table'
    token = get_token()
    headers = {'Content-Type': 'application/json', 'Authorization': 'Token ' + token}

    entry_id = check_new_entry(headers, token)

    # content = {"sheets": {"Sheet1": {"name": "Sheet1", "data":
    #      {"dataTable":{"0":{"0":{"value":5}},
    #      "8":{"5":{"value":4}},
    #      "9":{"3":{"value":"i"}}}}}}}

    content = {"sheets":
               {"Sheet1": {"name": "Sheet1",
                "data": {"dataTable": format_form(form)}}}}

    data = {'entry_id': entry_id, 'title': log_type, 'content': content}
    r = requests.post(element_url, data=json.dumps(data),
                      headers=headers)
    return r


def format_form(form):

    ready_form = {}
    for count, field in enumerate(form.fields):
        # assemble the dictionary entry
        # raw_data = form.cleaned_data[field]
        raw_data = getattr(form.data, field)
        if isinstance(raw_data, datetime.datetime):
            coerced_data = raw_data.strftime('%d/%m/%Y %H:%M:%S')
        elif isinstance(raw_data, datetime.date):
            coerced_data = raw_data.strftime('%d/%m/%Y')
        elif isinstance(raw_data, User):
            coerced_data = raw_data.username
        elif isinstance(raw_data, Mouse):
            coerced_data = raw_data.__str__()
        else:
            coerced_data = raw_data
        ready_form[count.__str__()] = {"0": {"value": field}, "1": {"value": coerced_data}}

    return ready_form


def check_new_entry(headers, token):

    entry_url = 'https://labfolder.mpdl.mpg.de/api/v2/entries'
    r = requests.get(entry_url + '?', headers=headers)

    if datetime.date.today() - datetime.datetime.strptime(
        json.loads(r.text)[-1]
       ['creation_date'], '%Y-%m-%dT%H:%M:%S.%f%z').date() > \
            datetime.timedelta(0):

        create_entry(token)
        r = requests.get(entry_url + '?', headers=headers)

    entry_id = json.loads(r.text)[-1]['id']

    return entry_id
# code for testing the system

# login_url = 'https://labfolder.mpdl.mpg.de/api/v2/auth/login'
# entry_url = 'https://labfolder.mpdl.mpg.de/api/v2/entries'
# element_url = 'https://labfolder.mpdl.mpg.de/api/v2/elements/table'
#
# headers = {'Content-Type': 'application/json'}
#
# r = requests.post(login_url,
#                   data=json.dumps(credentials),
#                   headers=headers)
#
# token = r.json()['token']
# print(r.status_code)
#
# headers = {'Content-Type': 'application/json;charset=UTF-8',
#            'Authorization': 'Token '+token}
#
# r = requests.get(entry_url+'?',
#                  headers=headers)
# a = json.loads(r.text)
# d = datetime.date.today() - \
#     datetime.datetime.strptime(
#         json.loads(r.text)[-1]
#         ['creation_date'], '%Y-%m-%dT%H:%M:%S.%f%z').date()
# print(r)

# r = requests.get(element_url+'/1dc7d109f18d873f869ac54948f97b46af595636',
#                  headers=headers)                                                   "9":{"3":{"value":"i"}}}}}}}

# content = {"sheets":{"Sheet1":{"name":"Sheet1","data":
#      {"dataTable":{"0":{"0":{"value":5}},
#      "8":{"5":{"value":4}},
#      "9":{"3":{"value":"i"}}}}}}}
#
# data = {'entry_id': '1921353', 'title': 'Django demo 2', 'content': content}
# r = requests.post(element_url, data=json.dumps(data),
#                   headers=headers)
#
# print(r.status_code)
# # json_data = json.loads(r.text)
# print(r.text)
