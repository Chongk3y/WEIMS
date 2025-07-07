# Standard library imports
import csv
import json
from datetime import datetime
# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.core.exceptions import ObjectDoesNotExist
# Django auth imports
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
# Third-party imports
import openpyxl
from django.db.models.functions import TruncMonth, ExtractYear

# Local app imports
from .models import Equipment, Category, Status
from .models import EquipmentHistory
from .models import EquipmentActionLog



def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_encoder(user):
    return user.groups.filter(name='Encoder').exists()

def is_client(user):
    return user.groups.filter(name='Client').exists()

def is_admin_or_superadmin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_admin_superadmin_encoder(user):
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Encoder']).exists()



@login_required
def equipment_table_json(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # Initial queryset
    qs = Equipment.objects.filter(is_returned=False, is_archived=False).select_related('category', 'status', 'emp')



    # Global search
    if search_value:
        qs = qs.filter(
            Q(item_propertynum__icontains=search_value) |
            Q(item_name__icontains=search_value) |
            Q(item_desc__icontains=search_value) |
            Q(category__name__icontains=search_value) |
            Q(status__name__icontains=search_value) |
            Q(po_number__icontains=search_value) |
            Q(fund_source__icontains=search_value) |
            Q(supplier__icontains=search_value) |
            Q(item_amount__icontains=search_value) |
            Q(assigned_to__icontains=search_value) |
            Q(end_user__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(current_location__icontains=search_value) |
            Q(item_purdate__icontains=search_value) |
            Q(project_name__icontains=search_value)
        )

    # Advanced filters
    for key, value in request.GET.items():
        if key.startswith('filter_col_') and value:
            col_idx = key.replace('filter_col_', '')
            if col_idx == '2':  # Property #
                qs = qs.filter(item_propertynum__icontains=value)
            elif col_idx == '3':  # Name
                qs = qs.filter(item_name__icontains=value)
            elif col_idx == '4':  # Description
                qs = qs.filter(item_desc__icontains=value)
            elif col_idx == '5':  # PO Number
                qs = qs.filter(po_number__icontains=value)
            elif col_idx == '6':  # Fund Source
                qs = qs.filter(fund_source__icontains=value)
            elif col_idx == '7':  # Supplier
                qs = qs.filter(supplier__icontains=value)
            elif col_idx == '8':  # Amount
                try:
                    qs = qs.filter(item_amount=float(value))
                except Exception:
                    pass
            elif col_idx == '9':  # Assigned To
                qs = qs.filter(assigned_to__icontains=value)
            elif col_idx == '10':  # End User
                qs = qs.filter(end_user__icontains=value)
            elif col_idx == '11':  # Location
                qs = qs.filter(location__icontains=value)
            elif col_idx == '12':  # Current Location
                qs = qs.filter(current_location__icontains=value)
            elif col_idx == '13':  # Category
                qs = qs.filter(category__name__icontains=value)
            elif col_idx == '14':  # Status
                qs = qs.filter(status__name__icontains=value)
            elif col_idx == '15':  # Purchase Date
                qs = qs.filter(item_purdate=value)

    # Sorting
    order_col = request.GET.get('order[0][column]', '1')
    order_dir = request.GET.get('order[0][dir]', 'desc')

    col_map = {
        '1': 'id',
        '3': 'item_propertynum',
        '4': 'item_name',
        '5': 'item_desc',
        '6': 'po_number',
        '7': 'item_amount',
        '8': 'end_user',
        '9': 'category__name',
        '10': 'status__name',
    }

    order_field = col_map.get(order_col, 'id')
    if order_dir == 'desc':
        order_field = '-' + order_field

    total = Equipment.objects.filter(is_returned=False).count()
    filtered = qs.count()

    equipments = qs.order_by(order_field)[start:start + length]

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
            <li>
            <a class="dropdown-item" href="/equipments/archive/{eq.id}/" onclick="return confirm('Archive this equipment?');">
                <i class="bi bi-archive"></i> Archive
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
            '',  # 0: Checkbox placeholder
            eq.id,  # 1: hidden ID
            f'<img src="{eq.user_image.url if eq.user_image else ""}" style="width:32px;height:32px;object-fit:cover;" class="img-thumbnail">',  # 2: Image
            eq.item_propertynum,  # 3: Property #
            eq.item_name,         # 4: Name
            eq.item_desc if eq.item_desc else 'None',  # 5: Description
            eq.po_number if eq.po_number else 'None',  # 6: PO Number
            f'₱{eq.item_amount:,.2f}',                 # 7: Amount
            eq.end_user if eq.end_user else 'None',    # 8: End User
            eq.category.name,                          # 9: Category
            eq.status.name,                            # 10: Status
            actions,                                   # 11: Actions
            eq.fund_source if eq.fund_source else 'None',         # 12: Fund Source
            eq.supplier if eq.supplier else 'None',               # 13: Supplier
            eq.assigned_to if eq.assigned_to else 'None',         # 14: Assigned To
            eq.location if eq.location else 'None',               # 15: Deployment Location
            eq.current_location if eq.current_location else 'None',# 16: Current Location
            eq.item_purdate.strftime('%Y-%m-%d') if eq.item_purdate else 'None', # 17: PO Date
            eq.project_name if eq.project_name else 'None',       # 18: Project Name
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
@user_passes_test(is_admin_superadmin_encoder)
def index(request):
    equipments = Equipment.objects.filter(is_returned=False).select_related('category', 'status', 'emp').all()
    categories = Category.objects.all()
    statuses = Status.objects.all()
    end_users = Equipment.objects.exclude(end_user__isnull=True).exclude(end_user='').values_list('end_user', flat=True).distinct()
    assigned_to_list = Equipment.objects.exclude(assigned_to__isnull=True).exclude(assigned_to='').values_list('assigned_to', flat=True).distinct()
    fund_sources = Equipment.objects.exclude(fund_source__isnull=True).exclude(fund_source='').values_list('fund_source', flat=True).distinct()
    suppliers = Equipment.objects.exclude(supplier__isnull=True).exclude(supplier='').values_list('supplier', flat=True).distinct()
    locations = Equipment.objects.exclude(location__isnull=True).exclude(location='').values_list('location', flat=True).distinct()
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
        'end_users': end_users,
        'assigned_to_list': assigned_to_list,
        'fund_sources': fund_sources,
        'suppliers': suppliers,
        'locations': locations,
        'selected_category': category_id,
        'selected_status': status_id,
        'date_from': date_from,
        'date_to': date_to,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'equipments/equipment_list.html', context)


@login_required
@user_passes_test(is_admin_superadmin_encoder)
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
@user_passes_test(is_admin_superadmin_encoder)
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
        order_receipt = request.FILES.get('order_receipt', None)

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
                updated_by=request.user,
                order_receipt=order_receipt 
            )
            equipment.save()
            EquipmentActionLog.objects.create(
            equipment=equipment,
            action='create',
            user=request.user,
            summary=f"Created equipment: {equipment.item_name} (Property #: {equipment.item_propertynum})"
)
            return HttpResponseRedirect('/equipments/')
      
