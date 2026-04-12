import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import FloorPlan, Hotspot
from .forms import FloorPlanForm, HotspotForm, FloorPlanAttachmentForm
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

@login_required
def upload_floor_plan(request):
    if request.method == 'POST':
        form = FloorPlanForm(request.POST, request.FILES)
        if form.is_valid():
            floor_plan = form.save(commit=False)
            floor_plan.owner = request.user
            floor_plan.save()
            return redirect('floor_plan_list')
    else:
        form = FloorPlanForm()
    return render(request, 'upload_floor_plan.html', {'form': form})


@login_required
def floor_plan_list(request):
    plans = FloorPlan.objects.filter(owner=request.user)
    return render(request, 'floor_plan_list.html', {'plans': plans})


@login_required
def floor_plan_detail(request, pk):
    plan = get_object_or_404(FloorPlan, pk=pk, owner=request.user)

    if request.method == 'POST':
        # Check if it's a file upload for the floor plan
        if 'upload_attachment' in request.POST:
            attachment_form = FloorPlanAttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.floor_plan = plan
                attachment.save()
                return redirect('floor_plan_detail', pk=pk)
        else:
            # Handle hotspot form
            form = HotspotForm(request.POST, request.FILES)
            if form.is_valid():
                hotspot = form.save(commit=False)
                hotspot.floor_plan = plan
                hotspot.save()
                return redirect('floor_plan_detail', pk=pk)
    
    form = HotspotForm()
    attachment_form = FloorPlanAttachmentForm()

    return render(request, 'floor_plan_detail.html', {
        'floorplan': plan,
        'form': form,
        'attachment_form': attachment_form
    })


@login_required
def add_hotspot(request, pk):
    plan = get_object_or_404(FloorPlan, pk=pk)
    if request.method == 'POST':
        form = HotspotForm(request.POST, request.FILES)
        if form.is_valid():
            hotspot = form.save(commit=False)
            hotspot.floor_plan = plan
            hotspot.save()
            return redirect('floor_plan_detail', pk=pk)
    else:
        form = HotspotForm()
    return render(request, 'add_hotspot.html', {'form': form, 'floorplan': plan})

@login_required
def update_hotspot_position(request, hotspot_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        x = data.get('x_percent')
        y = data.get('y_percent')

        hotspot = get_object_or_404(Hotspot, id=hotspot_id, floor_plan__owner=request.user)
        hotspot.x_percent = x
        hotspot.y_percent = y
        hotspot.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def hotspot_preview(request, pk):
    hotspot = get_object_or_404(Hotspot, pk=pk, floor_plan__owner=request.user)
    return render(request, 'hotspot_preview.html', {'hotspot': hotspot})

@login_required
@require_POST
def delete_floor_plan(request, pk):
    plan = get_object_or_404(FloorPlan, pk=pk, owner=request.user)
    plan.delete()
    return redirect('floor_plan_list')

@login_required
@require_POST
def delete_hotspot(request, hotspot_id):
    hotspot = get_object_or_404(Hotspot, id=hotspot_id, floor_plan__owner=request.user)
    plan_id = hotspot.floor_plan.id
    hotspot.delete()
    return redirect('floor_plan_detail', pk=plan_id)

@login_required
@require_POST
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(FloorPlanAttachment, id=attachment_id, floor_plan__owner=request.user)
    plan_id = attachment.floor_plan.id
    attachment.delete()
    return redirect('floor_plan_detail', pk=plan_id)