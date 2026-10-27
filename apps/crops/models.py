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
    planting_date = models.DateField(blank=True, null=True)
    expected_harvest_date = models.DateField(blank=True, null=True)
    estimated_yield = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_image(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return None

    @property
    def days_until_harvest(self):
        if not self.expected_harvest_date:
            return None
        import datetime
        return (self.expected_harvest_date - datetime.date.today()).days

    @property
    def growth_progress(self):
        if not self.planting_date or not self.expected_harvest_date:
            return None
        import datetime
        total_days = (self.expected_harvest_date - self.planting_date).days
        if total_days <= 0:
            return 100
        elapsed = (datetime.date.today() - self.planting_date).days
        if elapsed <= 0:
            return 0
        return min(100, max(0, round((elapsed / total_days) * 100)))

    @property
    def harvest_badge(self):
        days = self.days_until_harvest
        if days is None:
            return None
        if days < 0:
            return {
                'label': f'Overdue by {-days}d',
                'class': 'bg-danger-lt text-danger',
                'icon': 'fa-triangle-exclamation',
                'status': 'Overdue'
            }
        elif days == 0:
            return {
                'label': 'Ready to harvest today!',
                'class': 'bg-success text-white',
                'icon': 'fa-circle-check',
                'status': 'Ready'
            }
        elif days <= 14:
            return {
                'label': f'{days} days left',
                'class': 'bg-warning-lt text-warning',
                'icon': 'fa-clock',
                'status': 'Approaching'
            }
        else:
            return {
                'label': f'In {days} days',
                'class': 'bg-blue-lt text-primary',
                'icon': 'fa-calendar',
                'status': 'Growing'
            }

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

