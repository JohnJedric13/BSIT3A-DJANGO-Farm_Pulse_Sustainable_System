from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import re

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.crops.models import Crop, FarmLog, AIDiagnosis

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=1)
INVALID_LOGIN_MESSAGE = 'Invalid username or password.'
LOCKED_MESSAGE = 'Too many failed attempts. Locked for 1 minute.'


def _reset_lock_state(request):
    request.session['failed_attempts'] = 0
    request.session['lock_time'] = None


def _get_lock_state(request):
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')

    if not lock_time:
        return failed_attempts, None

    try:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
    except (TypeError, ValueError):
        _reset_lock_state(request)
        return 0, None

    if timezone.now() < unlock_time:
        remaining = int((unlock_time - timezone.now()).total_seconds())
        return failed_attempts, remaining

    _reset_lock_state(request)
    return 0, None


def _set_lock_state(request):
    lock_until = timezone.now() + LOCK_DURATION
    request.session['failed_attempts'] = MAX_FAILED_ATTEMPTS
    request.session['lock_time'] = lock_until.isoformat()
    return int(LOCK_DURATION.total_seconds())


def _validate_registration_data(data):
    errors = {}

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username:
        errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already taken.'

    if not first_name:
        errors['first_name'] = 'First name is required.'

    if not last_name:
        errors['last_name'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address.'
        else:
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors['password'] = ' '.join(exc.messages)

    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    return errors


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    failed_attempts, remaining = _get_lock_state(request)
    if remaining is not None:
        messages.error(request, f'Too many failed attempts. Try again in {remaining} seconds.')
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    if request.method == 'GET':
        return render(request, 'auth/login.html')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        _reset_lock_state(request)
        login(request, user)
        return redirect('dashboard')

    failed_attempts += 1
    request.session['failed_attempts'] = failed_attempts
    if failed_attempts >= MAX_FAILED_ATTEMPTS:
        remaining = _set_lock_state(request)
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
    messages.error(request, f'{INVALID_LOGIN_MESSAGE} {remaining_attempts} attempts remaining.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home(request):
    user = request.user
    if user.is_superuser:
        crops_qs = Crop.objects.all()
        logs_qs = FarmLog.objects.all()
        diagnoses_qs = AIDiagnosis.objects.all()
    else:
        crops_qs = Crop.objects.filter()
        logs_qs = FarmLog.objects.filter()
        diagnoses_qs = AIDiagnosis.objects.filter()

    total_crops = crops_qs.count()
    healthy_crops = crops_qs.filter(status='Healthy').count()
    warning_crops = crops_qs.filter(status='Minor Warning').count()
    unhealthy_crops = crops_qs.filter(status='Unhealthy').count()
    total_logs = logs_qs.count()
    total_diagnoses = diagnoses_qs.count()

    today = timezone.localdate()
    today_logs = logs_qs.filter(log_date=today).count()
    harvest_ready_count = crops_qs.filter(
        expected_harvest_date__isnull=False,
        expected_harvest_date__lte=today
    ).count()
    harvest_upcoming_count = crops_qs.filter(
        expected_harvest_date__gt=today,
        expected_harvest_date__lte=today + timedelta(days=14)
    ).count()
    next_harvest = crops_qs.filter(
        expected_harvest_date__gte=today
    ).order_by('expected_harvest_date').first()
    days_until_next_harvest = (
        (next_harvest.expected_harvest_date - today).days
        if next_harvest else None
    )
    next_harvest_count = (
        crops_qs.filter(expected_harvest_date=next_harvest.expected_harvest_date).count()
        if next_harvest else 0
    )

    healthy_percent = round((healthy_crops / total_crops * 100)) if total_crops > 0 else 0
    warning_percent = round((warning_crops / total_crops * 100)) if total_crops > 0 else 0
    unhealthy_percent = round((unhealthy_crops / total_crops * 100)) if total_crops > 0 else 0

    forecast_months = []
    current_month = today.replace(day=1)
    for offset in range(5):
        month_index = current_month.month - 1 + offset
        year = current_month.year + month_index // 12
        month = month_index % 12 + 1
        month_start = date(year, month, 1)
        next_month_start = date(year + (month == 12), month % 12 + 1, 1)
        forecast_months.append({
            'month': month_start.strftime('%b'),
            'year': month_start.year,
            'month_start': month_start,
            'yield_kg': Decimal('0'),
        })

    forecast_end = next_month_start
    harvest_crops = crops_qs.filter(
        expected_harvest_date__gte=current_month,
        expected_harvest_date__lt=forecast_end,
    ).only('estimated_yield', 'expected_harvest_date')
    forecast_amounts = {}
    unparsed_yield_count = 0
    yield_pattern = re.compile(
        r'^\s*([\d,]+(?:\.\d+)?)\s*(kg|kilograms?|g|grams?|tons?|tonnes?|t|lbs?|pounds?)\s*$',
        re.IGNORECASE,
    )
    unit_multipliers = {
        'g': Decimal('0.001'),
        'gram': Decimal('0.001'),
        'grams': Decimal('0.001'),
        'ton': Decimal('1000'),
        'tons': Decimal('1000'),
        'tonne': Decimal('1000'),
        'tonnes': Decimal('1000'),
        't': Decimal('1000'),
        'lb': Decimal('0.45359237'),
        'lbs': Decimal('0.45359237'),
        'pound': Decimal('0.45359237'),
        'pounds': Decimal('0.45359237'),
    }
    for crop in harvest_crops:
        raw_yield = (crop.estimated_yield or '').strip()
        if not raw_yield:
            continue
        match = yield_pattern.fullmatch(raw_yield)
        if not match:
            unparsed_yield_count += 1
            continue
        try:
            amount = Decimal(match.group(1).replace(',', ''))
        except InvalidOperation:
            unparsed_yield_count += 1
            continue
        unit = match.group(2).lower()
        if unit.startswith('kilogram'):
            unit = 'kg'
        elif unit.startswith('gram'):
            unit = 'gram' if unit == 'gram' else 'grams'
        elif unit.startswith('ton'):
            unit = 'tonne' if unit == 'tonne' else 'tons'
        elif unit.startswith('pound'):
            unit = 'pound' if unit == 'pound' else 'pounds'
        elif unit.startswith('lb'):
            unit = 'lbs' if unit == 'lbs' else 'lb'
        amount *= unit_multipliers.get(unit, Decimal('1'))
        key = (crop.expected_harvest_date.year, crop.expected_harvest_date.month)
        forecast_amounts[key] = forecast_amounts.get(key, Decimal('0')) + amount

    for month in forecast_months:
        month_start = month.pop('month_start')
        amount = forecast_amounts.get((month_start.year, month_start.month), Decimal('0'))
        month['yield_kg'] = amount.quantize(Decimal('0.1'))

    max_forecast_yield = max((month['yield_kg'] for month in forecast_months), default=Decimal('0'))
    chart_max = (
        (max_forecast_yield / Decimal('4')).to_integral_value(rounding=ROUND_CEILING) * 4
        if max_forecast_yield else Decimal('4')
    )
    for month in forecast_months:
        month['height_percent'] = (
            round(month['yield_kg'] / chart_max * 100)
            if chart_max else 0
        )
    forecast_total = sum((month['yield_kg'] for month in forecast_months), Decimal('0')).quantize(Decimal('0.1'))
    forecast_ticks = [
        (chart_max * Decimal(step) / Decimal('4')).quantize(Decimal('1'))
        for step in range(4, -1, -1)
    ]

    recent_crops = crops_qs.order_by('-created_at')[:5]
    recent_logs = logs_qs.select_related('crop').order_by('-log_date', '-created_at')[:2]
    recent_diagnoses = diagnoses_qs.select_related('crop', 'log').order_by('-created_at')[:4]

    context = {
        'total_crops': total_crops,
        'healthy_crops': healthy_crops,
        'warning_crops': warning_crops,
        'unhealthy_crops': unhealthy_crops,
        'harvest_ready_count': harvest_ready_count,
        'harvest_upcoming_count': harvest_upcoming_count,
        'next_harvest_count': next_harvest_count,
        'days_until_next_harvest': days_until_next_harvest,
        'healthy_percent': healthy_percent,
        'warning_percent': warning_percent,
        'unhealthy_percent': unhealthy_percent,
        'forecast_months': forecast_months,
        'forecast_total': forecast_total,
        'forecast_ticks': forecast_ticks,
        'forecast_chart_max': chart_max,
        'unparsed_yield_count': unparsed_yield_count,
        'total_logs': total_logs,
        'today_logs': today_logs,
        'total_diagnoses': total_diagnoses,
        'recent_crops': recent_crops,
        'recent_logs': recent_logs,
        'recent_diagnoses': recent_diagnoses,
    }
    return render(request, 'home.html', context)


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'GET':
        return render(request, 'auth/register.html')

    form_data = {
        'username': request.POST.get('username', ''),
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'email': request.POST.get('email', ''),
        'password': request.POST.get('password', ''),
        'confirm_password': request.POST.get('confirm_password', ''),
    }

    errors = _validate_registration_data(form_data)
    if errors:
        return render(request, 'auth/register.html', {'errors': errors, 'form_data': form_data})

    user = User.objects.create_user(
        username=form_data['username'].strip(),
        first_name=form_data['first_name'].strip(),
        last_name=form_data['last_name'].strip(),
        email=form_data['email'].strip(),
        password=form_data['password'],
    )
    login(request, user)
    return redirect('dashboard')
