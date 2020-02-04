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
from os.path import join, exists
from os import listdir

# django imports for the scheduler and direct linking
from django.core import management
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django import forms

# DRF specific requirements
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied

# imports from the same project
from . import labfolderRequest
from .forms import form_dict
from .paths import backup_path
from .permissions import IsOwnerOrReadOnly
from .serializers import *

import django_excel as excel
from django.shortcuts import render, redirect
from django.apps import apps

from .filters import DynamicSearchFilter
import pyexcel as pe


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
def check_restriction():
    print('Checking restrictions')
    # iterate through the restrictions in the database
    for restriction in Restriction.objects.all():
        if restriction.ongoing and (restriction.end_date < timezone.now()):
            print('Mouse: ' + str(restriction.mouse) + ' should not be restricted anymore')


# # function to render the scoresheets as part of the template
def handson_table(request, query_sets, fields):
    return excel.make_response_from_query_sets(query_sets, fields, 'handsontable.html')

    # content = excel.pe.save_as(source=query_sets,
    #                            dest_file_type='handsontable.html',
    #                            dest_embed=True)
    # content.seek(0)
    # return render(
    #     request,
    #     'custom-handson-table.html',
    #     {
    #         'handsontable_content': content.read()
    #     })
    # return Response({'handsontable_content': render(content)}, template_name='custom-handson-table.html')


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


def import_data(request):

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        search_fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation])

        def na_remover(row):
            row = [0 if el == 'N/A' else el for el in row]
            return row

        def mouse_namer(row):
            q = Mouse.objects.filter(mouse_name=row[-2])[0]
            row[-2] = q
            p = User.objects.filter(username=row[-1])[0]
            row[-1] = p
            return row

        def fix_format(row):
            # read the different sheets
            slug_field = slugify(str(row[1])[0:19])
            return row
        if form.is_valid():
            print(request.FILES['file'])

            def save_book_as(**keywords):
                return
            request.FILES['file'].save_book_to_database(models=[ScoreSheet], initializers=[mouse_namer],
                                                        mapdicts=[search_fields+['mouse', 'owner']])
                                                        # mapdicts=[search_fields.sort()])
            return HttpResponse(embedhandson_table(request))
        else:
            return HttpResponseBadRequest()
    else:
        form = UploadFileForm()
    return render(request, 'upload_form.html', {'form': form, 'title': 'Import', 'header': 'Upload data'})


def export_data(request, atype, queryset, fields):
    if atype == "sheet":
        return excel.make_response_from_a_table(ScoreSheet, 'xls', file_name="sheet")
    elif atype == "book":
        return excel.make_response_from_tables([ScoreSheet], 'xls', file_name="book")
    elif atype == "custom":
        return excel.make_response_from_query_sets(queryset, fields, 'xls', file_name='custom')
    else:
        return HttpResponseBadRequest("bad request, choose one")


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


def check_files(current_user=None):
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
        if model.__name__ == 'Profile':
            continue
        # get a list of the fields in this model
        fields = model._meta.fields
        # extract only the fields that correspond to paths
        fields = [el.name for el in fields if 'path' in el.name]
        # if the model contains such a field and there's a non-null entry
        if (len(fields) > 0) & (len(model.objects.values_list(*fields)) > 0):
            # append the paths to a global list
            database_paths.append(list(model.objects.values_list(*fields)[0]))
    # flatten the list
    # print([el for sublist in database_paths for el in sublist])
    database_paths = [el for sublist in database_paths for el in sublist]
    print(database_paths)
    # get the paths in the file system

    # # get the paths from the profile
    # fields = [el for el in models.Profile._meta.fields if 'path' in el.name]
    # fields = [el for el in fields if 'main' not in el.name]
    # # fields.remove('main_path')
    # # allocate a list for the physical files
    # physical_list = []
    # # run through the profile instances checking the paths
    # for profiles in models.Profile.objects.all():
    #     # for the fields
    #     for field in fields:
    #         physical_list.append(field.value_from_object(profiles))
    #         print(listdir(field.value_from_object(profiles)))
    # print(physical_list)
    return None


