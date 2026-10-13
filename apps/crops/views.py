import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count

from .models import Crop, FarmLog, AIDiagnosis


def scoped_crops(user):
    if user.is_superuser:
        return Crop.objects.all()
    return Crop.objects.filter(user=user)


def scoped_crop(user, pk):
    return get_object_or_404(scoped_crops(user), pk=pk)


@login_required(login_url='login')
def crop_list_page(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    crops_queryset = scoped_crops(request.user).order_by('-created_at')

    # Status counts for dashboard summary cards
    total_count = crops_queryset.count()
    healthy_count = crops_queryset.filter(status='Healthy').count()
    warning_count = crops_queryset.filter(status='Minor Warning').count()
    unhealthy_count = crops_queryset.filter(status='Unhealthy').count()

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
        'query': query,
        'status_filter': status_filter,
        'total_count': total_count,
        'healthy_count': healthy_count,
        'warning_count': warning_count,
        'unhealthy_count': unhealthy_count,
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
        'last_observation': crop.last_observation or '',
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

    if not name or not crop_type or not location:
        return JsonResponse({'error': 'Name, crop type, and location are required.'}, status=400)

    crop.name = name
    crop.crop_type = crop_type
    crop.location = location
    crop.status = status
    crop.last_observation = last_observation
    crop.save()

    return JsonResponse({
        'status': 'saved',
        'id': crop.id,
        'name': crop.name,
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

