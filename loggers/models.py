from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User
from os.path import basename


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
    license_path = models.CharField(max_length=500, default="N/A")
    expiration_date = models.DateField('date of expiration', default=timezone.localdate)
    project = models.ManyToManyField('Project', related_name='license')
    score_sheet_path = models.CharField(max_length=200, default='N/A')
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

    def __str__(self):
        return self.experiment_name


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

    def __str__(self):
        return self.mouse_set_name


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

    mouse = models.ForeignKey(Mouse, related_name='score_sheet', on_delete=models.CASCADE)
    sheet_date = models.DateTimeField('date of scoring', default=timezone.now)
    owner = models.ForeignKey('auth.User', related_name='score_sheet', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    carprofen = models.CharField('Carprofen', max_length=3, choices=CARPRO_LIST, default=zero)
    weight = models.FloatField('Weight (g)', default=0)
    food_consumed = models.FloatField('Food Consumed (g)', default=0)
    behavior = models.CharField(max_length=3, choices=SCORE_LIST, default="0")
    posture_fur = models.CharField(max_length=3, choices=SCORE_LIST, default="0")
    water_food_uptake = models.CharField(max_length=3, choices=SCORE_LIST, default="0")
    general_condition = models.CharField(max_length=3, choices=SCORE_LIST, default="0")
    skin_turgor = models.CharField(max_length=3, choices=SCORE_LIST, default="0")
    brain_surgery = models.CharField(max_length=3, choices=SCORE_LIST, default="0")

    notes = models.TextField(max_length=1000, default="N/A")

    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(str(self.sheet_date)[0:19])
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


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
    flgreenPath = models.CharField(max_length=1000, default="N/A")
    otherPath = models.CharField(max_length=1000, default="N/A")

    region = models.CharField(max_length=100, default=V1, choices=REGION_LIST)
    owner = models.ForeignKey('auth.User', related_name='window', on_delete=models.CASCADE,
                              null=null_value, default=default_user)

    slug = models.SlugField(unique=True, default=timezone.now())

    def save(self, *args, **kwargs):
        self.slug = slugify(str(self.window_date)[0:19]+'_'+self.mouse.mouse_name+'_'+self.region)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


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

    slug = models.SlugField(unique=True, default=str(timezone.now()))

    def save(self, *args, **kwargs):
        self.slug = slugify('_'.join((str(self.date)[0:19], str(self.mouse))))
        super().save()

    def __str__(self):
        return self.slug


# duration as duration field
class RestrictionType(models.Model):
    # define the types of restriction
    food = 'Food'
    water = 'Water'

    RESTRICTION_LIST = [(food, 'Food'), (water, 'Water')]
    duration = models.IntegerField('Duration of the restriction in days', default=1)
    restricted_element = models.CharField(max_length=100, default=food, choices=RESTRICTION_LIST)
    mouse_set = models.ForeignKey(MouseSet, related_name='restrictiontype', on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='restrictiontype', on_delete=models.CASCADE,
                              null=null_value, default=default_user)

    slug_restrictionType = models.SlugField(unique=True, default=str(timezone.now()))

    def save(self, *args, **kwargs):
        self.slug_restrictionType = slugify(str(self.mouse_set.mouse_set_name) + '_' + str(self.restricted_element))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug_restrictionType


class Restriction(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='restriction', on_delete=models.CASCADE)
    restriction_type = models.ForeignKey(RestrictionType, related_name='restriction', on_delete=models.CASCADE)
    start_date = models.DateTimeField('date of restriction start', default=timezone.now)
    end_date = models.DateTimeField('date of restriction end', null=True)
    ongoing = models.BooleanField('Is the restriction enabled', default=True)

    notes = models.TextField(max_length=5000, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='restriction', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    slug = models.SlugField(unique=True, default=str(timezone.now))

    def save(self, *args, **kwargs):
        self.slug = slugify(str(self.start_date)[0:19])
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


class VideoExperiment(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='video_experiment', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    result = models.CharField(max_length=200, default="N/A")
    lighting = models.CharField(max_length=200, default="N/A")
    rig = models.CharField(max_length=200, default="N/A")
    imaging = models.CharField(max_length=200, default="N/A")

    sync_path = models.CharField(max_length=200, default="N/A")
    bonsai_path = models.CharField(max_length=200, default="N/A")
    avi_path = models.CharField(max_length=200, default="N/A")
    fluo_path = models.CharField(max_length=200, default="N/A")
    tif_path = models.CharField(max_length=200, default="N/A")
    dlc_path = models.CharField(max_length=200, default="N/A")
    preproc_files = models.ManyToManyField('AnalyzedData', related_name='video_analysis', blank=True)

    owner = models.ForeignKey('auth.User', related_name='video_experiment', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    notes = models.TextField(max_length=5000, default="N/A")
    experiment_type = models.ManyToManyField('ExperimentType', related_name='videoexperiment_type')

    slug = models.SlugField(unique=True, default=str(timezone.now), max_length=200)

    def save(self, *args, **kwargs):
        self.slug = slugify(basename(str(self.bonsai_path)[:-4]))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


class TwoPhoton(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='two_photon', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    stimulusPath = models.CharField(max_length=200, default="N/A")
    scopePath = models.CharField(max_length=200, default="N/A")
    auxPath = models.CharField(max_length=200, default="N/A")
    owner = models.ForeignKey('auth.User', related_name='two_photon', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    preproc_files = models.ManyToManyField('AnalyzedData', related_name='twophoton_analysis')
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
    preproc_files = models.ManyToManyField('AnalyzedData', related_name='intrinsic_analysis')
    experiment_type = models.ManyToManyField('ExperimentType', related_name='intrinsicimaging_type')
    mapPath = models.CharField(max_length=1000, default="N/A")

    def __str__(self):
        return self.mouse.mouse_name+'_'+self.stimulus+'_'+self.region


class VRExperiment(models.Model):
    mouse = models.ForeignKey(Mouse, related_name='vr_experiment', on_delete=models.CASCADE)
    date = models.DateTimeField('date of the experiment', default=timezone.now)
    result = models.CharField(max_length=200, default="N/A")
    lighting = models.CharField(max_length=200, default="N/A")
    rig = models.CharField(max_length=200, default="N/A")
    imaging = models.CharField(max_length=200, default="N/A")

    sync_path = models.CharField(max_length=200, default="N/A")
    track_path = models.CharField(max_length=200, default="N/A")
    bonsai_path = models.CharField(max_length=200, default="N/A")
    avi_path = models.CharField(max_length=200, default="N/A")
    fluo_path = models.CharField(max_length=200, default="N/A")
    tif_path = models.CharField(max_length=200, default="N/A")
    dlc_path = models.CharField(max_length=200, default="N/A")

    preproc_files = models.ManyToManyField('AnalyzedData', related_name='vr_analysis', blank=True)

    owner = models.ForeignKey('auth.User', related_name='vr_experiment', on_delete=models.CASCADE,
                              null=null_value, default=default_user)
    notes = models.TextField(max_length=5000, default="N/A")
    experiment_type = models.ManyToManyField('ExperimentType', related_name='vrexperiment_type')

    slug = models.SlugField(unique=True, default=str(timezone.now))

    def save(self, *args, **kwargs):
        self.slug = slugify(basename(str(self.bonsai_path)[:-4]))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


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
    TwoPhoton_path = models.CharField(max_length=1000, default='"N/A', null=True)
    IntrinsicImaging_path = models.CharField(max_length=1000, default='"N/A', null=True)
    VideoExperiment_path = models.CharField(max_length=1000, default='"N/A', null=True)
    VRExperiment_path = models.CharField(max_length=1000, default='"N/A', null=True)
    ImmunoStain_path = models.CharField(max_length=1000, default='"N/A', null=True)
    Figure_path = models.CharField(max_length=1000, default='"N/A', null=True)


class AnalyzedData(models.Model):
    analysis_type = models.CharField(max_length=200, default="N/A")
    analysis_path = models.CharField(max_length=200, default="N/A")
    input_path = models.TextField(max_length=50000, default="N/A")
    pic_path = models.CharField(max_length=200, default="N/A")
    result = models.CharField(max_length=200, default="N/A")
    lighting = models.CharField(max_length=200, default="N/A")
    rig = models.CharField(max_length=200, default="N/A")
    imaging = models.CharField(max_length=200, default="N/A")
    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(max_length=5000, default="N/A")

    slug = models.SlugField(unique=True, default=timezone.now, max_length=200)

    def __str__(self):
        return self.slug


class Figure(models.Model):
    figure_type = models.CharField(max_length=200, default="N/A")
    figure_path = models.CharField(max_length=200, default="N/A")
    input_path = models.TextField(max_length=50000, default="N/A")
    preproc_files = models.ManyToManyField('AnalyzedData', related_name='figure_analysis')

    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(max_length=5000, default="N/A")

    slug = models.SlugField(unique=True, default=timezone.now, max_length=200)

    def __str__(self):
        return self.slug
