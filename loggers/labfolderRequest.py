import json
import requests
import datetime
from .userAuth import user_credentials
from django.contrib.auth.models import User
import pprint as pp

# define the urls to use
# define the login url to our labfolder
login_url = 'https://labfolder.mpdl.mpg.de/api/v2/auth/login'
# define the url to use to create the entry
entry_url = 'https://labfolder.mpdl.mpg.de/api/v2/entries'
# define the url to create elements, a table in this particular case
element_url = 'https://labfolder.mpdl.mpg.de/api/v2/elements/table'


def is_jsonable(x):
    """check if object is json serializable, taken from
    https://stackoverflow.com/questions/42033142/
    is-there-an-easy-way-to-check-if-an-object-is-json-serializable-in-python"""
    try:
        json.dumps(x)
        return True
    except TypeError:
        return False


def get_token(current_user):
    """get the auth token from labfolder"""
    # define the json header to send with the request
    headers = {'Content-Type': 'application/json'}
    # send the POST request asking for the token, using the imported credentials from file
    r = requests.post(login_url,
                      data=json.dumps(user_credentials[current_user]['credentials']),
                      headers=headers)
    # return said token
    return r.json()['token']


def create_entry(token, current_user):
    """create an entry using the token"""
    # define the corresponding headers, so json and the auth token
    headers = {'Content-Type': 'application/json', 'Authorization': 'Token '+token}
    # define the data to send, namely the title of the entry and the project_id imported from file
    data = {'title': 'bonDjango entry', 'project_id': user_credentials[current_user]['project_id']}
    # send the request
    r = requests.post(entry_url,
                      data=json.dumps(data),
                      headers=headers)
    return r


def create_table(form, log_type, current_user):
    """create a table inside a particular entry"""
    # get the actual auth token
    token = get_token(current_user)
    # assemble the header as above
    headers = {'Content-Type': 'application/json', 'Authorization': 'Token ' + token}
    # get the entry ID, either the one from today or a new one if one hasn't been created today
    entry_id = check_new_entry(headers, token, current_user)
    # assemble the json query with a properly formatted form based on the model
    content = {"sheets":
               {"Sheet1": {"name": "Sheet1",
                "data": {"dataTable": format_form(form)}}}}

    # define the data to be sent, i.e. entry id, model type and the content from above
    data = {'entry_id': entry_id, 'title': log_type, 'content': content}

    # send the request
    r = requests.post(element_url, data=json.dumps(data),
                      headers=headers)
    return r


def format_form(form):
    """given the data form, create a json formatted form to send in the request"""
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
        elif not is_jsonable(raw_data):
            coerced_data = raw_data.__str__()
        else:
            coerced_data = raw_data
        # add the data into the dict in the corresponding format
        ready_form[count.__str__()] = {"0": {"value": field}, "1": {"value": coerced_data}}
    # return the form
    return ready_form


def check_new_entry(headers, token, current_user):
    """check if there is a pre-existing entry today. if not, create one"""
    # get the current entries
    entries = get_project_entries(headers, current_user)

    # determine whether the latest entry is from today
    if (len(entries) == 0) or (datetime.date.today() - datetime.datetime.strptime(
       entries[-1]['creation_date'], '%Y-%m-%dT%H:%M:%S.%f%z').date() > datetime.timedelta(0)):
        # if not, create a new one
        create_entry(token, current_user)
        # update the list of entries
        entries = get_project_entries(headers, current_user)
    # return the id of either the new one or the latest one
    entry_id = entries[-1]['id']

    return entry_id


def get_project_entries(headers, current_user):
    """query labfolder for the entries belonging to this project"""
    # send a request to get a list of the current entries

    # initialize the page counter
    page_counter = 20
    # initialize output
    output = json.loads(requests.get(entry_url + '?', headers=headers).text)
    # initialize the list of entries
    entries = output
    # run until there are no more entries
    while len(output) > 0:
        r = requests.get(entry_url + '?offset=' + str(page_counter), headers=headers)
        # get the entries as a list
        output = json.loads(r.text)
        # append to the main list
        entries += output
        # update the counter
        page_counter += 20
    # get the target project id
    project_id = user_credentials[current_user]['project_id']
    # filter only for the ones in the target project
    entries = [el for el in entries if project_id in el.values()]
    return entries

