from django.conf import settings
from django.db import models


class Crop(models.Model):
    STATUS_CHOICES = [
        ('Healthy', 'Healthy'),
        ('Minor Warning', 'Minor Warning'),
        ('Unhealthy', 'Unhealthy'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='crops',
        db_column='user_id',
    )
    name = models.CharField(max_length=150)
    crop_type = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    status = models.CharField(max_length=50, default='Healthy', choices=STATUS_CHOICES)
    last_observation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crops'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.crop_type})"


class FarmLog(models.Model):
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        related_name='farm_logs',
        db_column='crop_id',
    )
    activity_type = models.CharField(max_length=100)
    observed_condition = models.CharField(max_length=50)
    notes = models.TextField()
    log_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'farm_logs'
        ordering = ['-log_date', '-created_at']

    def __str__(self):
        return f"{self.activity_type} - {self.crop.name} ({self.log_date})"


class AIDiagnosis(models.Model):
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        related_name='ai_diagnoses',
        db_column='crop_id',
    )
    log = models.ForeignKey(
        FarmLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_diagnoses',
        db_column='log_id',
    )
    symptom_summary = models.TextField()
    diagnosis_title = models.CharField(max_length=255)
    treatment_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_diagnoses'
        ordering = ['-created_at']
        verbose_name = 'AI Diagnosis'
        verbose_name_plural = 'AI Diagnoses'

    def __str__(self):
        return f"{self.diagnosis_title} - {self.crop.name}"

