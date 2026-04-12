from django.urls import path # type: ignore
from . import views

urlpatterns = [
    path('', views.floor_plan_list, name='floor_plan_list'),
    path('upload/', views.upload_floor_plan, name='upload_floor_plan'),
    path('floorplan/<int:pk>/', views.floor_plan_detail, name='floor_plan_detail'),
    path('floorplan/<int:pk>/add_hotspot/', views.add_hotspot, name='add_hotspot'),
    path('hotspot/<int:hotspot_id>/update/', views.update_hotspot_position, name='update_hotspot'),
    path('hotspot/<int:pk>/preview/', views.hotspot_preview, name='hotspot_preview'),
    path('floorplan/<int:pk>/delete/', views.delete_floor_plan, name='delete_floor_plan'),
]