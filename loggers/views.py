# imports required for the display of tif images on chrome (since it's not supported natively).
# Found the solution online
import base64
import datetime
import inspect
import pprint
import re
from io import BytesIO
from PIL import Image, ImageOps

# used to make paths below
from os.path import join

# django imports for the scheduler and direct linking
from django.core import management
from django.http import HttpResponseRedirect, HttpResponse

# DRF specific requirements
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# imports from the same project
from . import labfolderRequest
from .forms import form_dict
from .paths import backup_path
from .permissions import IsOwnerOrReadOnly
from .serializers import *

import django_excel as excel
from django.shortcuts import render


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
def pic_display(data):

    # # debugging code
    # pp = pprint.PrettyPrinter()
    # target = inspect.getmembers(instance)
    # pp.pprint([f[0] for f in target])
    # print(instance.get_queryset())

    # generate a url for a JPEG version of the TIF image
    def generate_image_url(image_path):

        # snippet taken online to generate the url based on loading the image and converting to JPEG
        # TODO: find the source
        output_img = BytesIO()
        output_thumb = BytesIO()
        img = Image.open(image_path)
        thumb = ImageOps.fit(img, (100, 100))

        img.save(output_img, format='JPEG')
        thumb.save(output_thumb, format='JPEG')
        im_data = output_img.getvalue()
        thumb_data = output_thumb.getvalue()
        image_url = 'data:image/jpg;base64,' + base64.b64encode(im_data).decode()
        thumb_url = 'data:image/jpg;base64,' + base64.b64encode(thumb_data).decode()
        return image_url, thumb_url

    # generate a list with the JPEG URLS
    im_list = [generate_image_url(f.bfPath) for f in data]

    # output the list to pass to the template to display
    return im_list


# view used by the scheduler to perform the database backups
# TODO: check database loaddata
def dump_database():
    # with a date/time coded text file
    with open(join(backup_path, datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')+r'.txt'), 'w') as f:
        # dump the database data into the file
        management.call_command('dumpdata', stdout=f)


# view to check whether food restriction is over schedule
# TODO: implement the check
def check_restriction():
    print('yay')
    # # iterate through the mice in the database
    # for mouse in Mouse.objects.all():
    #     # check if the mouse has a restriction
    #     if


# function to render the scoresheets as part of the template
def handson_table(request):
    return excel.make_response_from_tables([ScoreSheet], 'handsontable.html')


def embedhandson_table(request):
    content = excel.pe.save_as(
        model=ScoreSheet,
        dest_file_type='handsontable.html',
        dest_embed=True)
    content.seek(0)
    return render(
        request,
        'custom-handson-table.html',
        {
            'handsontable_content': content.read()
        })


# viewset for the users model
class UserViewSet(viewsets.ModelViewSet):
    # define the User objects to handle with this viewset
    queryset = User.objects.all()
    # define the corresponding serializer
    serializer_class = UserSerializer


# viewset for the group model
class GroupViewSet(viewsets.ModelViewSet):
    # define the User objects to handle with this viewset
    queryset = Group.objects.all()
    # define the corresponding serializer
    serializer_class = GroupSerializer


# viewset for the mice (comments apply to all below)
class MouseViewSet(viewsets.ModelViewSet):
    # define the actual model to be used throughout the viewset
    target_model = Mouse
    # pass all the model objects to the viewset
    queryset = target_model.objects.all()
    # define the corresponding serializer
    serializer_class = eval(target_model.__name__+'Serializer')
    # define the permissions structure
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    # define the filtering backend (i.e. for searching)
    filter_backends = (filters.SearchFilter,)
    # define the search fields to look through when filtering
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation] +
                     ['window__region', 'surgery__notes', 'vr_experiment__notes', 'vr_experiment__stimulus',
                      'vr_experiment__notes', 'intrinsic_imaging__stimulus'])
    # specify the modified lookup_field if not using id, needs to be both here and in the serializer itself
    lookup_field = 'mouse_name'

    # override of the perform_create method to also include the user when saving a new instance
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, strain_name=self.kwargs.get('mouseset__strain__strain_name'))

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
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    # def get_queryset(self):
    #     if self.request._request.method != 'GET':
    #         pprint.pprint(self.request.__dict__)
    #     return self.queryset

    # override the filter_queryset method from the generics to capture the search terms in session data
    def filter_queryset(self, queryset):
        # get the queryset (so effectively run the method normally)
        queryset = super().filter_queryset(queryset)
        # if a search was performed
        if 'search' in self.request.GET:
            # get the search terms from the request
            search_string = self.request.GET['search']
        else:
            # otherwise just save an empty string
            search_string = ''
        # save the search_string in the session data
        self.request.session['filtered_queryset'] = search_string
        # force update of the session data (not sure if essential here)
        self.request.session.modified = True
        # return the queryset
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        print(self.request.data)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    # extra action to display some or all of the pics available
    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def pic_action(self, request, *args, **kwargs):

        # remember original mutability state of the request
        _mutable = self.request.GET._mutable
        # set it to mutable
        self.request.GET._mutable = True
        # сhange the search parameters in the request to the ones we saved in session
        self.request.GET['search'] = request.session['filtered_queryset']
        # set the mutable flag back
        self.request.GET._mutable = _mutable
        # filter the queryset with the updated search terms
        data = self.filter_queryset(self.get_queryset())
        # get the pic url list from the function above
        pic_list = pic_display(data)
        # return a response to the pic displaying template
        return Response({'pic_list': pic_list}, template_name='loggers/pic_display.html')

    # extra action to display only the pic associated with the entry
    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def single_pic(self, request, *args, **kwargs):
        # get the current queryset
        data = [self.get_object()]
        # get the pic url list from the function above
        pic_list = pic_display(data)
        # return a response to the pic displaying template
        return Response({'pic_list': pic_list}, template_name='loggers/singlepic_display.html')


