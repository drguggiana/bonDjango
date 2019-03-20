from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

extra_common_fields = ['url', 'mouse_name', 'owner']


class MouseSerializer(serializers.HyperlinkedModelSerializer):

    owner = serializers.ReadOnlyField(source='owner.username')
    window = serializers.HyperlinkedRelatedField(many=True, view_name='window-detail', read_only=True)
    surgery = serializers.HyperlinkedRelatedField(many=True, view_name='surgery-detail', read_only=True)
    two_photon = serializers.HyperlinkedRelatedField(many=True, view_name='twophoton-detail', read_only=True)
    intrinsic_imaging = serializers.HyperlinkedRelatedField(many=True,
                                                            view_name='intrinsicimaging-detail', read_only=True)
    vr_experiment = serializers.HyperlinkedRelatedField(many=True, view_name='vrexperiment-detail', read_only=True)

    class Meta:
        model = Mouse
        related_field_list = ['url', 'owner', 'window', 'surgery', 'two_photon', 'intrinsic_imaging', 'vr_experiment']
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

# TUTORIAL SERIALIZER CODE

# mouse_name = serializers.CharField(max_length=200)
# dob = serializers.DateField('date of birth', default=timezone.now())
# mouse_strain = serializers.CharField(max_length=100, default="C57BL/6")
#
# def create(self, validated_data):
#     return Mouse.objects.create(**validated_data)
#
# def update(self, instance, validated_data):
#     instance.mouse_name = validated_data.get('mouse_name', instance)
#     instance.dob = validated_data.get('dob', instance)
#     instance.mouse_strain = validated_data.get('mouse_strain', instance)
#     instance.save()
#     return instance
