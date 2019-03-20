import inspect

from django.contrib import admin

from . import models

# Register your models here.

classMembers = inspect.getmembers(models, inspect.isclass)

classList = [model[0] for model in classMembers]

for model in classList:
    admin.site.register(getattr(models, model))
