import inspect
from django.contrib import admin
from . import models

# generate a list of the model classes
classMembers = inspect.getmembers(models, inspect.isclass)
classList = [model[0] for model in classMembers]

# register them with the project
for model in classList:
    admin.site.register(getattr(models, model))