@login_required 
@user_passes_test(is_admin_superadmin_encoder)
def edit_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    categories = Category.objects.all()
    statuses = Status.objects.all()
    users = User.objects.all()

    if request.method == 'POST':
        # Capture current values before changes
        original = {
            'item_propertynum': equipment.item_propertynum,
            'item_name': equipment.item_name,
            'item_desc': equipment.item_desc,
            'item_purdate': equipment.item_purdate,
            'po_number': equipment.po_number,
            'fund_source': equipment.fund_source,
            'supplier': equipment.supplier,
            'item_amount': equipment.item_amount,
            'assigned_to': equipment.assigned_to,
            'location': equipment.location,
            'end_user': equipment.end_user,
            'emp_id': equipment.emp_id,
            'category_id': equipment.category_id,
            'status_id': equipment.status_id,
        }

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
        equipment.assigned_to = request.POST.get('assigned_to') or None
        equipment.location = request.POST.get('location')
        equipment.end_user = request.POST.get('end_user') or None
        equipment.emp_id = request.POST.get('emp_id')
        equipment.category_id = request.POST.get('category_id')
        equipment.status_id = request.POST.get('status_id')
        equipment.updated_by = request.user

        if request.FILES.get('user_image'):
            equipment.user_image = request.FILES['user_image']

        # Save equipment first
        equipment.save()
        EquipmentActionLog.objects.create(
            equipment=equipment,
            action='edit',
            user=request.user,
            summary=f"Edited equipment: {equipment.item_name} (Property #: {equipment.item_propertynum})"
        )

        field_labels = {
            'item_propertynum': 'Property #',
            'item_name': 'Name',
            'item_desc': 'Description',
            'item_purdate': 'Purchase Date',
            'po_number': 'PO Number',
            'fund_source': 'Fund Source',
            'supplier': 'Supplier',
            'item_amount': 'Amount',
            'assigned_to': 'Assigned To',
            'location': 'Location',
            'end_user': 'End User',
            'emp_id': 'Employee',
            'category_id': 'Category',
            'status_id': 'Status',
        }
        for field, old in original.items():
            new = getattr(equipment, field)
            # For ForeignKeys, get display value
            if field == 'category_id' and old != new:
                old_val = str(Category.objects.get(pk=old).name) if old else ''
                new_val = str(equipment.category.name) if equipment.category else ''
            elif field == 'status_id' and old != new:
                old_val = str(Status.objects.get(pk=old).name) if old else ''
                new_val = str(equipment.status.name) if equipment.status else ''
            elif field == 'emp_id' and old != new:
                old_val = str(User.objects.get(pk=old).get_full_name()) if old else ''
                new_val = str(equipment.emp.get_full_name()) if equipment.emp else ''
            elif field == 'item_purdate' and old != new:
                old_val = old.strftime('%Y-%m-%d') if old else ''
                new_val = new.strftime('%Y-%m-%d') if new else ''
            elif field == 'item_amount':
                try:
                    old_val = float(old) if old not in (None, '', 'None') else 0.0
                except Exception:
                    old_val = 0.0
                try:
                    new_val = float(new) if new not in (None, '', 'None') else 0.0
                except Exception:
                    new_val = 0.0
                old_val_str = f"₱{old_val:,.2f}" if old not in ('', None, 'None') else ''
                new_val_str = f"₱{new_val:,.2f}" if new not in ('', None, 'None') else ''
                if old_val != new_val:
                    EquipmentHistory.objects.create(
                        equipment=equipment,
                        field_changed=field_labels.get(field, field),
                        old_value=old_val_str,
                        new_value=new_val_str,
                        action='Edited',
                        changed_by=request.user
                    )
                continue
            else:
                # Normalize for text fields: treat None, '', and 'None' as equivalent, and strip whitespace
                def norm(val):
                    if val is None or val == '' or str(val).strip().lower() == 'none':
                        return ''
                    return str(val).strip()
                old_val = norm(old)
                new_val = norm(new)
            if old_val != new_val:
                EquipmentHistory.objects.create(
                    equipment=equipment,
                    field_changed=field_labels.get(field, field),
                    old_value=old_val,
                    new_value=new_val,
                    action='Edited',
                    changed_by=request.user
                )

        return redirect('equipments:index')

    return render(request, 'equipments/edit.html', {
        'equipment': equipment,
        'categories': categories,
        'statuses': statuses,
        'users': users,
    })

