from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

# define fields to add to the serializer that are common to almost all models
# TODO: should probs add project, license here
extra_common_fields = ['url', 'mouse_name', 'owner']


# mouse serializer (comments will be basically the same for below)
class MouseSerializer(serializers.HyperlinkedModelSerializer):
    # define the fields associated with the model
    # owner is special since it has to be read only
    # TODO: so will project and license I guess
    owner = serializers.ReadOnlyField(source='owner.username')
    # the rest are all hyperlinked so people can navigate in the API online
    # field contents involve establishing that the serializer will deal with many instances, the name of the view and
    # whether it's read only or not as default
    window = serializers.HyperlinkedRelatedField(many=True, view_name='window-detail', read_only=True)
    surgery = serializers.HyperlinkedRelatedField(many=True, view_name='surgery-detail', read_only=True)
    two_photon = serializers.HyperlinkedRelatedField(many=True, view_name='twophoton-detail', read_only=True)
    intrinsic_imaging = serializers.HyperlinkedRelatedField(many=True,
                                                            view_name='intrinsicimaging-detail', read_only=True)
    vr_experiment = serializers.HyperlinkedRelatedField(many=True, view_name='vrexperiment-detail', read_only=True)

    # django specific Meta class
    class Meta:
        # define the model the serializer belongs to
        model = Mouse
        # define the related fields, which in this case is most of them
        related_field_list = ['url', 'owner', 'window', 'surgery', 'two_photon', 'intrinsic_imaging', 'vr_experiment']
        # define the search fields as anything that's not a relation
        fields = ([f.name for f in Mouse._meta.get_fields() if not f.is_relation]+related_field_list)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    mouse = serializers.HyperlinkedRelatedField(many=True, view_name='mouse-detail', read_only=True)

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'mouse')


class WindowSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Window
        fields = ([f.name for f in Window._meta.get_fields() if not f.is_relation]+extra_common_fields)


class SurgerySerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Surgery
        fields = ([f.name for f in Surgery._meta.get_fields() if not f.is_relation]+extra_common_fields)


class CricketSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Cricket
        fields = ([f.name for f in Cricket._meta.get_fields() if not f.is_relation]+['url', 'owner'])


class TwoPhotonSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = TwoPhoton
        fields = ([f.name for f in TwoPhoton._meta.get_fields() if not f.is_relation]+extra_common_fields)


class IntrinsicImagingSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = IntrinsicImaging
        fields = ([f.name for f in IntrinsicImaging._meta.get_fields() if not f.is_relation]+extra_common_fields)


class VRExperimentSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = VRExperiment
        fields = ([f.name for f in VRExperiment._meta.get_fields() if not f.is_relation]+extra_common_fields)


