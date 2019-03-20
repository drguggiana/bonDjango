# imports required for the display of tif images on chrome (since it's not supported natively).
# Found the solution online
import base64
import datetime
import inspect
import pprint
import re
from io import BytesIO
from PIL import Image

# used to make paths below
from os.path import join

# django imports for the scheduler and direct linking
from django.core import management
from django.http import HttpResponseRedirect

# DRF specific requirements
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# imports from the same project
from . import labfolderRequest
from .forms import form_dict
from .paths import backup_path
from .permissions import IsOwnerOrReadOnly
from .serializers import *


# snippet to convert camel case to snake case via regex
def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# view to generate labfolder entry, see dedicated file
def labfolder_entry(instance):
    # get the target model from the request
    target_model = convert(type(instance.get_object()).__name__)
    # create a form from the target model
    form = form_dict[target_model](instance.get_object())
    # pass the form and model to create the labfolder entry
    labfolderRequest.create_table(form, target_model)


# view to show images in the database, ideally after search query
# TODO: create a thumbnail version for browsing that then loads the full res image upon clicking
def pic_display(instance, request):

    # # debugging code
    # pp = pprint.PrettyPrinter()
    # target = inspect.getmembers(instance)
    # pp.pprint([f[0] for f in target])

    # get the object data
    data = [instance.get_object()]

    # generate a url for a JPEG version of the TIF image
    def generate_image_url(image_path):

        # snippet taken online to generate the url based on loading the image and converting to JPEG
        # TODO: find the source
        output = BytesIO()
        img = Image.open(image_path)
        img.save(output, format='JPEG')
        im_data = output.getvalue()
        image_url = 'data:image/jpg;base64,' + base64.b64encode(im_data).decode()
        return image_url

    # generate a list with the JPEG URLS
    bf_list = [generate_image_url(f.bfPath) for f in data]

    # output the list to pass to the template to display
    return bf_list


# view used by the scheduler to perform the database backups
# TODO: check database loaddata
def dump_database():
    # with a date/time coded text file
    with open(join(backup_path, datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')+r'.txt'), 'w') as f:
        # dump the database data into the file
        management.call_command('dumpdata', stdout=f)


# viewset for the users model
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    # define the User objects to handle with this viewset
    queryset = User.objects.all()
    # define the corresponding serializer
    serializer_class = UserSerializer


# viewset for the mice (comments apply to all below)
class MouseViewSet(viewsets.ModelViewSet):
    # define the actual model to be used throughout the viewset
    target_model = Mouse
    # pass all the model objects to the viewset
    queryset = target_model.objects.all()
    # define the corresponding serializer
    serializer_class = MouseSerializer
    # define the permissions structure
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    # define the filtering backend (i.e. for searching)
    filter_backends = (filters.SearchFilter,)
    # define the search fields to look through when filtering
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation] +
                     ['window__region', 'surgery__notes', 'vr_experiment__notes', 'vr_experiment__stimulus',
                      'vr_experiment__notes', 'intrinsic_imaging__stimulus'])

    # override of the perform_create method to also include the user when saving a new instance
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # extra action to generate a labfolder entry from the current mouse
    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        # generate the entry using the function listed above
        labfolder_entry(self)
        # redirect back to the main page
        return HttpResponseRedirect('/loggers/')


# viewset for the cranial windows
class WindowViewSet(viewsets.ModelViewSet):
    target_model = Window

    queryset = target_model.objects.all()
    serializer_class = WindowSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    # extra action to display some or all of the pics available
    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def pic_action(self, request, *args, **kwargs):
        # get the pic url list from the function above
        pic_list = pic_display(self, request)
        # return a response to the pic displaying template
        return Response({'pic_list': pic_list}, template_name='loggers/pic_display.html')


# viewset for surgeries
class SurgeryViewSet(viewsets.ModelViewSet):
    target_model = Surgery

    queryset = target_model.objects.all()
    serializer_class = SurgerySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')


# viewset for crickets
class CricketViewSet(viewsets.ModelViewSet):
    target_model = Cricket

    queryset = target_model.objects.all()
    serializer_class = CricketSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# viewset for 2P experiments
class TwoPhotonViewSet(viewsets.ModelViewSet):
    target_model = TwoPhoton

    queryset = target_model.objects.all()
    serializer_class = TwoPhotonSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# viewset for intrinsic imaging
class IntrinsicImagingViewSet(viewsets.ModelViewSet):
    target_model = IntrinsicImaging

    queryset = target_model.objects.all()
    serializer_class = IntrinsicImagingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# viewset for vr experiments
class VRExperimentViewSet(viewsets.ModelViewSet):
    target_model = VRExperiment

    queryset = target_model.objects.all()
    serializer_class = VRExperimentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)