@login_required
@user_passes_test(is_admin_or_superadmin)
def delete_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    item_name = equipment.item_name
    item_propertynum = equipment.item_propertynum
    # Log the delete action before deleting equipment and logs
    EquipmentActionLog.objects.create(
        equipment=equipment,
        action='delete',
        user=request.user,
        summary=f"Deleted equipment: {item_name} (Property #: {item_propertynum})"
    )
    # Delete related action logs
    EquipmentActionLog.objects.filter(equipment_id=equipment.id).delete()
    equipment.delete()
    return redirect('equipments:index')


@login_required
def dashboard(request):
    total_equipments = Equipment.objects.count()
    total_archived = Equipment.objects.filter(is_archived=True).count()
    total_returned = Equipment.objects.filter(is_returned=True).count()

    # Status counts for pie chart
    status_counts = Equipment.objects.values('status__name').annotate(
        name=F('status__name'), count=Count('id')
    )
    status_labels = [s['name'] for s in status_counts]
    status_data = [s['count'] for s in status_counts]

    # Category counts for bar chart
    categories = Category.objects.annotate(count=Count('equipment'))
    category_labels = [cat.name for cat in categories]
    category_counts = [cat.count for cat in categories]

    # Recent equipments
    recent_equipments = Equipment.objects.order_by('-id')[:5]

    # Equipments acquired per year (from PO date)
    from django.db.models.functions import ExtractYear
    year_qs = Equipment.objects.exclude(item_purdate=None).values(year=ExtractYear('item_purdate')).annotate(count=Count('id')).order_by('year')
    year_labels = [str(x['year']) for x in year_qs]
    year_data = [x['count'] for x in year_qs]

    # Total number and total cost of equipment per end user (currently held)
    enduser_qs = Equipment.objects.filter(is_archived=False, is_returned=False).exclude(end_user__isnull=True).exclude(end_user='').values('end_user').annotate(
        count=Count('id'),
        total=Sum('item_amount')
    ).order_by('-count')
    enduser_labels = [x['end_user'] for x in enduser_qs]
    enduser_counts = [x['count'] for x in enduser_qs]
    enduser_amounts = [float(x['total'] or 0) for x in enduser_qs]

    # Equipments by Assigned To: Count and Total Cost
    assigned_qs = Equipment.objects.filter(is_archived=False, is_returned=False).exclude(assigned_to__isnull=True).exclude(assigned_to='').values('assigned_to').annotate(
        count=Count('id'),
        total=Sum('item_amount')
    ).order_by('-count')
    assigned_labels = [x['assigned_to'] for x in assigned_qs]
    assigned_counts = [x['count'] for x in assigned_qs]
    assigned_amounts = [float(x['total'] or 0) for x in assigned_qs]

    # Equipments by Item Name: Count
    name_qs = Equipment.objects.values('item_name').annotate(count=Count('id')).order_by('-count')
    itemname_labels = [x['item_name'] for x in name_qs]
    itemname_counts = [x['count'] for x in name_qs]
    context = {
        'total_equipments': total_equipments,
        'total_archived': total_archived,
        'total_returned': total_returned,
        'status_counts': status_counts,
        'status_labels': status_labels,
        'status_data': status_data,
        'category_labels': json.dumps(category_labels),
        'category_counts': json.dumps(category_counts),
        'recent_equipments': recent_equipments,
        'month_labels': json.dumps(year_labels),  # Used by the chart, but now years
        'month_data': json.dumps(year_data),      # Used by the chart, but now yearly counts
        'enduser_labels': json.dumps(enduser_labels),
        'enduser_counts': json.dumps(enduser_counts),
        'enduser_amounts': json.dumps(enduser_amounts),
        'assigned_labels': json.dumps(assigned_labels),
        'assigned_counts': json.dumps(assigned_counts),
        'assigned_amounts': json.dumps(assigned_amounts),
        'itemname_labels': json.dumps(itemname_labels),
        'itemname_counts': json.dumps(itemname_counts),
    }
    return render(request, 'equipments/dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_superadmin)
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
@user_passes_test(is_admin_superadmin_encoder)
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active

        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                # Convert empty strings to None for all fields
                cleaned_row = [cell if cell not in ('', None) else None for cell in row]
                propertynum = cleaned_row[0]
                # Skip if property number exists and is already in DB (ignore if blank)
                if propertynum and Equipment.objects.filter(item_propertynum=propertynum).exists():
                    continue
                Equipment.objects.create(
                    item_propertynum=propertynum,
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


@login_required
def returned_equipment_table_json(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = Equipment.objects.filter(is_returned=True).select_related('category', 'status', 'emp')

    if search_value:
        qs = qs.filter(
            Q(item_propertynum__icontains=search_value) |
            Q(item_name__icontains=search_value) |
            Q(item_desc__icontains=search_value) |
            Q(category__name__icontains=search_value) |
            Q(status__name__icontains=search_value) |
            Q(po_number__icontains=search_value) |
            Q(fund_source__icontains=search_value) |
            Q(supplier__icontains=search_value) |
            Q(item_amount__icontains=search_value) |
            Q(assigned_to__icontains=search_value) |
            Q(end_user__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(current_location__icontains=search_value) |
            Q(item_purdate__icontains=search_value) |
            Q(project_name__icontains=search_value)
        )

    total = Equipment.objects.filter(is_returned=True).count()
    filtered = qs.count()
    equipments = qs.order_by('-updated_at')[start:start+length]

    data = []
    for eq in equipments:
        data.append([
            '',  # checkbox placeholder
            eq.id,
            f'<img src="{eq.user_image.url if eq.user_image else ""}" class="img-thumbnail" style="width:32px;height:32px;object-fit:cover;">',
            eq.item_propertynum,
            eq.item_name,
            eq.item_desc or 'None',
            eq.returned_by or 'None',
            f'<a href="{eq.return_document.url}" target="_blank">View</a>' if eq.return_document else 'None',
            eq.updated_at.strftime("%b %d, %Y") if eq.updated_at else 'None',
            eq.return_remarks or 'None',
            eq.return_condition or 'None',
            eq.return_type or 'None',
            eq.received_by or 'None'
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': data,
    })

@require_POST
@login_required
def return_equipment(request):
    eq_id = request.POST.get('equipment_id')
    file = request.FILES.get('return_document')
    remarks = request.POST.get('return_remarks')
    condition = request.POST.get('return_condition')
    return_type = request.POST.get('return_type')
    returned_by = request.POST.get('returned_by') 
    received_by = request.POST.get('received_by')
    if not eq_id or not file:
        messages.error(request, "Equipment and document are required.")
        return redirect('equipments:index')
    eq = get_object_or_404(Equipment, id=eq_id)
    eq.is_returned = True
    eq.return_document = file
    eq.return_remarks = remarks
    eq.return_condition = condition
    eq.return_type = return_type
    eq.returned_by = returned_by
    eq.received_by = received_by
    eq.save()
    messages.success(request, "Equipment marked as returned.")
    return redirect('equipments:index')

@login_required
@user_passes_test(is_admin_superadmin_encoder)
def archived_equipments(request):
    return render(request, 'equipments/archived_list.html')

@login_required
def archive_equipment(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    equipment.is_archived = True
    equipment.date_archived = timezone.now()
    equipment.archived_by = request.user
    equipment.save()
    EquipmentActionLog.objects.create(
    equipment=equipment,
    action='archive',
    user=request.user,
    summary=f"Archived equipment: {equipment.item_name} (Property #: {equipment.item_propertynum})"
)
    messages.success(request, "Equipment sent to archive.")
    return redirect('equipments:index')

@login_required
def archived_equipment_table_json(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = Equipment.objects.filter(is_archived=True).select_related('category', 'status', 'emp')

    if search_value:
        qs = qs.filter(
            Q(item_propertynum__icontains=search_value) |
            Q(item_name__icontains=search_value) |
            Q(item_desc__icontains=search_value) |
            Q(category__name__icontains=search_value) |
            Q(status__name__icontains=search_value) |
            Q(po_number__icontains=search_value) |
            Q(fund_source__icontains=search_value) |
            Q(supplier__icontains=search_value) |
            Q(item_amount__icontains=search_value) |
            Q(assigned_to__icontains=search_value) |
            Q(end_user__icontains=search_value) |
            Q(location__icontains=search_value) |
            Q(current_location__icontains=search_value) |
            Q(item_purdate__icontains=search_value) |
            Q(project_name__icontains=search_value)
        )

    total = Equipment.objects.filter(is_archived=True).count()
    filtered = qs.count()
    equipments = qs.order_by('-item_purdate')[start:start+length]

    data = []
    for eq in equipments:
        data.append([
            '',  # checkbox placeholder
            eq.id,
            f'<img src="{eq.user_image.url if eq.user_image else ""}" class="img-thumbnail" style="width:32px;height:32px;object-fit:cover;">',
            eq.item_propertynum,
            eq.item_name,
            eq.item_desc or 'None',
            eq.po_number or 'None',
            f'₱{eq.item_amount:,.2f}',
            eq.end_user or 'None',
            eq.category.name,
            f'{eq.status.name} {"<span class=\'badge bg-secondary ms-1\'>Deleted</span>" if eq.is_archived else ""}',
            eq.date_archived.strftime('%Y-%m-%d %H:%M') if eq.date_archived else 'None',
            f'{eq.archived_by.get_full_name() if eq.archived_by else "None"}',
            f'''
            <a class="btn btn-sm btn-outline-secondary" href="/equipments/unarchive/{eq.id}/" onclick="return confirm('Unarchive this equipment?');">
              <i class="bi bi-arrow-counterclockwise"></i> Recover
            </a>
            '''
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': data,
    })

@login_required
def unarchive_equipment(request, pk):
    eq = get_object_or_404(Equipment, pk=pk)
    eq.is_archived = False
    eq.save()
    EquipmentActionLog.objects.create(
    equipment=eq,
    action='unarchive',
    user=request.user,
    summary=f"Unarchived equipment: {eq.item_name} (Property #: {eq.item_propertynum})"
)
    return redirect('equipments:archived_equipments')

@login_required
def equipment_history_json(request, equipment_id):
    history = EquipmentHistory.objects.filter(equipment_id=equipment_id).order_by('-changed_at')
    data = [
        {
            'changed_at': h.changed_at.strftime('%Y-%m-%d %H:%M'),
            'action': h.action,
            'field_changed': h.field_changed,
            'old_value': h.old_value,
            'new_value': h.new_value,
            'changed_by': h.changed_by.get_full_name() or h.changed_by.username
        }
        for h in history
    ]
    return JsonResponse(data, safe=False)

@login_required
@user_passes_test(is_admin_or_superadmin)
def history_logs(request):
    logs = EquipmentActionLog.objects.select_related('user', 'equipment').order_by('-timestamp')[:500]  # Limit for performance
    return render(request, 'equipments/history_logs.html', {'logs': logs})

@login_required
@user_passes_test(is_admin_superadmin_encoder)
def clear_history_logs(request):
    if request.method == 'POST':
        EquipmentActionLog.objects.all().delete()
        EquipmentHistory.objects.all().delete()  # Optional: clear field-level history too
        messages.success(request, "All history logs have been cleared.")
    return redirect('equipments:history_logs')

@login_required
@user_passes_test(is_admin_superadmin_encoder)
def reports_page(request):
    from .models import Equipment, Category
    from django.db.models import Sum
    categories = Category.objects.all()
    suppliers = Equipment.objects.exclude(supplier__isnull=True).exclude(supplier='').values_list('supplier', flat=True).distinct()
    selected_category = request.GET.get('category', '')
    selected_supplier = request.GET.get('supplier', '')
    eqs = Equipment.objects.all()
    if selected_category:
        eqs = eqs.filter(category_id=selected_category)
    if selected_supplier:
        eqs = eqs.filter(supplier=selected_supplier)
    total_asset = eqs.aggregate(total=Sum('item_amount'))['total'] or 0

    # Asset value by category
    asset_by_category = (
        eqs.values('category__name')
        .annotate(total=Sum('item_amount'))
        .order_by('-total')
    )

    # Asset count by category
    asset_count_by_category = (
        eqs.values('category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Top suppliers by asset value
    top_suppliers = (
        eqs.values('supplier')
        .annotate(total=Sum('item_amount'))
        .order_by('-total')[:10]
    )

    # Asset status breakdown
    status_breakdown = (
        eqs.values('status__name')
        .annotate(count=Count('id'), total=Sum('item_amount'))
        .order_by('-count')
    )

    # Recently added assets (last 5)
    recent_assets = eqs.order_by('-created_at')[:5]

    # Monthly purchases (current year)
    from django.utils import timezone
    from django.db.models.functions import TruncMonth, ExtractYear
    now = timezone.now()
    current_year = now.year
    monthly_purchases = (
        eqs.filter(item_purdate__year=current_year)
        .annotate(month=TruncMonth('item_purdate'))
        .values('month')
        .annotate(count=Count('id'), total=Sum('item_amount'))
        .order_by('month')
    )

    # Yearly purchases
    yearly_purchases = (
        eqs.exclude(item_purdate=None)
        .annotate(year=ExtractYear('item_purdate'))
        .values('year')
        .annotate(count=Count('id'), total=Sum('item_amount'))
        .order_by('year')
    )

    # Assets by Location and Status
    assets_by_location_status = (
        eqs.values('location', 'status__name')
        .annotate(count=Count('id'), total=Sum('item_amount'))
        .order_by('location', 'status__name')
    )

    # For filter dropdowns
    locations = Equipment.objects.values_list('location', flat=True).distinct().order_by('location')
    statuses = Equipment.objects.values_list('status__name', flat=True).distinct().order_by('status__name')
    selected_location = request.GET.get('location', '')
    selected_status = request.GET.get('status', '')
    if selected_location:
        assets_by_location_status = assets_by_location_status.filter(location=selected_location)
    if selected_status:
        assets_by_location_status = assets_by_location_status.filter(status__name=selected_status)

    # CSV Export
    if request.GET.get('export_location_status') == '1':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="assets_by_location_status.csv"'
        writer = csv.writer(response)
        writer.writerow(['Location', 'Status', 'Asset Count', 'Total Value (₱)'])
        for row in assets_by_location_status:
            writer.writerow([
                row['location'] or '(None)',
                row['status__name'] or '(None)',
                row['count'],
                f"{row['total']:.2f}" if row['total'] is not None else '0.00'
            ])
        return response

    context = {
        'categories': categories,
        'suppliers': suppliers,
        'selected_category': selected_category,
        'selected_supplier': selected_supplier,
        'total_asset': total_asset,
        'asset_by_category': asset_by_category,
        'asset_count_by_category': asset_count_by_category,
        'top_suppliers': top_suppliers,
        'status_breakdown': status_breakdown,
        'recent_assets': recent_assets,
        'monthly_purchases': monthly_purchases,
        'yearly_purchases': yearly_purchases,
        'assets_by_location_status': assets_by_location_status,
        'locations': locations,
        'statuses': statuses,
        'selected_location': selected_location,
        'selected_status': selected_status,
    }
    return render(request, 'reports/reports.html', context)




