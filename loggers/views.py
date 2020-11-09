# imports required for the display of tif images on chrome (since it's not supported natively).
# Found the solution online
import base64
import datetime
import pytz
import inspect
import pprint as pp
import re
from io import BytesIO
from PIL import Image, ImageOps

# used to make paths below
from os.path import join, exists
from os import listdir

# django imports for the scheduler and direct linking
from django.core import management
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.forms.models import model_to_dict

# DRF specific requirements
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import JSONRenderer
from rest_framework.pagination import PageNumberPagination

# imports from the same project
from . import labfolderRequest
from .forms import form_dict
from .paths import backup_path
from .permissions import IsOwnerOrReadOnly
from .serializers import *

from django.apps import apps

from .filters import DynamicSearchFilter
from django_filters.rest_framework import DjangoFilterBackend
import pyexcel as pe
from .django_excel_interface import handson_table, embedhandson_table, import_data, export_data, \
    export_network, weights_function, percentage_function, import_old_data


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
    # get the current user
    current_user = str(instance.request.user)
    # pass the form and model to create the labfolder entry
    labfolderRequest.create_table(form, target_model, current_user)


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
def check_restriction():
    print('Checking restrictions')
    # iterate through the restrictions in the database
    for restriction in Restriction.objects.all():
        if restriction.ongoing and (restriction.end_date < timezone.now()):
            print('Mouse: ' + str(restriction.mouse) + ' should not be restricted anymore')


def save_session_data(self, queryset):
    # # get the queryset (so effectively run the method normally)
    # queryset = eval('super().filter_queryset(queryset)')
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
    return queryset


def load_session_data(self, request):
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
    return data


def check_files(instance=None):
    """Function that runs periodically, checking that the paths in the database actually lead to files"""
    # TODO: add callable version for particular user
    # TODO: save the user of the missing files
    # TODO: set up file saving of the list of missing files
    # TODO: check date modified/size
    # get the paths in the database
    app_models = apps.get_app_config('loggers').get_models()
    # allocate a list to store the database paths
    database_paths = []
    # get the logged in user
    # current_user
    # for all the models
    for model in app_models:
        # if it's the profile, skip it
        if model.__name__ in ['Profile', 'Project', 'License']:
            continue
        # get a list of the fields in this model
        fields = model._meta.fields
        # extract only the fields that correspond to paths
        fields = [el.name for el in fields if 'path' in el.name]
        # if the model contains such a field and there's a non-null entry
        if (len(fields) > 0) & (len(model.objects.values_list(*fields)) > 0):
            # append the paths to a global list
            database_paths.append(list(model.objects.values_list(*fields)))
    # flatten the list and exclude N/A
    database_paths = [el for sublist in database_paths for subtuple in sublist for el in subtuple
                      if el not in ['N/A', '']]
    # allocate memory for the missing files
    missing_files = []
    # # check for existence of the files
    # for files in database_paths:
    #     if not exists(files):
    #         missing_files.append(files)
    # print the list of missing files
    # print(missing_files)
    # get the paths in the file system

    # get the paths from the profile
    fields = [el for el in Profile._meta.fields if 'path' in el.name]
    fields = [el for el in fields if 'main' not in el.name]
    # fields.remove('main_path')
    # allocate a list for the physical files
    physical_list = []
    # run through the profile instances checking the paths
    for profiles in Profile.objects.all():
        # for the fields
        for field in fields:
            physical_list.append(field.value_from_object(profiles))
    # print(physical_list)
    return None


