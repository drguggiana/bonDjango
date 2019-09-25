import inspect

from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from . import models
from . import views

# make the schema view of the whole project
schema_view = get_schema_view(title='bonDjango schema')

# create a list of the model names
model_list = inspect.getmembers(models, inspect.isclass)
# TODO: have actual names (maybe from string method) instead of URLs on the links
# set up the url router
router = DefaultRouter()

# generate a list of the model classes
classMembers = inspect.getmembers(models, inspect.isclass)
classList = [model[0] for model in classMembers]

# register their viewsets with the router
for model in classList:
    router.register(views.convert(model), eval('views.'+model+'ViewSet'))

# register the user model viewset too
router.register(r'user', views.UserViewSet)
router.register(r'group', views.GroupViewSet)

# generate the actual list of urls produced by the router plus the schema view
urlpatterns = [

    path('', include(router.urls)),

    path('schema/', schema_view),
]
# add the api login to the urls
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

