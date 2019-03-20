import json
import requests
import datetime
from .userAuth import *
from django.contrib.auth.models import User
from .models import Mouse


# get the auth token from labfolder
def get_token():
    # define the login url to our labfolder
    login_url = 'https://labfolder.mpdl.mpg.de/api/v2/auth/login'
    # define the json header to send with the request
    headers = {'Content-Type': 'application/json'}
    # send the POST request asking for the token, using the imported credentials from file
    r = requests.post(login_url,
                      data=json.dumps(credentials),
                      headers=headers)
    # return said token
    return r.json()['token']


# create an entry using the token
def create_entry(token):
    # define the url to use to create the entry
    entry_url = 'https://labfolder.mpdl.mpg.de/api/v2/entries'
    # define the corresponding headers, so json and the auth token
    headers = {'Content-Type': 'application/json', 'Authorization': 'Token '+token}
    # define the data to send, namely the title of the entry and the project_id imported from file
    data = {'title': 'bonDjango entry', 'project_id': project_id}
    # send the request
    r = requests.post(entry_url,
                      data=json.dumps(data),
                      headers=headers)
    return r


# create a table inside a particular entry
def create_table(form, log_type):
    # define the url to create elements, a table in this particular case
    element_url = 'https://labfolder.mpdl.mpg.de/api/v2/elements/table'
    # get the actual auth token
    token = get_token()
    # assemble the header as above
    headers = {'Content-Type': 'application/json', 'Authorization': 'Token ' + token}
    # get the entry ID, either the one from today or a new one if one hasn't been created today
    entry_id = check_new_entry(headers, token)
    # assemble the json query with a properly formatted form based on the model
    # TODO: there's definitely a better way of doing this with json, need to learn
    content = {"sheets":
               {"Sheet1": {"name": "Sheet1",
                "data": {"dataTable": format_form(form)}}}}
    # define the data to be sent, i.e. entry id, model type and the content from above
    data = {'entry_id': entry_id, 'title': log_type, 'content': content}
    # send the request
    r = requests.post(element_url, data=json.dumps(data),
                      headers=headers)
    return r


# given the data form, create a json formatted form to send in the request
def format_form(form):
    # allocate a dict for the output
    ready_form = {}
    # for all of the fields in the form supplied
    for count, field in enumerate(form.fields):
        # assemble the dictionary entry
        raw_data = getattr(form.data, field)
        # depending on the instance type, format appropriately into string
        # TODO: figure out how to decode choice fields in case it's special
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
        # add the data into the dict in the corresponding format
        ready_form[count.__str__()] = {"0": {"value": field}, "1": {"value": coerced_data}}
    # return the form
    return ready_form


# check if there is a pre-existing entry today. if not, create one
def check_new_entry(headers, token):
    # define the entry url
    entry_url = 'https://lbfolder.mpdl.mpg.de/api/v2/entries'
    # send a request to get a list of the current entries
    r = requests.get(entry_url + '?', headers=headers)
    # determine whether the latest entry is from today
    if datetime.date.today() - datetime.datetime.strptime(
        json.loads(r.text)[-1]
       ['creation_date'], '%Y-%m-%dT%H:%M:%S.%f%z').date() > \
            datetime.timedelta(0):
        # if not, create a new one
        create_entry(token)
        r = requests.get(entry_url + '?', headers=headers)
    # return the id of either the new one or the latest one
    entry_id = json.loads(r.text)[-1]['id']

    return entry_id