def parse_path_experiment(proto_path, instance, model_path):
    """Parse the model arguments from the file name"""

    # split the file name into parts
    name_parts = proto_path.split('_')
    # get the base path for the current model
    base_path = eval('instance.request.user.profile.'+model_path)
    # get the different parameters from the model
    # get the date
    date = datetime.datetime.strptime('_'.join(name_parts[:6]), '%m_%d_%Y_%H_%M_%S')
    date = date.replace(tzinfo=pytz.UTC)
    # get whether there was imaging
    if ('_miniscope_' in proto_path) and not (any(el in proto_path for el in ['nomini', 'nofluo'])):
        imaging = 'doric'
    else:
        imaging = 'no'
    # initialize list for second animal coordinates
    is_animal2 = False
    # set the position counter
    animal_last = 8
    # define the rig
    if name_parts[6] in ['miniscope', 'social', 'other', 'VPrey', 'VScreen']:
        # set the rig variable
        rig = name_parts[6]
        # if the rig is social, set the second animal flag to true
        if rig == 'social':
            is_animal2 = True
        # increase the counter
        animal_last += 1
    else:
        rig = 'VR'

    # if imaging is detected, create the paths for fluo and tif
    if imaging != 'no':
        # define the calcium data path
        fluo_path = join(base_path, proto_path + '_calcium_data.h5')
        tif_path = join(base_path, proto_path + '.tif')
    else:
        fluo_path = ''
        tif_path = ''
    # get the animal
    animal = Mouse.objects.get(mouse_name='_'.join(name_parts[animal_last-2:animal_last+1]))
    # get the second animal if present
    if is_animal2:
        animal2 = Mouse.objects.get(mouse_name='_'.join(name_parts[animal_last+1:animal_last + 3]))
        animal_last += 3
    else:
        animal2 = ''
    # increase the counter
    animal_last += 1
    # get the result
    result = name_parts[animal_last]
    # increase the counter
    animal_last += 1
    # check if there is a lighting condition
    if (len(name_parts) > animal_last) and (name_parts[animal_last] in ['dark']):
        lighting = name_parts[animal_last]
        # increase the counter
        animal_last += 1
    else:
        lighting = 'normal'

    # add any extra info as notes
    if len(name_parts) > animal_last:
        notes = '_'.join((name_parts[animal_last:]))
    else:
        # if not, add blank to keep it searchable
        notes = 'BLANK'

    # define the path for the bonsai file
    bonsai_path = join(base_path, proto_path + '.csv')
    # define the path for the avi file
    avi_path = join(base_path, proto_path + '.avi')
    # define the path for the tracking and sync file depending on date
    track_path = join(base_path, proto_path + '.txt')
    # define the path for the h5 file from vscreen (unity)
    screen_path = join(base_path, proto_path + '.h5')
    # define the path for the sync file
    sync_path = proto_path
    # define the path for the dlc file
    dlc_path = join(base_path, proto_path + '_dlc.h5')
    if rig == 'miniscope':
        sync_path = sync_path.replace('_miniscope_', '_syncMini_')
    elif rig == 'VPrey':
        sync_path = sync_path.replace('_VPrey_', '_syncVPrey_')
    elif rig == 'VScreen':
        sync_path = sync_path.replace('_VScreen_', '_syncVScreen_')
    else:
        sync_path = sync_path[:19] + '_syncVR' + sync_path[19:]
    sync_path = join(base_path, sync_path) + '.csv'

    print(sync_path)
    return {'owner': instance.request.user,
            'mouse': animal,
            'date': date,
            'result': result,
            'lighting': lighting,
            'rig': rig,
            'imaging': imaging,
            'bonsai_path': bonsai_path,
            'avi_path': avi_path,
            'track_path': track_path,
            'sync_path': sync_path,
            'fluo_path': fluo_path,
            'tif_path': tif_path,
            'screen_path': screen_path,
            'dlc_path': dlc_path,
            'notes': notes,
            'animal2': animal2}


def parse_path_image(proto_path, instance, model_path):
    """Parse the model arguments from the file name"""

    # split the file name into parts
    name_parts = proto_path.split('_')
    # get the base path for the current model
    base_path = eval('instance.request.user.profile.' + model_path)
    # get the different parameters from the model
    # get the date
    date = datetime.datetime.strptime(name_parts[0], '%Y%m%d')

    # get the animal
    animal = Mouse.objects.get(mouse_name='_'.join(name_parts[1:4]))

    # get the region
    region = name_parts[4]

    # define the path for the different files
    bfpath = join(base_path, '_'.join((name_parts[0], animal.mouse_name, 'BF', region)) + '.tif')
    flpath = bfpath.replace('BF', 'FL')
    flgreenpath = bfpath.replace('BF', 'FLgreen')
    otherpath = bfpath.replace('BF', 'OTHER')

    return {'owner': instance.request.user,
            'mouse': animal,
            'window_date': date,
            'bfPath': bfpath,
            'flPath': flpath,
            'flgreenPath': flgreenpath,
            'otherPath': otherpath,
            'region': region}


