from django.contrib import admin
from django.urls import path
from . import views
from . import viewschrome
from . import viewsvscode

urlpatterns = [
    path('', views.home, name='home'),
    path('chrome/', viewschrome.chrome_view, name='chrome_view'),
    path('vscode/', viewsvscode.vscode_view, name='vscode_view'),
]
