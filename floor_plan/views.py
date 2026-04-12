import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import FloorPlan, Hotspot
from .forms import FloorPlanForm, HotspotForm, FloorPlanAttachmentForm
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST


def upload_floor_plan(request):
    if request.method == 'POST':
        form = FloorPlanForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('floor_plan_list')
    else:
        form = FloorPlanForm()
    return render(request, 'upload_floor_plan.html', {'form': form})


def floor_plan_list(request):
    plans = FloorPlan.objects.all()
    return render(request, 'floor_plan_list.html', {'plans': plans})


def floor_plan_detail(request, pk):
    plan = get_object_or_404(FloorPlan, pk=pk)

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

def update_hotspot_position(request, hotspot_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        x = data.get('x_percent')
        y = data.get('y_percent')

        hotspot = get_object_or_404(Hotspot, id=hotspot_id)
        hotspot.x_percent = x
        hotspot.y_percent = y
        hotspot.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def hotspot_preview(request, pk):
    hotspot = get_object_or_404(Hotspot, pk=pk)
    return render(request, 'hotspot_preview.html', {'hotspot': hotspot})

@require_POST
def delete_floor_plan(request, pk):
    plan = get_object_or_404(FloorPlan, pk=pk)
    plan.delete()
    return redirect('floor_plan_list')