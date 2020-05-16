from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User, Group

# define the common extra kwargs
common_extra_kwargs = {'mouse': {'lookup_field': 'mouse_name'}}


# define a function to put the url first and then sort all the other fields
def sort_fields(fields):
    if 'mouse' in fields:
        fields.remove('mouse')
        sorted_fields = (['url', 'mouse'] + sorted(fields))
    else:
        sorted_fields = (['url'] + sorted(fields))
    return sorted_fields


# mouse serializer (comments will be basically the same for below)
class MouseSerializer(serializers.HyperlinkedModelSerializer):
    # define the fields associated with the model
    # owner is special since it has to be read only
    owner = serializers.ReadOnlyField(source='owner.username')
    # the rest are all hyperlinked so people can navigate in the API online
    # field contents involve establishing that the serializer will deal with many instances, the name of the view and
    # whether it's read only or not as default
    window = serializers.HyperlinkedRelatedField(many=True, view_name='window-detail', read_only=True,
                                                 lookup_field='slug')
    surgery = serializers.HyperlinkedRelatedField(many=True, view_name='surgery-detail', read_only=True,
                                                  lookup_field='slug')
    two_photon = serializers.HyperlinkedRelatedField(many=True, view_name='twophoton-detail', read_only=True)
    intrinsic_imaging = serializers.HyperlinkedRelatedField(many=True,
                                                            view_name='intrinsicimaging-detail', read_only=True)
    vr_experiment = serializers.HyperlinkedRelatedField(many=True, view_name='vrexperiment-detail', read_only=True,
                                                        lookup_field='slug')
    video_experiment = serializers.HyperlinkedRelatedField(many=True, view_name='videoexperiment-detail', read_only=True
                                                           , lookup_field='slug')

    score_sheet = serializers.HyperlinkedRelatedField(many=True, view_name='scoresheet-detail', read_only=True,
                                                      lookup_field='slug')
    immuno_stain = serializers.HyperlinkedRelatedField(many=True, view_name='immunostain-detail', read_only=True)

    restriction = serializers.HyperlinkedRelatedField(many=True, view_name='restriction-detail', read_only=True,
                                                      lookup_field='slug')
    strain_name = serializers.ReadOnlyField()

    # django specific Meta class
    class Meta:
        # define the model the serializer belongs to
        model = Mouse
        # define the search fields as anything that's not a relation
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = {'url': {'lookup_field': 'mouse_name'}, 'restriction': {'lookup_field': 'slug'},
                        'window': {'lookup_field': 'slug'}}


class ProfileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Profile
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = {'user': {'lookup_field': 'username'}}


class UserSerializer(serializers.HyperlinkedModelSerializer):

    main_path = serializers.ReadOnlyField(source='profile.main_path',)

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'mouse', 'groups', 'main_path')

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'username'}


class GroupSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Group
        fields = ('url', 'name', 'user_set')

        extra_kwargs = {'user_set': {'lookup_field': 'username'}}


class WindowSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Window
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug'}


class SurgerySerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Surgery
        fields = ([f.name for f in model._meta.get_fields()])
        fields.remove('slug')
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug'}


class RestrictionTypeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = RestrictionType
        fields = ([f.name for f in model._meta.get_fields()])
        fields.remove('slug_restrictionType')
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug_restrictionType'}
        extra_kwargs['restriction'] = {'lookup_field': 'slug'}


class RestrictionSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    # start_date = serializers.ReadOnlyField()
    end_date = serializers.ReadOnlyField()

    class Meta:
        model = Restriction
        fields = ([f.name for f in model._meta.get_fields()])
        fields.remove('slug')
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug'}
        extra_kwargs['restriction_type'] = {'lookup_field': 'slug_restrictionType'}


class VideoExperimentSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    # preproc_files = serializers.HyperlinkedRelatedField(
    #                     view_name='analyzeddata-detail', many=True, read_only=True, lookup_field='slug')
    # mouse = serializers.HyperlinkedRelatedField(
    #                     view_name='mouse-detail', read_only=True, lookup_field='mouse_name')

    class Meta:
        model = VideoExperiment
        fields = ([f.name for f in model._meta.get_fields()])
        # fields.remove('slug')
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug'}
        extra_kwargs['preproc_files'] = {'lookup_field': 'slug'}


class TwoPhotonSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    preproc_files = serializers.HyperlinkedRelatedField(
                        view_name='analyzeddata-detail', many=True, read_only=True, lookup_field='slug')

    class Meta:
        model = TwoPhoton
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        # extra_kwargs['preproc_files'] = {'lookup_field': 'slug'}


class IntrinsicImagingSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    preproc_files = serializers.HyperlinkedRelatedField(
                        view_name='analyzeddata-detail', many=True, read_only=True, lookup_field='slug')

    class Meta:
        model = IntrinsicImaging
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        # extra_kwargs['preproc_files'] = {'lookup_field': 'slug'}


class VRExperimentSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    preproc_files = serializers.HyperlinkedRelatedField(
                        view_name='analyzeddata-detail', many=True, read_only=True, lookup_field='slug')

    class Meta:
        model = VRExperiment
        fields = ([f.name for f in model._meta.get_fields()])
        # fields.remove('slug')
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug'}
        # extra_kwargs['preproc_files'] = {'lookup_field': 'slug'}


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Project
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = {'members': {'lookup_field': 'username'}}


class LicenseSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = License
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = {'members': {'lookup_field': 'username'}}


class StrainSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Strain
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()


class ScoreSheetSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = ScoreSheet
        fields = ([f.name for f in model._meta.get_fields()])
        fields.remove('slug')
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['url'] = {'lookup_field': 'slug'}


class ImmunoStainSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = ImmunoStain
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()


class MouseSetSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = MouseSet
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)

        extra_kwargs = common_extra_kwargs.copy()
        extra_kwargs['restrictiontype'] = {'lookup_field': 'slug_restrictionType'}


class ExperimentTypeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = ExperimentType
        fields = ([f.name for f in model._meta.get_fields()])
        fields = sort_fields(fields)
        extra_kwargs = {'users': {'lookup_field': 'username'},
                        'vrexperiment_type': {'lookup_field': 'slug'},
                        'videoexperiment_type': {'lookup_field': 'slug'},
                        'surgery_type': {'lookup_field': 'slug'}}


class AnalyzedDataSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = AnalyzedData
        fields = ([f.name for f in model._meta.get_fields()])
        # fields.remove('slug')
        fields = sort_fields(fields)
        extra_kwargs = {'url': {'lookup_field': 'slug'},
                        'vr_analysis': {'lookup_field': 'slug'},
                        'video_analysis': {'lookup_field': 'slug'},
                        'figure_analysis': {'lookup_field': 'slug'}
                        }


class FigureSerializer(serializers.HyperlinkedModelSerializer):
    preproc_files = serializers.HyperlinkedRelatedField(
        view_name='analyzeddata-detail', many=True, read_only=True, lookup_field='slug')

    class Meta:
        model = Figure
        fields = ([f.name for f in model._meta.get_fields()])
        # fields.remove('slug')
        fields = sort_fields(fields)
        extra_kwargs = {'url': {'lookup_field': 'slug'},
                        }


class GeneralSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = None
        extra_kwargs = None


class PythonSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = None
        extra_kwargs = None


# obtained from https://www.django-rest-framework.org/api-guide/serializers/#example
# class DynamicFieldsModelSerializer(serializers.ModelSerializer):
#     """
#     A ModelSerializer that takes an additional `fields` argument that
#     controls which fields should be displayed.
#     """
#
#     def __init__(self, *args, **kwargs):
#
#         fields = kwargs.pop('fields', None)
#         # Instantiate the superclass normally
#         super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
#
#         # fields = self.context['request'].query_params.get('fields')
#         if fields is not None:
#             # fields = fields.split(',')
#             # Drop any fields that are not specified in the `fields` argument.
#             allowed = set(fields)
#             existing = set(self.fields.keys())
#             for field_name in existing - allowed:
#                 self.fields.pop(field_name)
# Include this in the target serializer, Groups in this case
# users = serializers.SerializerMethodField()
# def get_users(self, obj):
#     users_list = User.objects.filter(groups__name=obj.name)
#     users_serial = UserSerializer(users_list, many=True, context={'request': self.context['request']}
#                                   , fields=['url', 'username'])
#     return users_serial.data
