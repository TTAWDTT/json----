from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('file/', views.view_file, name='view_file'),
    path('raw/', views.raw_file, name='raw_file'),
]