def general_serializer(instance):
    """Provide a serializer depending on the request"""
    # get the serializer for this model
    serializer_class = eval(instance.target_model.__name__ + 'Serializer')
    # use this for create, update and retrieve, since we only need special serialization to display less in list and
    # to communicate with python
    if instance.action in ['retrieve', 'create', 'update']:
        # if it's the detail view, just return the standard serializer
        return serializer_class
    elif instance.action == 'from_python':
        # copy the declared fields from the detail serializer
        PythonSerializer._declared_fields = serializer_class._declared_fields.copy()
        # also the fields
        PythonSerializer.Meta.fields = serializer_class.Meta.fields.copy()
        # get fields
        model_fields = instance.target_model._meta.get_fields()
        # copy the extra_kwargs
        PythonSerializer.Meta.extra_kwargs = serializer_class.Meta.extra_kwargs.copy()
        # and the model
        PythonSerializer.Meta.model = instance.target_model
        # turn the relations into text fields, except the m2m field since the automatic serialization works better
        for fields in model_fields:
            if fields.is_relation:

                if (not isinstance(fields, models.ManyToManyField)) and \
                        (not isinstance(fields, models.ManyToManyRel)):
                    PythonSerializer._declared_fields[fields.name] = serializers.StringRelatedField()
                else:
                    PythonSerializer._declared_fields[fields.name] = serializers.StringRelatedField(many=True)

        return PythonSerializer
    else:  # if not, modify it to remove unnecessary fields from the list view

        # copy the attributes to the generalized serializer
        GeneralSerializer._declared_fields = serializer_class._declared_fields.copy()
        GeneralSerializer.Meta.fields = serializer_class.Meta.fields.copy()
        GeneralSerializer.Meta.extra_kwargs = serializer_class.Meta.extra_kwargs.copy()
        GeneralSerializer.Meta.model = instance.target_model
        # allocate a list of the fields to remove from the list view
        remove_fields = []
        # for all the fields in the serializer
        for fields in GeneralSerializer.Meta.fields:

            # remove the id field (since it's not in declared_fields)
            if fields in ['id', 'slug']:
                # eliminate the field from the serializer
                remove_fields.append(fields)
                continue
            if instance.target_model.__name__ != 'Mouse' and fields == 'mouse':
                # remove the current mouse extra_kwargs so it displays
                del GeneralSerializer.Meta.extra_kwargs[fields]
                continue
            # remove the fields that have been assigned as read only
            if (fields in serializer_class._declared_fields.keys()) and \
               (('read_only=True' in str(GeneralSerializer._declared_fields[fields])) or
               ('ReadOnly' in str(GeneralSerializer._declared_fields[fields]))):

                # eliminate the field from the serializer
                remove_fields.append(fields)
                # remove the field from declared fields
                del GeneralSerializer._declared_fields[fields]
                continue

            GeneralSerializer.Meta.extra_kwargs[fields] = {'write_only': True}

        # remove the read only fields
        GeneralSerializer.Meta.fields = [el for el in GeneralSerializer.Meta.fields if el not in remove_fields]
        # overwrite url kwargs, since it is set by default to read only
        GeneralSerializer.Meta.extra_kwargs['url'] = {'lookup_field': instance.lookup_field}
        # put the mouse entry at the top
        if 'mouse' in GeneralSerializer.Meta.fields:
            GeneralSerializer.Meta.fields.remove('mouse')
            GeneralSerializer.Meta.fields = ['mouse'] + GeneralSerializer.Meta.fields
        return GeneralSerializer


