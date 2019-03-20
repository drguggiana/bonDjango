import inspect

from django import forms

from . import models

MouseForm = forms.modelform_factory(models.Mouse, fields='__all__')
WindowForm = forms.modelform_factory(models.Window, fields='__all__')
SurgeryForm = forms.modelform_factory(models.Surgery, fields='__all__')
CricketForm = forms.modelform_factory(models.Cricket, fields='__all__')
TwoPhotonForm = forms.modelform_factory(models.TwoPhoton, fields='__all__')
IntrinsicImagingForm = forms.modelform_factory(models.IntrinsicImaging, fields='__all__')
VRExperimentForm = forms.modelform_factory(models.VRExperiment, fields='__all__')

form_dict = {'mouse': MouseForm, 'window': WindowForm, 'surgery': SurgeryForm,
             'cricket': CricketForm, 'two_photon': TwoPhotonForm,
             'intrinsic_imaging': IntrinsicImagingForm, 'vr_experiment': VRExperimentForm}


class QueryForm(forms.Form):
    classMembers = inspect.getmembers(models, inspect.isclass)

    classList = [(model[0], model[0]) for model in classMembers]
    model_selector = forms.ChoiceField(label='Select a data type', choices=classList)
    query_string = forms.CharField(label='Filter query', max_length=1000)
