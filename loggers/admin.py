import inspect
from django.contrib import admin
from . import models

# generate a list of the model classes
classMembers = inspect.getmembers(models, inspect.isclass)
classList = [model[0] for model in classMembers]

# eliminate User from the list (needed for the profile addition)
classList.remove('User')

# register them with the project
for model in classList:
    admin.site.register(getattr(models, model))
