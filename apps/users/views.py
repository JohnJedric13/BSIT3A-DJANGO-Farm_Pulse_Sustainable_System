from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q


def _is_superuser(user):
    return user.is_superuser


# PAGE
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
def user_list_page(request):
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    users_list = User.objects.all().order_by('-date_joined')

    # Summary counts for KPI cards
    total_users = users_list.count()
    active_users = users_list.filter(is_active=True).count()
    superuser_count = users_list.filter(is_superuser=True).count()
    staff_count = users_list.filter(is_staff=True, is_superuser=False).count()

    if query:
        users_list = users_list.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if role_filter == 'superuser':
        users_list = users_list.filter(is_superuser=True)
    elif role_filter == 'staff':
        users_list = users_list.filter(is_staff=True, is_superuser=False)
    elif role_filter == 'user':
        users_list = users_list.filter(is_staff=False, is_superuser=False)
    elif role_filter == 'active':
        users_list = users_list.filter(is_active=True)
    elif role_filter == 'inactive':
        users_list = users_list.filter(is_active=False)

    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)

    return render(request, 'users/list.html', {
        'users': users,
        'query': query,
        'role_filter': role_filter,
        'total_users': total_users,
        'active_users': active_users,
        'superuser_count': superuser_count,
        'staff_count': staff_count,
    })


# LIST USERS (AJAX)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
def user_list_ajax(request):
    users_list = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)
    data = list(users.object_list.values(
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_active',
        'is_superuser',
        'date_joined',
    ))
    return JsonResponse({
        "data":     data,
        "has_next": users.has_next(),
        "has_prev": users.has_previous(),
        "page":     users.number,
        "pages":    users.paginator.num_pages,
        "total":    users.paginator.count,
    })


# GET SINGLE USER (AJAX)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
def user_get_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    return JsonResponse({
        "id":           user.id,
        "username":     user.username,
        "first_name":   user.first_name,
        "last_name":    user.last_name,
        "email":        user.email,
        "is_staff":     user.is_staff,
        "is_active":    user.is_active,
        "is_superuser": user.is_superuser,
        "date_joined":  user.date_joined.strftime('%b %d, %Y %H:%M') if user.date_joined else 'N/A',
        "last_login":   user.last_login.strftime('%b %d, %Y %H:%M') if user.last_login else 'Never',
    })


# CREATE / UPDATE USER (AJAX)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
@require_POST
def user_save_ajax(request):
    user_id = request.POST.get("id")

    if user_id:
        user = get_object_or_404(User, pk=user_id)
    else:
        user = User()

    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()

    if not username:
        return JsonResponse({"error": "Username is required."}, status=400)

    dup_qs = User.objects.filter(Q(username=username) | (Q(email=email) & ~Q(email="")))
    if user_id:
        dup_qs = dup_qs.exclude(pk=user_id)
    if dup_qs.filter(username=username).exists():
        return JsonResponse({"error": "That username is already taken."}, status=400)
    if email and dup_qs.filter(email=email).exists():
        return JsonResponse({"error": "That email is already in use."}, status=400)

    is_staff = request.POST.get("is_staff") == "true"
    is_active = request.POST.get("is_active") == "true"
    is_superuser = request.POST.get("is_superuser") == "true"

    # Self-modification safety checks
    if user_id and request.user == user:
        if not is_active:
            return JsonResponse({"error": "You cannot deactivate your own account."}, status=400)
        if not is_superuser and user.is_superuser:
            return JsonResponse({"error": "You cannot remove your own superuser status."}, status=400)

    # Superuser automatically gets staff rights
    if is_superuser:
        is_staff = True

    user.username     = username
    user.first_name   = request.POST.get("first_name", "").strip()
    user.last_name    = request.POST.get("last_name", "").strip()
    user.email        = email
    user.is_staff     = is_staff
    user.is_active    = is_active
    user.is_superuser = is_superuser

    password = request.POST.get("password")
    if password:
        if len(password) < 8:
            return JsonResponse({"error": "Password must be at least 8 characters."}, status=400)
        user.set_password(password)
    elif not user_id:
        return JsonResponse({"error": "Password is required for new users."}, status=400)

    try:
        user.save()
    except IntegrityError:
        return JsonResponse({"error": "Could not save user due to a conflict (duplicate username/email)."}, status=400)

    return JsonResponse({
        "status": "success",
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    })


# TOGGLE ACTIVE / INACTIVE (AJAX ACTION)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
@require_POST
def user_toggle_status_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user == user:
        return JsonResponse({"error": "You cannot change your own active status."}, status=400)

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])

    return JsonResponse({
        "status": "success",
        "is_active": user.is_active,
        "message": f"User '{user.username}' is now {'active' if user.is_active else 'inactive'}."
    })


# TOGGLE SUPERUSER (AJAX ACTION)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
@require_POST
def user_toggle_superuser_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user == user and user.is_superuser:
        return JsonResponse({"error": "You cannot remove your own superuser role."}, status=400)

    user.is_superuser = not user.is_superuser
    if user.is_superuser:
        user.is_staff = True
    user.save(update_fields=['is_superuser', 'is_staff'])

    return JsonResponse({
        "status": "success",
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "message": f"User '{user.username}' superuser role is now {'enabled' if user.is_superuser else 'disabled'}."
    })


# RESET PASSWORD (AJAX ACTION)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
@require_POST
def user_reset_password_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    password = request.POST.get("password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()

    if not password:
        return JsonResponse({"error": "Password cannot be empty."}, status=400)
    if len(password) < 8:
        return JsonResponse({"error": "Password must be at least 8 characters long."}, status=400)
    if password != confirm_password:
        return JsonResponse({"error": "Passwords do not match."}, status=400)

    user.set_password(password)
    user.save(update_fields=['password'])

    return JsonResponse({
        "status": "success",
        "message": f"Password for '{user.username}' has been successfully reset."
    })


# DELETE USER (AJAX)
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
@require_POST
def user_delete_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user == user:
        return JsonResponse({"error": "You cannot delete yourself"}, status=400)

    # Prevent deleting the last superuser
    if user.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
        return JsonResponse({"error": "Cannot delete the last remaining superuser."}, status=400)

    user.delete()
    return JsonResponse({"status": "deleted"})
