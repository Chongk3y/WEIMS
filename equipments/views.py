from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Equipment, Category, Status
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.db.models import Count
import json
from django.db.models import F, Q
from django.contrib import messages
from django.core.paginator import Paginator
import csv

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_encoder(user):
    return user.groups.filter(name='Encoder').exists()

def is_admin_or_encoder(user):
    return user.groups.filter(name__in=['Admin', 'Encoder']).exists()

def is_client(user):
    return user.groups.filter(name='Client').exists()

@login_required
@user_passes_test(is_admin_or_encoder)
def index(request):
    equipments = Equipment.objects.all()
    categories = Category.objects.all()
    statuses = Status.objects.all()

    category_id = request.GET.get('category')
    status_id = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    order = request.GET.get('order', 'desc')
    equipments = equipments.order_by('-item_purdate' if order == 'desc' else 'item_purdate')

    if category_id:
        equipments = equipments.filter(category_id=category_id)
    if status_id:
        equipments = equipments.filter(status_id=status_id)
    if date_from:
        equipments = equipments.filter(item_purdate__gte=date_from)
    if date_to:
        equipments = equipments.filter(item_purdate__lte=date_to)

    context = {
        'equipments': equipments,
        'categories': categories,
        'statuses': statuses,
        'selected_category': category_id,
        'selected_status': status_id,
        'date_from': date_from,
        'date_to': date_to,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'equipments/equipment_list.html', context)



@login_required
@user_passes_test(is_admin_or_encoder)
def add_equipment(request):
    users = User.objects.all()
    categories = Category.objects.all()
    statuses = Status.objects.all()
    from datetime import date
    today_date = date.today()
    return render(request, 'equipments/add.html', {
        'users': users,
        'categories': categories,
        'statuses': statuses,
        'today_date': today_date,
        'is_admin': is_admin(request.user),
    })

@login_required
@user_passes_test(is_admin_or_encoder)
def processaddequipment(request):
    errors = {}
    values = request.POST
    if request.method == 'POST':
        item_propertynum = request.POST.get('item_propertynum')
        item_name = request.POST.get('item_name')
        item_desc = request.POST.get('item_desc')
        item_purdate = request.POST.get('item_purdate')
        po_number = request.POST.get('po_number')
        fund_source = request.POST.get('fund_source')
        supplier = request.POST.get('supplier')
        item_amount = request.POST.get('item_amount')
        assigned_to = request.POST.get('assigned_to')
        location = request.POST.get('location')
        end_user = request.POST.get('end_user')
        emp_id = request.POST.get('emp_id')
        category_id = request.POST.get('category_id')
        status_id = request.POST.get('status_id')
        user_image = request.FILES.get('user_image', 'equipment_pic/image.jpg')

        # Field validations
        if not item_propertynum:
            errors['item_propertynum'] = 'Property number is required.'
        elif Equipment.objects.filter(item_propertynum=item_propertynum).exists():
            errors['item_propertynum'] = 'Property number already exists.'

        if not item_name:
            errors['item_name'] = 'Item name is required.'
        if not item_desc:
            errors['item_desc'] = 'Description is required.'
        if not item_purdate:
            errors['item_purdate'] = 'Purchase date is required.'
        if not po_number:
            errors['po_number'] = 'PO number is required.'
        if not fund_source:
            errors['fund_source'] = 'Fund source is required.'
        if not supplier:
            errors['supplier'] = 'Supplier is required.'
        if not item_amount:
            errors['item_amount'] = 'Amount is required.'
        if not assigned_to:
            errors['assigned_to'] = 'Assigned to is required.'
        if not location:
            errors['location'] = 'Location is required.'
        if not end_user:
            errors['end_user'] = 'End user is required.'
        if not emp_id:
            errors['emp_id'] = 'Employee is required.'
        if not category_id:
            errors['category_id'] = 'Category is required.'
        if not status_id:
            errors['status_id'] = 'Status is required.'

        if errors:
            users = User.objects.all()
            categories = Category.objects.all()
            statuses = Status.objects.all()
            from datetime import date
            today_date = date.today()
            return render(request, 'equipments/add.html', {
                'errors': errors,
                'values': values,
                'users': users,
                'categories': categories,
                'statuses': statuses,
                'today_date': today_date,
                'is_admin': is_admin(request.user),
            })
        else:
            equipment = Equipment.objects.create(
                user_image=user_image,
                item_propertynum=item_propertynum,
                item_name=item_name,
                item_desc=item_desc,
                item_purdate=item_purdate,
                po_number=po_number,
                fund_source=fund_source,
                supplier=supplier,
                item_amount=item_amount,
                assigned_to=assigned_to,
                location=location,
                end_user=end_user,
                emp_id=emp_id,
                category_id=category_id,
                status_id=status_id
            )
            equipment.save()
            return HttpResponseRedirect('/equipments/')
      
