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

# set up the url router
router = DefaultRouter()
# register the different models with their viewsets
router.register(r'mouse', views.MouseViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'window', views.WindowViewSet)
router.register(r'surgery', views.SurgeryViewSet)
router.register(r'cricket', views.CricketViewSet)
router.register(r'two_photon', views.TwoPhotonViewSet)
router.register(r'intrinsic_imaging', views.IntrinsicImagingViewSet)
router.register(r'vr_experiment', views.VRExperimentViewSet)

# generate the actual list of urls produced by the router plus the schema view
urlpatterns = [

    path('', include(router.urls)),

    path('schema/', schema_view),
]
# add the api login to the urls
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

