from django.contrib import admin
from .models import Crop, FarmLog, AIDiagnosis


class FarmLogInLine(admin.TabularInline):
    model = FarmLog
    extra = 0
    fields = ('log_date', 'activity_type', 'observed_condition', 'notes')


class AIDiagnosisInLine(admin.StackedInline):
    model = AIDiagnosis
    extra = 0
    fields = ('diagnosis_title', 'symptom_summary', 'treatment_plan')


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'crop_type', 'location', 'status', 'user', 'created_at')
    list_filter = ('status', 'crop_type', 'created_at')
    search_fields = ('name', 'crop_type', 'location', 'user__username')
    inlines = [FarmLogInLine, AIDiagnosisInLine]


@admin.register(FarmLog)
class FarmLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'crop', 'activity_type', 'observed_condition', 'log_date', 'created_at')
    list_filter = ('activity_type', 'observed_condition', 'log_date')
    search_fields = ('crop__name', 'activity_type', 'notes')


@admin.register(AIDiagnosis)
class AIDiagnosisAdmin(admin.ModelAdmin):
    list_display = ('id', 'diagnosis_title', 'crop', 'log', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('diagnosis_title', 'symptom_summary', 'treatment_plan', 'crop__name')

