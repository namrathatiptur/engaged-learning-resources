"""
URL configuration for config project.

Project-wide 404/500 use Django defaults (HTML) for /admin/ and public pages; views
return JSON from json_error_response only where explicitly used (e.g. activities).

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from activities import views as activities_views

from .media_serve import protected_media

urlpatterns = [
    path("", activities_views.home, name="home"),
    path("contact/", activities_views.contact, name="contact"),
    path("team/", activities_views.team, name="team"),
    path("consulting/", activities_views.consulting, name="consulting"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("activities/", include("activities.urls")),
    path("tags/", activities_views.tag_list),
    path("categories/", activities_views.category_list),
    # Uploaded materials: never expose via public static() — require login (same as preview/download).
    path("media/<path:path>", protected_media),
]
