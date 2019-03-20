import inspect

from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from . import models
from . import views

schema_view = get_schema_view(title='bonDjango schema')

# create a list of the model names
model_list = inspect.getmembers(models, inspect.isclass)

print(model_list)

router = DefaultRouter()
# router.register(r'mouse', views.MouseViewSet)
router.register(r'mouse', views.MouseViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'window', views.WindowViewSet)
router.register(r'surgery', views.SurgeryViewSet)
router.register(r'cricket', views.CricketViewSet)
router.register(r'two_photon', views.TwoPhotonViewSet)
router.register(r'intrinsic_imaging', views.IntrinsicImagingViewSet)
router.register(r'vr_experiment', views.VRExperimentViewSet)



# [router.register(str())]

urlpatterns = [
    # OLD VIEW URLS
    # path('', views.index, name='index'),
    # path('log_view/<str:log_type>/', views.log_view, name='log view'),
    # path('query_manager/', views.query_manager, name='query manager'),
    # path('browse_models/<str:model_type>/', views.browse_models, name='browse models'),
    # path('pic_view/', views.pic_viewer, name='pic view'),
    # path('model_details/<str:model_type>/<str:target_model>/', views.model_details, name='model details'),
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),

    # TUTORIAL VIEWS

    # path('mice/<int:pk>/', views.MouseDetail.as_view(), name='mouse-detail'),
    # path('mice/', views.MouseList.as_view(), name='mice-list'),
    # path('users/', views.UserList.as_view(), name='user-list'),
    # path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    # path('', views.api_root),
    # path('<int:pk>/dob/', views.MouseDOB.as_view(), name='dob-list')

    path('', include(router.urls)),

    path('schema/', schema_view),
]

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
