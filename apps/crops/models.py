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
    image = models.ImageField(upload_to='diagnoses/', blank=True, null=True)
    symptom_summary = models.TextField()
    diagnosis_title = models.CharField(max_length=255)
    treatment_plan = models.TextField()
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
    def parsed_plan(self):
        import re
        text = (self.treatment_plan or '').strip()
        if not text:
            return {'visual': '', 'immediate': [], 'preventative': [], 'raw': ''}

        pattern = re.compile(
            r'(?:VISUAL\s+DIAGNOSIS[:\s]*)(.*?)(?=(?:IMMEDIATE\s+(?:ORGANIC/FIELD\s+)?ACTIONS[:\s]*)|$)'
            r'(?:(?:IMMEDIATE\s+(?:ORGANIC/FIELD\s+)?ACTIONS[:\s]*)(.*?)(?=(?:PREVENTATIVE\s+PRACTICES[:\s]*)|$))?'
            r'(?:(?:PREVENTATIVE\s+PRACTICES[:\s]*)(.*))?',
            re.IGNORECASE | re.DOTALL
        )
        m = pattern.search(text)
        if not m:
            return {'visual': text, 'immediate': [], 'preventative': [], 'raw': text}

        visual_raw = (m.group(1) or '').strip()
        immediate_raw = (m.group(2) or '').strip()
        preventative_raw = (m.group(3) or '').strip()

        def extract_bullets(sec_text):
            if not sec_text:
                return []
            bullets = []
            current = []
            for line in sec_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if re.match(r'^[-*•\d\.]+\s+', stripped):
                    if current:
                        bullets.append(" ".join(current).strip())
                        current = []
                    cleaned = re.sub(r'^[-*•\d\.]+\s+', '', stripped)
                    current.append(cleaned)
                else:
                    if current:
                        current.append(stripped)
                    else:
                        current.append(stripped)
            if current:
                bullets.append(" ".join(current).strip())
            return bullets

        return {
            'visual': visual_raw,
            'immediate': extract_bullets(immediate_raw),
            'preventative': extract_bullets(preventative_raw),
            'raw': text,
        }

    @property
    def formatted_plan_html(self):
        import html
        parsed = self.parsed_plan
        visual = parsed.get('visual', '').strip()
        immediate = parsed.get('immediate', [])
        preventative = parsed.get('preventative', [])
        raw_text = parsed.get('raw', '')

        if not visual and not immediate and not preventative:
            return f'<div class="ai-plan-text small">{html.escape(raw_text)}</div>'

        parts = []

        if visual:
            parts.append(
                f'<div class="ai-section-card ai-visual-card p-3 rounded border mb-3">'
                f'  <div class="d-flex align-items-center gap-2 mb-2">'
                f'    <span class="avatar avatar-xs rounded bg-blue-lt text-primary flex-shrink-0">'
                f'      <i class="fas fa-microscope"></i>'
                f'    </span>'
                f'    <span class="fw-bold small text-primary text-uppercase" style="letter-spacing: 0.04em; font-size: 0.74rem;">'
                f'      Visual Diagnosis &amp; Root Cause'
                f'    </span>'
                f'  </div>'
                f'  <div class="small text-body" style="line-height: 1.6;">'
                f'    {html.escape(visual)}'
                f'  </div>'
                f'</div>'
            )

        if immediate:
            items_html = "".join([
                f'<li class="d-flex align-items-start gap-2 p-2 rounded bg-surface-secondary border-start border-warning border-3">'
                f'  <i class="fas fa-circle-check text-warning mt-1 flex-shrink-0" style="font-size: 0.85rem;"></i>'
                f'  <span class="small text-body" style="line-height: 1.55;">{html.escape(act)}</span>'
                f'</li>'
                for act in immediate
            ])
            parts.append(
                f'<div class="ai-section-card ai-immediate-card p-3 rounded border mb-3">'
                f'  <div class="d-flex align-items-center gap-2 mb-2">'
                f'    <span class="avatar avatar-xs rounded bg-warning-lt text-warning flex-shrink-0">'
                f'      <i class="fas fa-bolt"></i>'
                f'    </span>'
                f'    <span class="fw-bold small text-warning text-uppercase" style="letter-spacing: 0.04em; font-size: 0.74rem;">'
                f'      Immediate Field Actions (Do This Now)'
                f'    </span>'
                f'  </div>'
                f'  <ul class="list-unstyled mb-0 d-flex flex-column gap-2">'
                f'    {items_html}'
                f'  </ul>'
                f'</div>'
            )

        if preventative:
            items_html = "".join([
                f'<li class="d-flex align-items-start gap-2 p-2 rounded bg-surface-secondary border-start border-success border-3">'
                f'  <i class="fas fa-shield-halved text-success mt-1 flex-shrink-0" style="font-size: 0.85rem;"></i>'
                f'  <span class="small text-body" style="line-height: 1.55;">{html.escape(prev)}</span>'
                f'</li>'
                for prev in preventative
            ])
            parts.append(
                f'<div class="ai-section-card ai-preventative-card p-3 rounded border mb-0">'
                f'  <div class="d-flex align-items-center gap-2 mb-2">'
                f'    <span class="avatar avatar-xs rounded bg-success-lt text-success flex-shrink-0">'
                f'      <i class="fas fa-seedling"></i>'
                f'    </span>'
                f'    <span class="fw-bold small text-success text-uppercase" style="letter-spacing: 0.04em; font-size: 0.74rem;">'
                f'      Preventative Practices &amp; Long-Term Care'
                f'    </span>'
                f'  </div>'
                f'  <ul class="list-unstyled mb-0 d-flex flex-column gap-2">'
                f'    {items_html}'
                f'  </ul>'
                f'</div>'
            )

        return "".join(parts)

    class Meta:
        db_table = 'ai_diagnoses'
        ordering = ['-created_at']
        verbose_name = 'AI Diagnosis'
        verbose_name_plural = 'AI Diagnoses'

    def __str__(self):
        return f"{self.diagnosis_title} - {self.crop.name}"
