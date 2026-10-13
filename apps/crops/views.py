import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count

from .models import Crop, FarmLog, AIDiagnosis


CROP_HARVEST_PRESETS = [
    {'name': 'Tomato / Roma Tomato', 'days': 75},
    {'name': 'Sweet Corn', 'days': 80},
    {'name': 'Rice / Jasmine Rice', 'days': 120},
    {'name': 'Eggplant', 'days': 90},
    {'name': 'Potato', 'days': 100},
    {'name': 'Lettuce', 'days': 45},
    {'name': 'Carrot', 'days': 75},
    {'name': 'Cabbage', 'days': 85},
    {'name': 'Cucumber', 'days': 55},
    {'name': 'Chili / Pepper', 'days': 80},
    {'name': 'Onion', 'days': 110},
    {'name': 'Cassava', 'days': 270},
]


def scoped_crops(user):
    if user.is_superuser:
        return Crop.objects.all()
    return Crop.objects.filter()


def scoped_crop(user, pk):
    return get_object_or_404(scoped_crops(user), pk=pk)


@login_required(login_url='login')
def crop_list_page(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    crops_queryset = scoped_crops(request.user).order_by('-created_at')
    today = datetime.date.today()

    # Status counts for dashboard summary cards
    total_count = crops_queryset.count()
    healthy_count = crops_queryset.filter(status='Healthy').count()
    warning_count = crops_queryset.filter(status='Minor Warning').count()
    unhealthy_count = crops_queryset.filter(status='Unhealthy').count()
    harvest_ready_count = crops_queryset.filter(expected_harvest_date__isnull=False, expected_harvest_date__lte=today).count()
    harvest_upcoming_count = crops_queryset.filter(
        expected_harvest_date__gt=today,
        expected_harvest_date__lte=today + datetime.timedelta(days=14)
    ).count()

    if query:
        crops_queryset = crops_queryset.filter(
            Q(name__icontains=query) |
            Q(crop_type__icontains=query) |
            Q(location__icontains=query) |
            Q(last_observation__icontains=query)
        )

    if status_filter:
        crops_queryset = crops_queryset.filter(status=status_filter)

    paginator = Paginator(crops_queryset, 10)
    page_number = request.GET.get('page', 1)
    crops = paginator.get_page(page_number)

    return render(request, 'crops/list.html', {
        'crops': crops,
        'all_crops': scoped_crops(request.user).order_by('name'),
        'query': query,
        'status_filter': status_filter,
        'total_count': total_count,
        'healthy_count': healthy_count,
        'warning_count': warning_count,
        'unhealthy_count': unhealthy_count,
        'harvest_ready_count': harvest_ready_count,
        'harvest_upcoming_count': harvest_upcoming_count,
        'crop_presets': CROP_HARVEST_PRESETS,
        'today': today.isoformat(),
    })


@login_required(login_url='login')
def crop_detail(request, pk):
    crop = scoped_crop(request.user, pk)
    logs = crop.farm_logs.all().order_by('-log_date', '-created_at')
    diagnoses = crop.ai_diagnoses.select_related('log').all().order_by('-created_at')

    return render(request, 'crops/detail.html', {
        'crop': crop,
        'logs': logs,
        'diagnoses': diagnoses,
        'crop_presets': CROP_HARVEST_PRESETS,
        'today': datetime.date.today().isoformat(),
    })


@login_required(login_url='login')
def crop_get_ajax(request, pk):
    crop = scoped_crop(request.user, pk)
    return JsonResponse({
        'id': crop.id,
        'name': crop.name,
        'crop_type': crop.crop_type,
        'location': crop.location,
        'status': crop.status,
        'planting_date': crop.planting_date.isoformat() if crop.planting_date else '',
        'expected_harvest_date': crop.expected_harvest_date.isoformat() if crop.expected_harvest_date else '',
        'estimated_yield': crop.estimated_yield or '',
        'last_observation': crop.last_observation or '',
        'image_url': crop.display_image or '',
    })


@login_required(login_url='login')
@require_POST
def crop_save_ajax(request):
    crop_id = request.POST.get('id')

    if crop_id:
        crop = scoped_crop(request.user, crop_id)
    else:
        crop = Crop(user=request.user)

    name = request.POST.get('name', '').strip()
    crop_type = request.POST.get('crop_type', '').strip()
    location = request.POST.get('location', '').strip()
    status = request.POST.get('status', 'Healthy').strip()
    last_observation = request.POST.get('last_observation', '').strip()
    planting_date = request.POST.get('planting_date', '').strip() or None
    expected_harvest_date = request.POST.get('expected_harvest_date', '').strip() or None
    estimated_yield = request.POST.get('estimated_yield', '').strip() or None

    if not name or not crop_type or not location:
        return JsonResponse({'error': 'Name, crop type, and location are required.'}, status=400)

    crop.name = name
    crop.crop_type = crop_type
    crop.location = location
    crop.status = status
    crop.last_observation = last_observation
    crop.planting_date = planting_date
    crop.expected_harvest_date = expected_harvest_date
    crop.estimated_yield = estimated_yield

    if 'image' in request.FILES:
        crop.image = request.FILES['image']
    elif request.POST.get('remove_image') == '1':
        if crop.image:
            crop.image.delete(save=False)
        crop.image = None

    crop.save()

    return JsonResponse({
        'status': 'saved',
        'id': crop.id,
        'name': crop.name,
        'image_url': crop.display_image or '',
    })


@login_required(login_url='login')
@require_POST
def crop_delete_ajax(request, pk):
    crop = scoped_crop(request.user, pk)
    crop.delete()
    return JsonResponse({'status': 'deleted'})


@login_required(login_url='login')
@require_POST
def log_save_ajax(request, crop_id):
    crop = scoped_crop(request.user, crop_id)

    activity_type = request.POST.get('activity_type', '').strip()
    observed_condition = request.POST.get('observed_condition', '').strip()
    notes = request.POST.get('notes', '').strip()
    log_date = request.POST.get('log_date', '').strip()

    if not activity_type or not notes or not log_date:
        return JsonResponse({'error': 'Activity type, log date, and notes are required.'}, status=400)

    log = FarmLog.objects.create(
        crop=crop,
        activity_type=activity_type,
        observed_condition=observed_condition or 'Normal',
        notes=notes,
        log_date=log_date,
    )

    # Automatically keep the crop's last observation updated
    crop.last_observation = notes
    # Optionally update status if specified
    update_status = request.POST.get('update_crop_status')
    if update_status and update_status in dict(Crop.STATUS_CHOICES):
        crop.status = update_status
    crop.save()

    return JsonResponse({'status': 'saved', 'id': log.id})


@login_required(login_url='login')
@require_POST
def log_delete_ajax(request, pk):
    log = get_object_or_404(FarmLog, pk=pk)
    # verify ownership of crop
    scoped_crop(request.user, log.crop_id)
    log.delete()
    return JsonResponse({'status': 'deleted'})


@login_required(login_url='login')
@require_POST
def diagnosis_save_ajax(request, crop_id):
    crop = scoped_crop(request.user, crop_id)

    diagnosis_title = request.POST.get('diagnosis_title', '').strip()
    symptom_summary = request.POST.get('symptom_summary', '').strip()
    treatment_plan = request.POST.get('treatment_plan', '').strip()
    log_id = request.POST.get('log_id', '').strip()

    if not diagnosis_title or not symptom_summary or not treatment_plan:
        return JsonResponse({'error': 'Diagnosis title, symptoms, and treatment plan are required.'}, status=400)

    log = None
    if log_id:
        log = FarmLog.objects.filter(pk=log_id, crop=crop).first()

    diagnosis = AIDiagnosis.objects.create(
        crop=crop,
        log=log,
        diagnosis_title=diagnosis_title,
        symptom_summary=symptom_summary,
        treatment_plan=treatment_plan,
    )

    return JsonResponse({'status': 'saved', 'id': diagnosis.id})


@login_required(login_url='login')
@require_POST
def diagnosis_delete_ajax(request, pk):
    diagnosis = get_object_or_404(AIDiagnosis, pk=pk)
    # verify ownership
    scoped_crop(request.user, diagnosis.crop_id)
    diagnosis.delete()
    return JsonResponse({'status': 'deleted'})


@login_required(login_url='login')
def activity_logs_page(request):
    user = request.user
    crops = scoped_crops(user).order_by('name')

    query = request.GET.get('q', '').strip()
    activity_type = request.GET.get('type', '').strip()
    crop_filter = request.GET.get('crop', '').strip()
    date_filter = request.GET.get('date', '').strip()

    if user.is_superuser:
        logs_queryset = FarmLog.objects.select_related('crop')
    else:
        logs_queryset = FarmLog.objects.filter(crop__in=crops).select_related('crop')

    # Total counts
    total_logs = logs_queryset.count()
    watering_count = logs_queryset.filter(activity_type__icontains='Watering').count()
    fertilizing_count = logs_queryset.filter(activity_type__icontains='Fertiliz').count()
    inspection_count = logs_queryset.filter(activity_type__icontains='Inspect').count()

    if query:
        logs_queryset = logs_queryset.filter(
            Q(crop__name__icontains=query) |
            Q(activity_type__icontains=query) |
            Q(observed_condition__icontains=query) |
            Q(notes__icontains=query)
        )
    if activity_type:
        logs_queryset = logs_queryset.filter(activity_type=activity_type)
    if crop_filter:
        logs_queryset = logs_queryset.filter(crop_id=crop_filter)
    if date_filter:
        logs_queryset = logs_queryset.filter(log_date=date_filter)

    logs_queryset = logs_queryset.order_by('-log_date', '-created_at')

    paginator = Paginator(logs_queryset, 15)
    page_number = request.GET.get('page', 1)
    logs = paginator.get_page(page_number)

    return render(request, 'crops/activity_logs.html', {
        'logs': logs,
        'crops': crops,
        'total_logs': total_logs,
        'watering_count': watering_count,
        'fertilizing_count': fertilizing_count,
        'inspection_count': inspection_count,
        'query': query,
        'activity_type': activity_type,
        'crop_filter': crop_filter,
        'date_filter': date_filter,
        'today': datetime.date.today().isoformat(),
    })


@login_required(login_url='login')
@require_POST
def activity_log_save_ajax(request):
    crop_id = request.POST.get('crop_id')
    if not crop_id:
        return JsonResponse({'error': 'Please select a crop for this activity.'}, status=400)

    crop = scoped_crop(request.user, crop_id)

    activity_type = request.POST.get('activity_type', '').strip()
    observed_condition = request.POST.get('observed_condition', '').strip()
    notes = request.POST.get('notes', '').strip()
    log_date = request.POST.get('log_date', '').strip()

    if not activity_type or not notes or not log_date:
        return JsonResponse({'error': 'Activity type, log date, and symptom/observation notes are required.'}, status=400)

    log = FarmLog.objects.create(
        crop=crop,
        activity_type=activity_type,
        observed_condition=observed_condition or 'Normal / Good',
        notes=notes,
        log_date=log_date,
    )

    crop.last_observation = notes
    update_status = request.POST.get('update_crop_status')
    if update_status and update_status in dict(Crop.STATUS_CHOICES):
        crop.status = update_status
    crop.save()

    return JsonResponse({
        'status': 'saved',
        'id': log.id,
        'crop_name': crop.name,
        'activity_type': log.activity_type,
    })


