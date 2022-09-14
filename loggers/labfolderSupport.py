import json
import requests
import datetime
import os
import csv
from labfolderRequest import get_project_entries, get_token, get_signatures
from userAuth import paths
from pprint import pprint


# define the urls to use
# define the login url to our labfolder
login_url = 'https://labfolder.mpdl.mpg.de/api/v2/auth/login'
# define the url to use to create the entry
entry_url = 'https://labfolder.mpdl.mpg.de/api/v2/entries'
# define the url to create elements, a table in this particular case
element_url = 'https://labfolder.mpdl.mpg.de/api/v2/elements/table'

# define the user to use for prototyping
target_user = 'drguggiana'
# get the token
token = get_token(target_user)
# assemble the header
headers = {'Content-Type': 'application/json', 'Authorization': 'Token ' + token}
# get all the current entries
entries = get_project_entries(headers, target_user)
# compile the element ids
current_ids = []
for el in entries:
    for el2 in el['elements']:
        current_ids.append(el2['id'])
# get the already archived ones

# check if the file exists
if os.path.exists(paths['labfolder_dump']):
    # load the element ids
    # saved_ids = []
    with open(paths['labfolder_dump'], 'r', newline='') as f:
        saved_ids = csv.reader(f, delimiter=',')
else:
    # create the file
    with open(paths['labfolder_dump'], 'w', newline=''):
        pass
    # generate an empty list of ids
    saved_ids = []

# get the signature workflows
signatures = get_signatures(headers, target_user)
# compare them and determine which entries to exclude
exclude_entries = current_ids[:, 0]
# update the dump file

pprint(entries)