def from_python_function(instance):
    """Manage requests from python analyzing scripts"""
    # set the pagination class
    pagination_class = FromPythonPagination
    # filter queryset based on the search terms
    instance.queryset = instance.filter_queryset(instance.queryset)
    # get the serializer for this view
    current_serializer = general_serializer(instance)
    # serialize the data (many flag for serializing a queryset)
    serialized_queryset = current_serializer(instance.queryset, many=True, context={'request': instance.request})
    # get the data to serialize
    data = serialized_queryset.data
    # generate the response
    return HttpResponse(JSONRenderer().render({'count': len(instance.queryset), 'next': None, 'previous': None,
                                               'results': data}))


class FromPythonPagination(PageNumberPagination):
    """Class to control pagination when querying from analysis scripts"""
    page_size = 10000
    page_size_query_param = 'page_size'
    max_page_size = 100000


# viewset for the users model
class UserViewSet(viewsets.ModelViewSet):
    # define the User objects to handle with this viewset
    queryset = User.objects.all()
    # define the corresponding serializer
    serializer_class = UserSerializer

    lookup_field = 'username'

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def check_files_action(self, request, *args, **kwargs):
        check_files(kwargs['username'])
        return HttpResponseRedirect('/loggers/user/')


# viewset for the profile model
class ProfileViewSet(viewsets.ModelViewSet):
    # define the User objects to handle with this viewset
    queryset = Profile.objects.all()
    # define the corresponding serializer
    serializer_class = ProfileSerializer
    # define the permissions structure
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )

    def perform_create(self, serializer):
        # populate the path fields
        field_list = [f.name for f in Profile._meta.get_fields() if not f.is_relation]
        save_statement = ''
        for f in field_list:
            if f not in ['user', 'main_path', 'id', 'pk']:
                save_statement += f+"='"+self.request.data['main_path']+"\\\\"+f[:-5]+"',"
        eval("serializer.save(" + save_statement + ")")


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
    # serializer_class = eval(target_model.__name__+'Serializer')
    # define the permissions structure
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    # define the filtering backend (i.e. for searching)
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter,)
    ordering = ['-dob']
    ordering_fields = ['dob']
    # define the search fields to look through when filtering
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation] +
                     ['window__region', 'surgery__notes', 'vr_experiment__notes', 'video_experiment__notes',
                      'owner__username'])
    # specify the modified lookup_field if not using id, needs to be both here and in the serializer itself
    lookup_field = 'mouse_name'

    # override of the perform_create method to also include the user when saving a new instance
    def perform_create(self, serializer):
        # check that there are enough mouse slots left in the mouseset
        max_number = serializer.validated_data['mouse_set'].max_number
        current_number = serializer.validated_data['mouse_set'].current_number
        if current_number < max_number:
            current_number += 1
            # mouseset_name = self.request.data['mouse_set'].split('/')[5]
            # serializer.save(owner=self.request.user,
            #                 strain_name=MouseSet.objects.get(mouse_set_name=mouseset_name).strain_id)

            # alternative way
            mouse_set_instance = serializer.validated_data['mouse_set']
            data = {'current_number': current_number}
            mouse_set_serializer_instance = MouseSetSerializer(mouse_set_instance, data=data, partial=True)
            mouse_set_serializer_instance.is_valid()
            mouse_set_serializer_instance.save()
            serializer.save(owner=self.request.user, strain_name=mouse_set_instance.strain_id)
        else:
            raise PermissionDenied({'message': 'Max number of mice reached on this set'})

    def get_serializer_class(self):
        return general_serializer(self)

    # extra action to generate a labfolder entry from the current mouse
    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        # generate the entry using the function listed above
        labfolder_entry(self)
        # redirect back to the main page
        return HttpResponseRedirect('/loggers/')


