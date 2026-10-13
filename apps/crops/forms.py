from django import forms
from .models import Crop, FarmLog, AIDiagnosis


class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['name', 'crop_type', 'location', 'status', 'last_observation']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tomato Field A'}),
            'crop_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Roma Tomato'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. North Greenhouse'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'last_observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional initial observation or condition note...'}),
        }


class FarmLogForm(forms.ModelForm):
    class Meta:
        model = FarmLog
        fields = ['activity_type', 'observed_condition', 'notes', 'log_date']
        widgets = {
            'activity_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Field Inspection, Watering, Fertilizing'}),
            'observed_condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Healthy, Unhealthy / Sick, Minor Leaf Yellowing'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed activity & condition notes...'}),
            'log_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AIDiagnosisForm(forms.ModelForm):
    class Meta:
        model = AIDiagnosis
        fields = ['log', 'diagnosis_title', 'symptom_summary', 'treatment_plan']
        widgets = {
            'log': forms.Select(attrs={'class': 'form-select'}),
            'diagnosis_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Early Blight (Alternaria solani)'}),
            'symptom_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Summary of observed symptoms...'}),
            'treatment_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Recommended treatment actions and follow-up...'}),
        }

