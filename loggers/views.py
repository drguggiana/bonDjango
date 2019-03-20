# from django.shortcuts import render
import base64
import datetime
import inspect
import pprint
import re
from io import BytesIO
from os.path import join

from PIL import Image
# from rest_framework.reverse import reverse
#
# from django.views import generic
from django.contrib.auth.models import User
from django.core import management
from django.http import HttpResponseRedirect
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
# from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response

from . import labfolderRequest
from .forms import form_dict
from .models import *
from .paths import backup_path
from .permissions import IsOwnerOrReadOnly
from .serializers import *


# Create your views here.


def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def labfolder_entry(instance):
    target_model = convert(type(instance.get_object()).__name__)
    form = form_dict[target_model](instance.get_object())
    labfolderRequest.create_table(form, target_model)


def pic_display(instance, request):
    pp = pprint.PrettyPrinter()
    target = inspect.getmembers(instance)
    pp.pprint([f[0] for f in target])
    # print(instance.get_queryset()[0].dob)
    # data = instance.get_queryset()
    data = [instance.get_object()]
    # print(instance.)

    def generate_image_url(image_path):
        # if image_path == 'N/A':
        #     return

        output = BytesIO()
        img = Image.open(image_path)
        img.save(output, format='JPEG')
        im_data = output.getvalue()
        image_url = 'data:image/jpg;base64,' + base64.b64encode(im_data).decode()
        return image_url
    bf_list = [generate_image_url(f.bfPath) for f in data]
    # bf_list = filter(None, bf_list)

    return bf_list


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MouseViewSet(viewsets.ModelViewSet):
    target_model = Mouse
    queryset = target_model.objects.all()
    serializer_class = MouseSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ([f.name for f in target_model._meta.get_fields() if not f.is_relation] +
                     ['window__region', 'surgery__notes', 'vr_experiment__notes', 'vr_experiment__stimulus',
                      'vr_experiment__notes', 'intrinsic_imaging__stimulus'])

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def labfolder_action(self, request, *args, **kwargs):
        labfolder_entry(self)
        return HttpResponseRedirect('/loggers/')


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

    @action(detail=True, renderer_classes=[renderers.TemplateHTMLRenderer])
    def pic_action(self, request, *args, **kwargs):
        pic_list = pic_display(self, request)
        # pic_list = []
        return Response({'pic_list': pic_list}, template_name='loggers/pic_display.html')


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


def dump_database():
    with open(join(backup_path, datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S')+r'.txt'), 'w') as f:
        management.call_command('dumpdata', stdout=f)


# OLDER VIEWS

# def index(request):
#     model_list = inspect.getmembers(models, inspect.isclass)
#     log_list = form_dict.keys()
#
#     context = {'model_list': model_list, 'log_list': log_list}
#     return render(request, 'loggers/index.html', context)
#
#
# def browse_models(request, model_type):
#     class_list = inspect.getmembers(models, inspect.isclass)
#     target_index = [x for x, y in enumerate(class_list) if y[0] == model_type]
#
#     model_list = class_list[target_index[0]][1].objects.all()
#     context = {'model_type': model_type, 'model_list': model_list}
#     return render(request, 'loggers/browse.html', context)
#
# class DetailView(generic.DetailView):
#     model = models.Mouse
#     template_name = 'loggers/detail.html'
#
#
# def log_view(request, log_type):
#
#     # if this is a POST request we need to process the form data
#     if request.method == 'POST':
#         # create a form instance and populate it with data from the request:
#         form = form_dict[log_type](request.POST)
#         # check whether it's valid:
#         if form.is_valid():
#
#             # form.save()
#             # redirect to a new URL:
#             if 'checkbox' in request.POST:
#                 labfolderRequest.create_table(form, log_type)
#             return HttpResponseRedirect('/loggers/')
#
#     # if a GET (or any other method) we'll create a blank form
#     else:
#         form = form_dict[log_type]()
#
#     return render(request, 'loggers/logForm.html', {'form': form, 'log_type': log_type})
#
#
# def pic_viewer(request, pic_list):
#     # if this is a POST request we need to process the form data
#     if request.method == 'POST':
#         context = {'pic_list': pic_list}
#     else:
#         link_list = models.Window.objects.all()
#         context = {'link_list': link_list}
#     return render(request, 'loggers/pic_viewer.html', context)
#
#
# def query_manager(request):
#     # if this is a POST request we need to process the form data
#     if request.method == 'POST':
#         form = QueryForm(request.POST)
#         if form.is_valid():
#             model = form.cleaned_data['model_selector']
#             query_string = form.cleaned_data['query_string']
#             results = eval(model+'.objects.filter('+query_string+')')
#             context = {'form': form, 'results': results}
#
#     # if a GET (or any other method) we'll create a blank form
#     else:
#         form = QueryForm()
#
#         context = {'form': form}
#     return render(request, 'loggers/queries.html', context)

# STEPS OF THE TUTORIAL

# @api_view(['GET'])
# def api_root(request, format=None):
#     return Response({'users': reverse('user-list', request=request, format=format),
#                      'mice': reverse('mice-list', request=request, format=format)})


# class UserList(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#
#
# class UserDetail(generics.RetrieveAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

# class MouseDOB(generics.GenericAPIView):
#     queryset = models.Mouse.objects.all()
#     renderer_classes = (renderers.StaticHTMLRenderer,)
#
#     def get(self, request, *args, **kwargs):
#         mouse = self.get_object()
#         return Response(mouse.dob)
#
#
# class MouseList(generics.ListCreateAPIView):
#     queryset = models.Mouse.objects.all()
#     serializer_class = MouseSerializer
#     permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
#
#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)
#
#
# class MouseDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = models.Mouse.objects.all()
#     serializer_class = MouseSerializer
#     permission_classes = (permissions.IsAuthenticatedOrReadOnly,
#                           IsOwnerOrReadOnly,)

# class MouseList(APIView):
#
#     def get(self, request, format=None):
#         mice = models.Mouse.objects.all()
#         serializer = MouseSerializer(mice, many=True)
#         return Response(serializer.data)
#
#     def post(self, request, format=None):
#         serializer = MouseSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class MouseDetail(APIView):
#     """
#     Retrieve, update or delete a code snippet.
#     """
#     def get_object(self, pk):
#         try:
#             return models.Mouse.objects.get(pk=pk)
#         except models.Mouse.DoesNotExist:
#             raise Http404
#
#     def get(self, request, pk, format=None):
#         mouse = self.get_object(pk)
#         serializer = MouseSerializer(mouse)
#         return Response(serializer.data)
#
#     def put(self, request, pk, format=None):
#         mouse = self.get_object(pk)
#         serializer = MouseSerializer(mouse, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self, request, pk, format=None):
#         mouse = self.get_object(pk)
#         mouse.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

# def model_details(request, model_type, target_model):
#
#     # get the model instance
#
#     # get the fields and make a list
#     # pass the list to the renderer
#     context = {'details_list': details_list}
#     return render(request, 'loggers/detail.html', context)


