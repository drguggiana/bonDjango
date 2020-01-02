from django import forms
from . import models

# define the forms based on the models, one for each
MouseForm = forms.modelform_factory(models.Mouse, fields='__all__')
WindowForm = forms.modelform_factory(models.Window, fields='__all__')
SurgeryForm = forms.modelform_factory(models.Surgery, fields='__all__')
VideoExperimentForm = forms.modelform_factory(models.VideoExperiment, fields='__all__')
TwoPhotonForm = forms.modelform_factory(models.TwoPhoton, fields='__all__')
IntrinsicImagingForm = forms.modelform_factory(models.IntrinsicImaging, fields='__all__')
VRExperimentForm = forms.modelform_factory(models.VRExperiment, fields='__all__')

# define a dictionary with the model name mapping to its respective form
# TODO: this seems redundant, can find better way, probably just based on a list
form_dict = {'mouse': MouseForm, 'window': WindowForm, 'surgery': SurgeryForm,
             'video_experiment': VideoExperimentForm, 'two_photon': TwoPhotonForm,
             'intrinsic_imaging': IntrinsicImagingForm, 'vr_experiment': VRExperimentForm}