# viewset for the cranial windows
class WindowViewSet(viewsets.ModelViewSet):
    # TODO: properly set the paths to the different file systems
    target_model = Window

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name'])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['window_date'] = ['gt', 'lt', 'exact']
    # filterset_fields['notes'] = ['icontains']
    filterset_fields['slug'] = ['icontains']

    lookup_field = 'slug'

    def filter_queryset(self, queryset):
        """override the filter_queryset method from the generics to capture the search terms in session data"""
        # get the queryset (so effectively run the method normally)
        queryset = super().filter_queryset(queryset)
        # now fix it and save it in session data
        queryset = save_session_data(self, queryset)
        return queryset

    def perform_create(self, serializer):
        # serializer.save(owner=self.request.user, testPath=eval("self.request.user.profile." +
        #                 self.target_model.__name__+"_path") + "\\" + str(self.request.data['Select file']))
        serializer.save(owner=self.request.user)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    # extra action to display some or all of the pics available
    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def pic_action(self, request, *args, **kwargs):
        # load data from the session
        data = load_session_data(self, request)
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

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def load_batch(self, request, *args, **kwargs):
        """Select several files from a file dialog to create entries"""
        try:
            # get a list of the files in the associated path
            base_path = self.request.user.profile.Window_path
            file_list = listdir(base_path)
            # include only csv files
            file_list = [el[:-4].replace('BF_', '') for el in file_list if ('.tif' in el) and ('.xml' not in el)
                         and ('_BF_' in el)]
            # get a list of the existing file names
            existing_rows = [el[0] for el in Window.objects.values_list('slug')]
            # for all the files
            for file in file_list:
                # check if the entry already exists
                if file.lower() in existing_rows:
                    # if so, skip making a new one
                    continue
                # get the data for the entry
                data_dict = parse_path_image(file, self, 'Window_path')
                print(data_dict)
                # check the paths in the filesystem, otherwise leave the entry empty
                for key, value in data_dict.items():
                    if (isinstance(value, str)) and ('Path' in key) and (not exists(value)):
                        data_dict[key] = ''
                # create the model instance with the data
                model_instance = Window.objects.create(**data_dict)

                # save the model instance
                model_instance.save()

            return HttpResponseRedirect('/loggers/window/')
        except:
            return HttpResponseBadRequest('loading file failed, check file names')


# viewset for surgeries
class SurgeryViewSet(viewsets.ModelViewSet):
    target_model = Surgery

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    # permission_classes = (permissions.IsAuthenticatedOrReadOnly,
    #                       IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']

    lookup_field = 'slug'

    def get_permissions(self):
        if self.action == 'create' and 'experiment_type' in self.request.data:
            # get the type of experiment from the url
            url_experiment_type = self.request.data['experiment_type']
            # get the users in the experiment type
            user_queryset = ExperimentType.objects.get(experiment_name=url_experiment_type.split('/')[-2]).users.all()
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

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')


class RestrictionTypeViewSet(viewsets.ModelViewSet):
    target_model = RestrictionType

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    lookup_field = 'slug_restrictionType'

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RestrictionViewSet(viewsets.ModelViewSet):
    target_model = Restriction

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
        # calculate the end date based on the start date and the duration
        # get the start date
        # start_date = serializer.validated_data['start_date']
        start_date = timezone.now()
        # get the duration from the linked restriction type
        duration = serializer.validated_data['restriction_type'].duration
        # calculate the resulting date
        end_date = start_date + datetime.timedelta(days=duration)
        # save the info
        serializer.save(owner=self.request.user, end_date=end_date, ongoing=True)