def parse_path(proto_path, instance, model_path):
    """Parse the model arguments from the file name"""

    # split the file name into parts
    name_parts = proto_path.split('_')
    # get the base path for the current model
    base_path = eval('instance.request.user.profile.'+model_path)
    # get the different parameters from the model
    # get the date
    date = datetime.datetime.strptime('_'.join(name_parts[:6]), '%m_%d_%Y_%H_%M_%S')
    # initialize list for second animal coordinates
    is_animal2 = False
    # set the position counter
    animal_last = 8
    # check if there is a miniscope condition
    if name_parts[6] in ['miniscope', 'social', 'other']:
        rig = name_parts[6]
        # set the coordinates of the animal name
        # animal_last = 9

        if rig == 'miniscope':
            # define the miniscope path
            fluo_path = join(base_path, proto_path + '.csv')
        elif rig == 'social':
            fluo_path = ''
            is_animal2 = True
        else:
            rig = 'other'
            fluo_path = ''

        # increase the counter
        animal_last += 1
    else:
        rig = 'VR'
        fluo_path = ''
        # animal_last = 8

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
        notes = ''

    # define the path for the bonsai file
    bonsai_path = join(base_path, proto_path + '.csv')
    # define the path for the avi file
    avi_path = join(base_path, proto_path + '.avi')
    # # define the path for the tracking and sync file depending on date
    track_path = join(base_path, proto_path + '.txt')
    # define the path for the sync file
    sync_path = join(base_path, proto_path + '.csv')
    if rig == 'miniscope':
        sync_path = sync_path.replace('miniscope', 'syncMini')
    else:
        sync_path = sync_path[:19] + '_syncVR' + sync_path[19:]
    
    return {'owner': instance.request.user,
            'mouse': animal,
            'date': date,
            'result': result,
            'lighting': lighting,
            'rig': rig,
            'bonsai_path': bonsai_path,
            'avi_path': avi_path,
            'track_path': track_path,
            'sync_path': sync_path,
            'fluo_path': fluo_path,
            'notes': notes,
            'animal2': animal2}


def general_serializer(instance):
    # get the serializer for this model
    serializer_class = eval(instance.target_model.__name__ + 'Serializer')

    if instance.action == 'retrieve':
        # if it's the detail view, just return the standard serializer
        return serializer_class
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

            # remove the if field (since it's not in declared_fields)
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


class UploadFileForm(forms.Form):
    file = forms.FileField()


# viewset for the users model
class UserViewSet(viewsets.ModelViewSet):
    # define the User objects to handle with this viewset
    queryset = User.objects.all()
    # define the corresponding serializer
    serializer_class = UserSerializer

    lookup_field = 'username'


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
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name'])

    lookup_field = 'slug'

    # def get_queryset(self):
    #     if self.request._request.method != 'GET':
    #         pprint.pprint(self.request.__dict__)
    #     return self.queryset

    # override the filter_queryset method from the generics to capture the search terms in session data
    def filter_queryset(self, queryset):
        # get the queryset (so effectively run the method normally)
        queryset = super().filter_queryset(queryset)
        # now fix it and save it in session data
        queryset = save_session_data(self, queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, testPath=eval("self.request.user.profile." +
                        self.target_model.__name__+"_path") + "\\" + str(self.request.data['Select file']))

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


# viewset for surgeries
class SurgeryViewSet(viewsets.ModelViewSet):
    target_model = Surgery

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    lookup_field = 'slug'

    def get_permissions(self):
        if self.action == 'create' and 'experiment_type' in self.request.data:
            # get the type of experiment from the url
            url_experiment_type = self.request.data['experiment_type'].split('/')[5]
            # get the users in the experiment type
            user_queryset = ExperimentType.objects.get(experiment_name=url_experiment_type).users.all()
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
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    lookup_field = 'slug'

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def load_batch(self, request, *args, **kwargs):
        """Select several files from a file dialog to create entries"""
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
            data_dict = parse_path(file, self, 'VideoExperiment_path')
            # get rid of the animal2 entry
            del data_dict['animal2']
            # and of the motive one
            del data_dict['track_path']
            # check the paths in the filesystem, otherwise leave the entry empty
            for key, value in data_dict.items():
                if (isinstance(value, str)) and ('path' in key) and (not exists(value)):
                    data_dict[key] = ''
            # create the model instance with the data
            model_instance = VideoExperiment.objects.create(**data_dict)
            # get the model for the experiment type to use
            experiment_type = ExperimentType.objects.filter(experiment_name='Free_behavior')
            # add the experiment type to the model instance (must use set() cause m2m)
            model_instance.experiment_type.set(experiment_type)
            # save the model instance
            model_instance.save()

        return HttpResponseRedirect('/loggers/video_experiment/')


