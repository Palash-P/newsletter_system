"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from newsletters import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/subscribe/', views.subscribe, name='subscribe'),
    path('api/newsletters/', views.newsletter, name='newsletters'),
    path('api/verify/<uuid:token>/', views.verify_email, name='verify-email'),
    path('api/unsubscribe/<uuid:token>/', views.unsubscribe, name='unsubscribe'),
    path('api/newsletters/<int:pk>/send/', views.send_newsletter, name='send-newsletter'),
    path('api/track/open/<int:campaign_id>/', views.track_open, name='track-open'),
    path('api/track/click/<int:campaign_id>/', views.track_click, name='track-click'),
    path('api/analytics/', views.analytics, name='analytics'),
]