# viewset for crickets
class VideoExperimentViewSet(viewsets.ModelViewSet):
    target_model = VideoExperiment

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']
    filterset_fields['slug'] = ['iexact']

    lookup_field = 'slug'

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=False, renderer_classes=[renderers.StaticHTMLRenderer])
    def from_python(self, request, *args, **kwargs):
        return from_python_function(self)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def load_batch(self, request, *args, **kwargs):
        """Select several files from a file dialog to create entries"""
        try:
            # get a list of the files in the associated path
            base_path = self.request.user.profile.VideoExperiment_path
            file_list = listdir(base_path)
            # include only csv files
            file_list = [el[:-4] for el in file_list if ('.csv' in el) and ('sync' not in el)]
            # get a list of the existing file names (bonsai)
            existing_rows = [el[0] for el in VideoExperiment.objects.values_list('slug')]
            # for all the files
            for file in file_list:
                # check if the entry already exists
                if file.lower() in existing_rows:
                    # if so, skip making a new one
                    continue
                # get the data for the entry
                data_dict = parse_path_experiment(file, self, 'VideoExperiment_path')
                # get rid of the animal2 entry
                del data_dict['animal2']
                # and of the motive one
                del data_dict['track_path']
                # check the paths in the filesystem, otherwise leave the entry empty
                for key, value in data_dict.items():
                    # if the entry is already empty, don't check
                    if data_dict[key] == '':
                        continue
                    if (isinstance(value, str)) and ('path' in key) and (not exists(value)):
                        # print a warning
                        print('Path not found for key %s and value %s' % (key, value))
                        # clear the path
                        data_dict[key] = ''

                # if the tif file exists but the calcium_data file doesn't, log it in the notes
                if (data_dict['fluo_path'] == '') and (data_dict['tif_path'] != ''):
                    data_dict['imaging'] = 'no'
                    data_dict['notes'] += 'norois'
                # create the model instance with the data
                model_instance = VideoExperiment.objects.create(**data_dict)
                # get the model for the experiment type to use
                experiment_type = ExperimentType.objects.filter(experiment_name='Free_behavior')
                # add the experiment type to the model instance (must use set() cause m2m)
                model_instance.experiment_type.set(experiment_type)
                # save the model instance
                model_instance.save()

            return HttpResponseRedirect('/loggers/video_experiment/')
        except:
            print('Problem file:' + file)
            return HttpResponseBadRequest('loading file %s failed, check file names' % file)

# viewset for 2P experiments
class TwoPhotonViewSet(viewsets.ModelViewSet):
    target_model = TwoPhoton

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    # filterset_fields['notes'] = ['icontains']

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
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    # filterset_fields['notes'] = ['icontains']

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
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']
    filterset_fields['slug'] = ['icontains']

    lookup_field = 'slug'

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=False, renderer_classes=[renderers.StaticHTMLRenderer])
    def from_python(self, request, *args, **kwargs):
        return from_python_function(self)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def load_batch(self, request, *args, **kwargs):
        """Select files automatically from a target path to create entries"""
        # initialize file to avoid the warning below
        file = ''
        try:
            # get a list of the files in the associated path
            base_path = self.request.user.profile.VRExperiment_path
            file_list = listdir(base_path)
            # include only csv files
            file_list = [el[:-4] for el in file_list if ('.csv' in el) and ('sync' not in el)]
            # get a list of the existing file names (bonsai)
            existing_rows = [el[0] for el in VRExperiment.objects.values_list('slug')]
            # for all the files
            for file in file_list:
                # check if the entry already exists
                if file.lower() in existing_rows:
                    # if so, skip making a new one
                    continue
                # get the data for the entry
                data_dict = parse_path_experiment(file, self, 'VRExperiment_path')
                # get rid of the animal2 entry
                del data_dict['animal2']
                # check the paths in the filesystem, otherwise leave the entry empty
                for key, value in data_dict.items():
                    # if the entry is already empty, don't check
                    if data_dict[key] == '':
                        continue
                    if (isinstance(value, str)) and ('path' in key) and (not exists(value)):
                        # print a warning
                        print('Path not found for key %s and value %s' % (key, value))
                        # clear the path
                        data_dict[key] = ''
                # if the tif file exists but the calcium_data file doesn't, log it in the notes
                if (data_dict['fluo_path'] == '') and (data_dict['tif_path'] != ''):
                    data_dict['imaging'] = 'no'
                    data_dict['notes'] += 'norois'
                # create the model instance with the data
                model_instance = VRExperiment.objects.create(**data_dict)
                # get the model for the experiment type to use
                experiment_type = ExperimentType.objects.filter(experiment_name='Free_behavior')
                # add the experiment type to the model instance (must use set() cause m2m)
                model_instance.experiment_type.set(experiment_type)
                # save the model instance
                model_instance.save()

            return HttpResponseRedirect('/loggers/vr_experiment/')
        except:
            print('Problem file:' + file)
            return HttpResponseBadRequest('loading file %s failed, check file names' % file)

    def perform_create(self, serializer):
        # # get the file name from the entry
        # proto_path = str(self.request.data['Select file'])[:-4]
        # # save the instance
        # serializer.save(**parse_path(proto_path, self))
        serializer.save(owner=self.request.user)