@login_required 
@user_passes_test(is_admin_or_encoder)
def edit_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    categories = Category.objects.all()
    statuses = Status.objects.all()
    from django.contrib.auth.models import User
    users = User.objects.all()

    if request.method == 'POST':
        equipment.item_propertynum = request.POST.get('item_propertynum')
        equipment.item_name = request.POST.get('item_name')
        equipment.item_desc = request.POST.get('item_desc')
        equipment.item_purdate = request.POST.get('item_purdate')
        equipment.po_number = request.POST.get('po_number')
        equipment.fund_source = request.POST.get('fund_source')
        equipment.supplier = request.POST.get('supplier')
        equipment.item_amount = request.POST.get('item_amount')
        equipment.assigned_to = request.POST.get('assigned_to')
        equipment.location = request.POST.get('location')
        equipment.end_user = request.POST.get('end_user')
        equipment.emp_id = request.POST.get('emp_id')
        equipment.category_id = request.POST.get('category_id')
        equipment.status_id = request.POST.get('status_id')
        if request.FILES.get('user_image'):
            equipment.user_image = request.FILES['user_image']
        equipment.save()
        return redirect('equipments:index')

    return render(request, 'equipments/edit.html', {
        'equipment': equipment,
        'categories': categories,
        'statuses': statuses,
        'users': users,
    })

@login_required
@user_passes_test(is_admin)
def delete_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    equipment.delete()
    return redirect('equipments:index')


@login_required
def dashboard(request):
    total_equipments = Equipment.objects.count()
    status_counts = []
    for status in Status.objects.all():
        count = Equipment.objects.filter(status=status).count()
        status_counts.append({'name': status.name, 'count': count})
    return render(request, 'equipments/dashboard.html', {
        'total_equipments': total_equipments,
        'status_counts': status_counts,
    })

@login_required
def dashboard(request):
    total_equipments = Equipment.objects.count()

    status_counts = Equipment.objects.values('status__name').annotate(
        name=F('status__name'), count=Count('id')
    )

    recent_equipments = Equipment.objects.order_by('-id')[:5]

    categories = Category.objects.annotate(count=Count('equipment'))
    category_labels = [cat.name for cat in categories]
    category_counts = [cat.count for cat in categories]

    context = {
        'total_equipments': total_equipments,
        'status_counts': status_counts,
        'recent_equipments': recent_equipments,
        'category_labels': json.dumps(category_labels),
        'category_counts': json.dumps(category_counts),
    }

    return render(request, 'equipments/dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_encoder)
def user(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'equipments/user.html', {
        'users': users,
        'is_admin': is_admin(request.user),
    })

@login_required
@user_passes_test(is_admin)
def add_user(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role')
        if not username or not password or not role:
            error = "All fields are required."
        elif User.objects.filter(username=username).exists():
            error = "Username already exists."
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            group = Group.objects.get(name=role)
            user.groups.add(group)
            return redirect('equipments:user')
    return render(request, 'equipments/add_user.html', {'error': error})


@login_required
def category_list(request):
    is_admin = request.user.groups.filter(name="Admin").exists()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.warning(request, "Category already exists.")
            else:
                Category.objects.create(name=name)
                messages.success(request, "Category added successfully.")
        else:
            messages.error(request, "Category name cannot be empty.")
        return redirect('equipments:category')  # update with your URL name

    categories = Category.objects.all().order_by('name')
    return render(request, 'equipments/category.html', {
        'categories': categories, 
        'is_admin': is_admin,})




@login_required
def edit_category(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            category.name = name
            category.save()
            messages.success(request, "Category updated successfully.")
        else:
            messages.error(request, "Category name cannot be empty.")
    return redirect('equipments:category')


@login_required
@user_passes_test(is_admin)
def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully.")
    return redirect('equipments:category')


@login_required
def status_list(request):
    is_admin = request.user.groups.filter(name="Admin").exists()
    statuses = Status.objects.all()
    return render(request, 'equipments/status.html', {
        'statuses': statuses
        , 'is_admin': is_admin,})


@login_required
def add_status(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            if Status.objects.filter(name__iexact=name).exists():
                messages.warning(request, "Status already exists.")
            else:
                Status.objects.create(name=name)
                messages.success(request, "Status added successfully.")
        else:
            messages.error(request, "Status name cannot be empty.")
    return redirect('equipments:status')

@login_required
def edit_status(request, id):
    status = get_object_or_404(Status, id=id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            status.name = name
            status.save()
            messages.success(request, "Status updated successfully.")
        else:
            messages.error(request, "Status name cannot be empty.")
    return redirect('equipments:status')

@login_required
@user_passes_test(is_admin)
def delete_status(request, id):
    status = get_object_or_404(Status, id=id)
    if request.method == 'POST':
        status.delete()
        messages.success(request, "Status deleted successfully.")
    return redirect('equipments:status')

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="equipments.csv"'

    writer = csv.writer(response)
    writer.writerow(['Property #', 'Name', 'Description', 'Purchase Date', 'Amount', 'Assigned To', 'Location', 'Status'])

    for equipment in Equipment.objects.all():
        writer.writerow([
            equipment.item_propertynum,
            equipment.item_name,
            equipment.item_desc,
            equipment.item_purdate,
            equipment.item_amount,
            equipment.assigned_to,
            equipment.location,
            equipment.status.name if equipment.status else ''
        ])

    return response