# viewset for 2P experiments
class TwoPhotonViewSet(viewsets.ModelViewSet):
    target_model = TwoPhoton

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
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
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
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
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-date']
    ordering_fields = ['date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

    lookup_field = 'slug'

    def get_serializer_class(self):
        return general_serializer(self)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

    @action(detail=False, renderer_classes=[renderers.TemplateHTMLRenderer])
    def load_batch(self, request, *args, **kwargs):
        """Select several files from a file dialog to create entries"""
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
            data_dict = parse_path(file, self, 'VRExperiment_path')
            # get rid of the animal2 entry
            del data_dict['animal2']
            # check the paths in the filesystem, otherwise leave the entry empty
            for key, value in data_dict.items():
                if (isinstance(value, str)) and ('path' in key) and (not exists(value)):
                    data_dict[key] = ''
            # create the model instance with the data
            model_instance = VRExperiment.objects.create(**data_dict)
            # get the model for the experiment type to use
            experiment_type = ExperimentType.objects.filter(experiment_name='Free_behavior')
            # add the experiment type to the model instance (must use set() cause m2m)
            model_instance.experiment_type.set(experiment_type)
            # save the model instance
            model_instance.save()

        return HttpResponseRedirect('/loggers/vr_experiment/')

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
    # TODO: add the visualizations
    target_model = ScoreSheet

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-sheet_date']
    ordering_fields = ['sheet_date']
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation])

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

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')

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

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def export_scoresheet(self, request, *args, **kwargs):
        # remember to install the required pyexcel format variants
        # get the mouse from the request
        mouse = self.get_object().mouse
        # get the other scoresheet objects from the same mouse
        data = ScoreSheet.objects.filter(mouse=mouse)
        # get the fields
        fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name',
                                                                                          'owner__username'])
        return HttpResponse(export_data(request, "custom", data, fields), content_type='application/msexcel')

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def export_to_network(self, request, *args, **kwargs):
        # get the license from this animal
        license_object = self.get_object().mouse.mouse_set.license
        # get the user from this animal
        user_object = license_object.owner
        # get all the mice from this license and user
        # first get the mouse_sets
        mouse_sets = MouseSet.objects.filter(owner=user_object, license=license_object)
        # now get the mice within this mouse set
        mice = [list(el.mouse.all()) for el in mouse_sets]
        # flatten the list
        mice = [el for sublist in mice for el in sublist]
        # get the corresponding scoresheets
        scoresheets = [list(el.score_sheet.all()) for el in mice]
        # get the fields
        # get the fields
        fields = ([f.name for f in ScoreSheet._meta.get_fields() if not f.is_relation] + ['mouse__mouse_name',
                                                                                          'owner__username'])
        file_stream = pe.save_as(query_sets=scoresheets[0], column_names=fields,
                                 dest_file_type='xls')
        # sheet = file_stream.sheet

        print(file_stream.read())
        return HttpResponse(export_data(request, "custom", scoresheets[0], fields), content_type='application/msexcel')
        # return HttpResponseRedirect('/loggers/score_sheet/')


# viewset for immuno stains
class ImmunoStainViewSet(viewsets.ModelViewSet):
    target_model = ImmunoStain

    queryset = target_model.objects.all()
    serializer_class = eval(target_model.__name__+'Serializer')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (DynamicSearchFilter, filters.OrderingFilter, )
    ordering = ['-window_date']
    ordering_fields = ['window_date']
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