# viewset for projects
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


# viewset for scoresheets
class ScoreSheetViewSet(viewsets.ModelViewSet):
    target_model = ScoreSheet

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, )
    ordering = ['-sheet_date']
    ordering_fields = ['sheet_date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['sheet_date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']

    lookup_field = 'slug'

    # override the filter_queryset method from the generics to capture the search terms in session data
    def filter_queryset(self, queryset):
        # get the queryset (so effectively run the method normally)
        queryset = super().filter_queryset(queryset)
        # now fix it and save it in session data
        queryset = save_session_data(self, queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def see_scoresheet(self, request, *args, **kwargs):
        # TODO: figure out how to properly embed the table in a template
        # get the mouse from the request
        mouse = self.get_object().mouse
        # get the other scoresheet objects from the same mouse
        data = ScoreSheet.objects.filter(mouse=mouse)
        # get the fields
        fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name'])
        return HttpResponse(handson_table(request, data, fields))

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer], methods=['GET', 'POST'])
    def import_scoresheet(self, request, *args, **kwargs):
        return HttpResponse(import_data(request))

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer], methods=['GET', 'POST'])
    def import_old_scoresheet(self, request, *args, **kwargs):
        return HttpResponse(import_old_data(request))

    # @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    # def export_scoresheet(self, request, *args, **kwargs):
    #     # remember to install the required pyexcel format variants
    #     # get the mouse from the request
    #     mouse = self.get_object().mouse
    #     # get the other scoresheet objects from the same mouse
    #     data = ScoreSheet.objects.filter(mouse=mouse)
    #     # get the fields
    #     fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name',
    #                                                                                       'owner__username'])
    #     return HttpResponse(export_data(request, "custom", data, fields), content_type='application/msexcel')

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def export_to_network(self, request, *args, **kwargs):
        return export_network(self, request)

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def see_weight(self, request, *args, **kwargs):
        # get the mouse from the request
        mouse = self.get_object().mouse
        # get the other scoresheet objects from the same mouse
        data = ScoreSheet.objects.filter(mouse=mouse)
        # get the fields
        fields = (['sheet_date', 'weight', 'food_consumed'])
        return weights_function(request, data, fields)

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def see_percentage_weight(self, request, *args, **kwargs):
        # get the mouse from the request
        mouse = self.get_object().mouse
        # get the other scoresheet objects from the same mouse
        data = ScoreSheet.objects.filter(mouse=mouse)
        # get the restrictions
        restrictions = Restriction.objects.filter(mouse=mouse, ongoing=True)
        # get the fields
        fields = (['sheet_date', 'weight', 'food_consumed', 'notes'])
        return percentage_function(request, data, fields, restrictions)


# viewset for immuno stains
class ImmunoStainViewSet(viewsets.ModelViewSet):
    target_model = ImmunoStain

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']

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

    def get_serializer_class(self):
        return general_serializer(self)


class AnalyzedDataViewSet(viewsets.ModelViewSet):

    target_model = AnalyzedData
    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__ + 'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']
    filterset_fields['slug'] = ['icontains']

    lookup_field = 'slug'

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=False, renderer_classes=[renderers.StaticHTMLRenderer])
    def from_python(self, request, *args, **kwargs):
        return from_python_function(self)


class FigureViewSet(viewsets.ModelViewSet):

    target_model = Figure
    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__ + 'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])
    filterset_fields = {f.name: ['exact'] for f in target_model._meta.get_fields() if not f.is_relation}
    filterset_fields['date'] = ['gt', 'lt', 'exact']
    filterset_fields['notes'] = ['icontains']

    lookup_field = 'slug'

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=False, renderer_classes=[renderers.StaticHTMLRenderer])
    def from_python(self, request, *args, **kwargs):
        return from_python_function(self)

# if relative URLs are desired, override the get_serializer_context method with the snippet below
# def get_serializer_context(self):
    #     context_out = super().get_serializer_context()
    #     context_out['request'] = None
    #     return context_out
