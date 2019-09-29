from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User


null_value = False
default_user = None


class Project(models.Model):
    project_name = models.CharField(max_length=200, default="N/A", primary_key=True)
    owner = models.ForeignKey('auth.User', related_name='project', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    members = models.ManyToManyField('auth.User', related_name='project_members')

    def __str__(self):
        return self.project_name


class License(models.Model):
    license_name = models.CharField(max_length=200, default="N/A", primary_key=True)
    license_id = models.CharField(max_length=200, default="N/A")
    expiration_date = models.DateField('date of expiration', default=timezone.localdate)
    project = models.ManyToManyField('Project', related_name='license')
    owner = models.ForeignKey('auth.User', related_name='license', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    members = models.ManyToManyField('auth.User', related_name='license_members')

    def __str__(self):
        return self.license_name


class ExperimentType(models.Model):
    experiment_name = models.CharField(max_length=200, default="N/A", primary_key=True)
    users = models.ManyToManyField('auth.User', related_name='experiment_users')
    owner = models.ForeignKey('auth.User', related_name='experiment', on_delete=models.CASCADE,
                              null=null_value, default=default_user)


class Strain(models.Model):
    strain_name = models.CharField(max_length=200, default='C57Bl6', primary_key=True)
    ab_path = models.CharField(max_length=1000, default="N/A")
    im_path = models.CharField(max_length=200, default="N/A")
    license = models.ManyToManyField('License', related_name='strain', through='MouseSet')
    owner = models.ForeignKey('auth.User', related_name='strain', on_delete=models.CASCADE,
                              null=null_value, default=default_user)

    def __str__(self):
        return self.strain_name


class MouseSet(models.Model):
    mouse_set_name = models.CharField(max_length=200, default="N/A", primary_key=True)
    strain = models.ForeignKey('Strain', related_name='mouseset', on_delete=models.CASCADE)
    license = models.ForeignKey('License', related_name='mouseset', on_delete=models.CASCADE)
    max_number = models.IntegerField('Max number of animals', default=1)
    current_number = models.IntegerField('Current number of animals', default=0)
    owner = models.ForeignKey('auth.User', related_name='mouseset', on_delete=models.CASCADE,
                              null=null_value, default=default_user)


# mouse model
class Mouse(models.Model):
    male = 'm'
    female = 'f'
    GENDERS = ((male, 'Male'), (female, 'Female'))

    mouse_name = models.CharField(max_length=200, primary_key=True)
    dob = models.DateField('date of birth', default=timezone.localdate)
    strain_name = models.CharField(max_length=200, default="N/A", null=True)
    mouse_gender = models.CharField(max_length=100, default="female", choices=GENDERS)
    mouse_set = models.ForeignKey('MouseSet', related_name='mouse', on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey('auth.User', related_name='mouse', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    # TODO: BooleanField to indicate if the animal is under food restriction, somehow check when period is over

    def __str__(self):
        return self.mouse_name


class ScoreSheet(models.Model):
    # define the score choices
    na = 'N/A'
    zero = '0'
    one = '1'
    two = '2'
    SCORE_LIST = [(na, 'N/A'), (zero, '0'), (one, '1'), (two, '2')]
    CARPRO_LIST = [(zero, '0'), (one, '1')]

    sheet_date = models.DateTimeField('date of scoring', default=timezone.now)
    mouse = models.ForeignKey(Mouse, related_name='score_sheet', on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='score_sheet', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    carprofen = models.CharField('Carprofen', max_length=3, choices=CARPRO_LIST)
    weight = models.FloatField('Weight (g)', default=0)
    food_consumed = models.FloatField('Food Consumed (g)', default=0)
    behavior = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")
    posture_fur = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")
    water_food_uptake = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")
    general_condition = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")
    skin_turgor = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")

    slug = models.SlugField(unique=True)

    brain_surgery = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")
    lid_suture = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")
    inutero_electroporation = models.CharField(max_length=3, choices=SCORE_LIST, default="N/A")

    notes = models.TextField(max_length=1000, default="N/A")

    def save(self, *args, **kwargs):
        self.slug = slugify(str(self.sheet_date)[0:19])
        super().save(*args, **kwargs)


# TODO: implement cache to not have to reenter every entry
class Window(models.Model):
    # define the possible regions
    V1 = 'V1'
    mPFC = 'mPFC'
    HVAs = 'HVAs'
    S1 = 'S1'
    S1V1 = 'S1V1'
    A1 = 'A1'

    REGION_LIST = ((V1, 'Primary visual cortex'), (mPFC, 'medial Prefrontal Cortex'), (HVAs, 'Higher Visual Areas'),
                   (S1, 'Primary somatosensory cortex'), (A1, 'Primary auditory cortex'),
                   (S1V1, "Primary visual and somatosensory cortex"))
    mouse = models.ForeignKey(Mouse, related_name='window', on_delete=models.CASCADE)
    window_date = models.DateTimeField('date window was taken', default=timezone.now)
    bfPath = models.CharField(max_length=1000, default="N/A")
    flPath = models.CharField(max_length=1000, default="N/A")
    other_path = models.CharField(max_length=1000, default="N/A")

    region = models.CharField(max_length=100, default=V1, choices=REGION_LIST)
    owner = models.ForeignKey('auth.User', related_name='window', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    testPath = models.CharField(max_length=1000, default='N/A', null=True)

    def __str__(self):
        return self.mouse.mouse_name + '_' + self.region


# duration as duration field
class Surgery(models.Model):
    # define the types of anesthesia
    FMM = 'FMM'
    iso = 'Iso'

    ANESTHESIA_LIST = [(FMM, 'FMM'), (iso, 'Isofluorane')]
    mouse = models.ForeignKey(Mouse, related_name='surgery', on_delete=models.CASCADE)
    date = models.DateTimeField('date of operation', default=timezone.now)
    experiment_type = models.ManyToManyField('ExperimentType', related_name='surgery_type')
    duration = models.IntegerField('Duration in minutes of the procedure', default=1)
    notes = models.TextField(max_length=5000, default="N/A")
    anesthesia = models.CharField(max_length=100, default=FMM, choices=ANESTHESIA_LIST)
    owner = models.ForeignKey('auth.User', related_name='surgery', on_delete=models.CASCADE,
                              null=null_value, default=default_user)

    def __str__(self):
        return self.mouse.mouse_name+'_'+str(self.experiment_type.all()[0].authorization_name)


# duration as duration field
class RestrictionType(models.Model):
    # define the types of restriction
    food = 'Food'
    water = 'Water'

    RESTRICTION_LIST = [(food, 'Food'), (water, 'Water')]
    duration = models.IntegerField('Duration in days of the restriction in days', default=1)
    restricted_element = models.CharField(max_length=100, default=food, choices=RESTRICTION_LIST)
    mouse_set = models.ForeignKey(MouseSet, related_name='restrictiontype', on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='restrictiontype', on_delete=models.CASCADE,
                              null=null_value, default=default_user)

    # def __str__(self):
    #     return self.mouse.mouse_name + '_' + str(self.experiment_type.all()[0].authorization_name)


class Restriction(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='restriction', on_delete=models.CASCADE)
    restriction_type = models.ForeignKey(RestrictionType, related_name='restriction', on_delete=models.CASCADE)
    start_date = models.DateTimeField('date of restriction start', default=timezone.now)
    end_date = models.DateTimeField('date of restriction end', null=True)
    ongoing = models.BooleanField('Is the restriction enabled', default=True)

    notes = models.TextField(max_length=5000, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='restriction', on_delete=models.CASCADE,
                              null=null_value, default=default_user)


class Cricket(models.Model):
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulus = models.CharField(max_length=200, default="N/A")
    notes = models.TextField(max_length=1000, default="N/A")
    path = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='cricket', on_delete=models.CASCADE,
                              null=null_value, default=default_user)

    def __str__(self):
        return self.date+'_'+self.stimulus


class TwoPhoton(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='two_photon', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulusPath = models.CharField(max_length=200, default="N/A")
    scopePath = models.CharField(max_length=200, default="N/A")
    auxPath = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='two_photon', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    experiment_type = models.ManyToManyField('ExperimentType', related_name='twophoton_type')

    def __str__(self):
        return self.mouse.mouse_name+'_'+self.stimulusPath


class IntrinsicImaging(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='intrinsic_imaging', on_delete=models.CASCADE)
    path = models.CharField(max_length=200, default="N/A")
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    region = models.CharField(max_length=100, default="V1")
    stimulus = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='intrinsic_imaging', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    experiment_type = models.ManyToManyField('ExperimentType', related_name='intrinsicimaging_type')
    mapPath = models.CharField(max_length=1000, default="N/A")

    def __str__(self):
        return self.mouse.mouse_name+'_'+self.stimulus+'_'+self.region


class VRExperiment(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='vr_experiment', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulus = models.CharField(max_length=200, default="N/A")
    fluorescencePath = models.CharField(max_length=200, default="N/A")
    trackPath = models.CharField(max_length=200, default="N/A")
    stimulusPath = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='vr_experiment', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    notes = models.TextField(max_length=5000, default="N/A")
    experiment_type = models.ManyToManyField('ExperimentType', related_name='vrexperiment_type')

    def __str__(self):
        return self.mouse.mouse_name+'_'+self.stimulus


class ImmunoStain(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='immuno_stain', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    im_path = models.CharField(max_length=200, default="N/A")
    other_path = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='immunostain', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    notes = models.TextField(max_length=1000, default="N/A")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    main_path = models.CharField(max_length=1000, default='"N/A')
    ScoreSheet_path = models.CharField(max_length=1000, default='"N/A', null=True)
    Window_path = models.CharField(max_length=1000, default='"N/A', null=True)
    Cricket_path = models.CharField(max_length=1000, default='"N/A', null=True)
    TwoPhoton_path = models.CharField(max_length=1000, default='"N/A', null=True)
    IntrinsicImaging_path = models.CharField(max_length=1000, default='"N/A', null=True)
    VRExperiment_path = models.CharField(max_length=1000, default='"N/A', null=True)
    ImmunoStain_path = models.CharField(max_length=1000, default='"N/A', null=True)







