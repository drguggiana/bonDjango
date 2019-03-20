from django.db import models
from django.utils import timezone

# Create your models here.


# class License(models.Model):
#     license_name = models.CharField(max_length=200)
#     number_of_animals = models.IntegerField
#
#     def __str__(self):
#         return self.license_name


class Mouse(models.Model):
    mouse_name = models.CharField(max_length=200)
    dob = models.DateField('date of birth', default=timezone.localdate)
    mouse_strain = models.CharField(max_length=100, default="C57BL/6")
    # mouse_gender = models.CharField(max_length=100, default="C57BL/6")
    owner = models.ForeignKey('auth.User', related_name='mouse', on_delete=models.CASCADE)
    # license_name = models.ForeignKey(License, related_name='mouse', on_delete=models.CASCADE)

    def __str__(self):
        return self.mouse_name


class Window(models.Model):
    mouse_name = models.ForeignKey(Mouse, related_name='window', on_delete=models.CASCADE)
    window_date = models.DateTimeField('date window was taken', default=timezone.now)
    bfPath = models.CharField(max_length=1000, default="N/A")
    flPath = models.CharField(max_length=1000, default="N/A")
    other_path = models.CharField(max_length=1000, default="N/A")
    region = models.CharField(max_length=100, default="V1")
    owner = models.ForeignKey('auth.User', related_name='window', on_delete=models.CASCADE)

    def __str__(self):
        return self.mouse_name.mouse_name + '_' + self.region


class Surgery(models.Model):
    mouse_name = models.ForeignKey(Mouse, related_name='surgery', on_delete=models.CASCADE)
    date = models.DateTimeField('date of operation', default=timezone.now)
    type = models.CharField(max_length=100, default="Headbar/Craniotomy")
    duration = models.IntegerField
    notes = models.CharField(max_length=5000, default="N/A")
    anesthesia = models.CharField(max_length=100, default="FMM")
    owner = models.ForeignKey('auth.User', related_name='surgery', on_delete=models.CASCADE)

    def __str__(self):
        return self.mouse_name+'_'+self.type


class Cricket(models.Model):
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulus = models.CharField(max_length=200, default="N/A")
    notes = models.CharField(max_length=1000, default="N/A")
    path = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='cricket', on_delete=models.CASCADE)

    def __str__(self):
        return self.date+'_'+self.stimulus


class TwoPhoton(models.Model):
    mouse_name = models.ForeignKey(Mouse, related_name='two_photon', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulusPath = models.CharField(max_length=200, default="N/A")
    scopePath = models.CharField(max_length=200, default="N/A")
    auxPath = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='two_photon', on_delete=models.CASCADE)

    def __str__(self):
        return self.mouse_name+'_'+self.stimulusPath
    
    
class IntrinsicImaging(models.Model):
    mouse_name = models.ForeignKey(Mouse, related_name='intrinsic_imaging', on_delete=models.CASCADE)
    path = models.CharField(max_length=200, default="N/A")
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    region = models.CharField(max_length=100, default="V1")
    stimulus = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='intrinsic_imaging', on_delete=models.CASCADE)

    def __str__(self):
        return self.mouse_name+'_'+self.stimulus+'_'+self.region


class VRExperiment(models.Model):
    mouse_name = models.ForeignKey(Mouse, related_name='vr_experiment', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulus = models.CharField(max_length=200, default="N/A")
    notes = models.CharField(max_length=1000, default="N/A")
    fluorescencePath = models.CharField(max_length=200, default="N/A")
    trackPath = models.CharField(max_length=200, default="N/A")
    stimulusPath = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='vr_experiment', on_delete=models.CASCADE)

    def __str__(self):
        return self.mouse_name+'_'+self.stimulus