# viewset for surgeries
class SurgeryViewSet(viewsets.ModelViewSet):
    target_model = Surgery

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    def get_permissions(self):
        if self.action == 'create' and 'experiment_type' in self.request.data:
            # get the type of experiment from the url
            url_experiment_type = self.request.data['experiment_type'].split('/')[5]

            # get the users in the experiment type
            user_queryset = ExperimentType.objects.get(authorization_name=url_experiment_type).users.all()
            if self.request.user not in user_queryset:
                permission_classes = [IsAdminUser, ]
            else:
                permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

        else:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]
        # return super(SurgeryViewSet, self).get_permissions()

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
    serializer_class = eval(target_model.__name__+'Serializer')
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
    serializer_class = eval(target_model.__name__+'Serializer')
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
    serializer_class = eval(target_model.__name__+'Serializer')
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
    serializer_class = eval(target_model.__name__+'Serializer')
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
class ProjectViewSet(viewsets.ModelViewSet):
    target_model = Project

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# viewset for vr experiments
class LicenseViewSet(viewsets.ModelViewSet):
    target_model = License

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
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
class StrainViewSet(viewsets.ModelViewSet):
    target_model = Strain

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
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
class ScoreSheetViewSet(viewsets.ModelViewSet):
    target_model = ScoreSheet

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    lookup_field = 'slug'

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, renderer_classes=[renderers.StaticHTMLRenderer])
    def see_all_action(self, request, *args, **kwargs):
        return HttpResponse(embedhandson_table(request))


# viewset for vr experiments
class ImmunoStainViewSet(viewsets.ModelViewSet):
    target_model = ImmunoStain

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
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
class MouseSetViewSet(viewsets.ModelViewSet):
    target_model = MouseSet

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
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


class ExperimentTypeViewSet(viewsets.ModelViewSet):
    target_model = ExperimentType

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__ + 'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# if relative URLs are desired, override the get_serializer_context method with the snippet below
# def get_serializer_context(self):
    #     context_out = super().get_serializer_context()
    #     context_out['request'] = None
    #     return context_out
