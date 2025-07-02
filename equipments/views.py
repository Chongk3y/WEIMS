from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from .models import Equipment, Category, Status
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.db.models import Count
import json
from django.db.models import F, Q
from django.contrib import messages
from django.core.paginator import Paginator
import csv
import openpyxl
from datetime import datetime
from django.views.decorators.http import require_POST


def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_encoder(user):
    return user.groups.filter(name='Encoder').exists()

def is_client(user):
    return user.groups.filter(name='Client').exists()

def is_admin_or_encoder(user):
    return user.groups.filter(name__in=['Admin', 'Encoder']).exists()

def is_admin_superadmin_encoder(user):
    return (
        user.groups.filter(name__in=["Admin", "Superadmin", "Encoder"]).exists()
    )


@login_required
def equipment_table_json(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = Equipment.objects.filter(is_returned=False).select_related('category', 'status', 'emp')

    # Handle global search
    if search_value:
        qs = qs.filter(
            Q(item_propertynum__icontains=search_value) |
            Q(item_name__icontains=search_value) |
            Q(item_desc__icontains=search_value) |
            Q(category__name__icontains=search_value) |
            Q(status__name__icontains=search_value)
        )
    # Handle advanced filters
    for key, value in request.GET.items():
        if key.startswith('filter_col_') and value:
            col_idx = key.replace('filter_col_', '')
            # Map col_idx to field name
            if col_idx == '2':  # Property #
                qs = qs.filter(item_propertynum__icontains=value)
            elif col_idx == '3':  # Name
                qs = qs.filter(item_name__icontains=value)
            elif col_idx == '4':  # Description
                qs = qs.filter(item_desc__icontains=value)
            elif col_idx == '5':  # Amount
                qs = qs.filter(item_amount__icontains=value)
            elif col_idx == '6':  # Category
                qs = qs.filter(category__name=value)
            elif col_idx == '7':  # Status
                qs = qs.filter(status__name=value)

    total = Equipment.objects.filter(is_returned=False).count()
    filtered = qs.count()
    equipments = qs.order_by('-item_purdate')[start:start+length]


    total = Equipment.objects.filter(is_returned=False).count()
    filtered = qs.count()
    equipments = qs.order_by('-item_purdate')[start:start+length]

    data = []
    for eq in equipments:
        actions = f'''
        <div class="dropdown" data-bs-auto-close="outside">
        <button class="btn btn-outline-secondary btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
            Actions
        </button>
        <ul class="dropdown-menu">
            <li>
            <a class="dropdown-item" href="/equipments/edit/{eq.id}/">
                <i class="bi bi-pencil-square"></i> Edit
            </a>
            </li>
            <li>
            <a class="dropdown-item" href="/equipments/delete/{eq.id}/" onclick="return confirm('Are you sure?');">
                <i class="bi bi-trash"></i> Delete
            </a>
            </li>
            {f'''
            <li>
            <button type="button" class="dropdown-item" data-bs-toggle="modal" data-bs-target="#returnModal" data-eqid="{eq.id}">
            <i class="bi bi-arrow-90deg-left"></i> Return
            </button>
            </li>
            ''' if not eq.is_returned else ''}
        </ul>
        </div>
        '''
        data.append([
            '',  # 0: Placeholder for checkbox
            eq.id,  # 1: hidden ID
            f'<img src="{eq.user_image.url if eq.user_image else ""}" style="width:32px;height:32px;object-fit:cover;" class="img-thumbnail">',
            eq.item_propertynum,
            eq.item_name,
            eq.item_desc if eq.item_desc is not None else 'None',
            eq.po_number if eq.po_number else 'None',
            f'₱{eq.item_amount:,.2f}',
            eq.end_user if eq.end_user else 'None',
            eq.category.name,
            eq.status.name,
            actions
        ])


    return JsonResponse({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': data,
    })

@login_required
def equipment_detail_json(request, pk):
    try:
        eq = Equipment.objects.select_related('category', 'status', 'created_by', 'updated_by').get(pk=pk)
    except Equipment.DoesNotExist:
        raise Http404
    data = {
        "image": eq.user_image.url if eq.user_image else "",
        "propertynum": eq.item_propertynum or "None",
        "name": eq.item_name or "None",
        "desc": eq.item_desc if eq.item_desc not in (None, '') else "None",
        "addinfo": eq.additional_info if eq.additional_info not in (None, '') else "None",
        "amount": f"{eq.item_amount:,.2f}" if eq.item_amount is not None else "None",
        "category": eq.category.name if eq.category and eq.category.name else "None",
        "status": eq.status.name if eq.status and eq.status.name else "None",
        "po_number": eq.po_number if eq.po_number not in (None, '') else "None",
        "fund_source": eq.fund_source if eq.fund_source not in (None, '') else "None",
        "supplier": eq.supplier if eq.supplier not in (None, '') else "None",
        "po_date": eq.item_purdate.strftime("%b %d, %Y") if eq.item_purdate else "None",
        "project_name": eq.project_name if eq.project_name not in (None, '') else "None",
        "assigned_to": eq.assigned_to if eq.assigned_to not in (None, '') else "None",
        "end_user": eq.end_user if eq.end_user not in (None, '') else "None",
        "location": eq.location if eq.location not in (None, '') else "None",
        "current_location": eq.current_location if eq.current_location not in (None, '') else "None",
        "created": eq.created_at.strftime("%b %d, %Y") if eq.created_at else "None",
        "created_by": f"{eq.created_by.first_name} {eq.created_by.last_name}" if eq.created_by else "None",
        "updated": eq.updated_at.strftime("%b %d, %Y") if eq.updated_at else "None",
        "updated_by": f"{eq.updated_by.first_name} {eq.updated_by.last_name}" if eq.updated_by else "None",
    }
    return JsonResponse(data)

@login_required
@user_passes_test(is_admin_or_encoder)
def index(request):
    equipments = Equipment.objects.filter(is_returned=False).select_related('category', 'status', 'emp').all()
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

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(equipments, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'equipments': page_obj,
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
        item_desc = request.POST.get('item_desc') or None
        item_purdate = request.POST.get('item_purdate') or None
        po_number = request.POST.get('po_number')
        fund_source = request.POST.get('fund_source') or None
        supplier = request.POST.get('supplier') or None
        item_amount = request.POST.get('item_amount')
        assigned_to = request.POST.get('assigned_to') or None
        location = request.POST.get('location') or None
        end_user = request.POST.get('end_user') or None
        category_id = request.POST.get('category_id')
        status_id = request.POST.get('status_id')
        user_image = request.FILES.get('user_image', 'equipment_pic/image.jpg')

        # Field validations (keep as is)
        # ...existing validation code...

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
                item_purdate=item_purdate if item_purdate else None,
                po_number=po_number,
                fund_source=fund_source,
                supplier=supplier,
                item_amount=item_amount,
                assigned_to=assigned_to,
                location=location,
                end_user=end_user,
                emp=request.user,
                category_id=category_id,
                status_id=status_id,
                created_by=request.user,
                updated_by=request.user
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

        # Handle item_purdate safely
        item_purdate = request.POST.get('item_purdate')
        if item_purdate:
            try:
                equipment.item_purdate = datetime.strptime(item_purdate, '%Y-%m-%d').date()
            except ValueError:
                equipment.item_purdate = None
        else:
            equipment.item_purdate = None

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
        equipment.updated_by = request.user

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
@user_passes_test(is_admin_superadmin_encoder)
def user(request):
    users = User.objects.all().order_by('-date_joined')  # <-- Add this line
    is_admin = request.user.groups.filter(name="Admin").exists()
    is_superadmin = request.user.groups.filter(name="Superadmin").exists()
    is_encoder = request.user.groups.filter(name="Encoder").exists()
    return render(request, 'equipments/user.html', {
        'users': users,
        'is_admin': is_admin,
        'is_superadmin': is_superadmin,
        'is_encoder': is_encoder,
    })

@login_required
@user_passes_test(is_admin_superadmin_encoder)
def add_user(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Check for required fields
        if not all([username, password, role, first_name, last_name]):
            error = "All fields are required."
        elif User.objects.filter(username=username).exists():
            error = "Username already exists."
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            group = Group.objects.get(name=role)
            user.groups.add(group)
            return redirect('equipments:user')
            
    return render(request, 'equipments/add_user.html', {'error': error})

@login_required
@user_passes_test(is_admin_superadmin_encoder)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        role = request.POST.get('role')
        if role:
            # Remove from all groups and add to the selected one
            user.groups.clear()
            group = Group.objects.get(name=role)
            user.groups.add(group)
        user.save()
        return redirect('equipments:user')
    return render(request, 'equipments/edit_user.html', {'user_obj': user})

@login_required
@user_passes_test(is_admin_superadmin_encoder)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('equipments:user')
    return render(request, 'equipments/confirm_delete_user.html', {'user_obj': user})

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
        return redirect('equipments:category')  

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


@login_required
@user_passes_test(is_admin_or_encoder)
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active

        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                # Convert empty strings to None for all fields
                cleaned_row = [cell if cell not in ('', None) else None for cell in row]

                Equipment.objects.create(
                    item_propertynum=cleaned_row[0],
                    item_name=cleaned_row[1],
                    item_desc=cleaned_row[2],
                    additional_info=(cleaned_row[3][:300] if cleaned_row[3] else None),
                    item_purdate=parse_date(cleaned_row[4]),
                    po_number=cleaned_row[5],
                    fund_source=cleaned_row[6],
                    supplier=cleaned_row[7],
                    item_amount=cleaned_row[8],
                    project_name=cleaned_row[9],
                    assigned_to=cleaned_row[10],
                    end_user=cleaned_row[11],
                    location=cleaned_row[12],
                    current_location=cleaned_row[13],
                    category=Category.objects.get(pk=1),  
                    status=Status.objects.get(pk=1),      
                    emp=request.user,
                    created_by=request.user,
                    updated_by=request.user,
                )
            except Exception as e:
                messages.error(request, f"Row {idx}: {e}")
        messages.success(request, "Excel import completed.")
    return redirect('equipments:index')

def parse_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        return None  # or raise


@require_POST
@login_required
def bulk_update_equipment(request):
    
    ids = request.POST.get('equipment_ids', '')
    status_id = request.POST.get('status_id')
    category_id = request.POST.get('category_id')
    if not ids:
        return JsonResponse({'error': 'No equipment selected.'}, status=400)
    id_list = [int(i) for i in ids.split(',') if i.isdigit()]
    qs = Equipment.objects.filter(id__in=id_list)
    updates = {}
    if status_id:
        updates['status_id'] = status_id
    if category_id:
        updates['category_id'] = category_id
    if updates:
        qs.update(**updates)
    return JsonResponse({'success': True})


@login_required
def returned(request):
    equipments = Equipment.objects.filter(is_returned=True)
    return render(request, 'equipments/returned.html', {'equipments': equipments})


@require_POST
@login_required
def return_equipment(request):
    eq_id = request.POST.get('equipment_id')
    file = request.FILES.get('return_document')
    remarks = request.POST.get('return_remarks')
    condition = request.POST.get('return_condition')
    return_type = request.POST.get('return_type')
    if not eq_id or not file:
        messages.error(request, "Equipment and document are required.")
        return redirect('equipments:index')
    eq = get_object_or_404(Equipment, id=eq_id)
    eq.is_returned = True
    eq.return_document = file
    eq.return_remarks = remarks
    eq.return_condition = condition
    eq.return_type = return_type
    eq.received_by = request.user
    eq.save()
    messages.success(request, "Equipment marked as returned.")
    return redirect('equipments:index')