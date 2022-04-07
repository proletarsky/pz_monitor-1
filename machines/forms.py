import datetime

from django import forms
from django.forms import widgets
from django.forms.models import inlineformset_factory, modelformset_factory
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from .models import Reason, ClassifiedInterval, Equipment, Repair_rawdata, Area
from django.utils import timezone
from django.contrib.auth.models import User


class ReasonForm(forms.ModelForm):
    class Meta:
        model = Reason
        exclude = ['']


class EquipmentDetailForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker'}))

    class Meta:
        model = Equipment
        fields = ['model']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'datepicker'})
        }

    def save(self, commit=True):
        """
        prevent form from saving object
        :param commit:
        :return:
        """
        return self.instance


class ClassifiedIntervalForm(forms.ModelForm):
    class Meta:
        model = ClassifiedInterval
        fields = ['user_classification']

    def __init__(self, *args, **kwargs):
        super(ClassifiedIntervalForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            if instance.end.date() > datetime.date(year=2022, month=4, day=10):
                self.fields['user_classification'].queryset = Reason.objects.filter(is_operator=True, selectable=True)
            else:
                self.fields['user_classification'].queryset = Reason.objects.filter(is_operator=True)
            if self.instance.automated_classification.is_working:
                self.fields['user_classification'].widget.attrs['class'] = 'hidden'


ClassifiedIntervalFormSet = modelformset_factory(ClassifiedInterval, form=ClassifiedIntervalForm,
                                                 extra=0, can_delete=False)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cd['password2']


class Repairform(forms.ModelForm):
    class Meta:
        model = Repair_rawdata
        fields = ('id', 'machines_id', 'repair_job_status', 'repairer_master_reason', 'repair_reason', 'repair_comment')
