"""DjangoTest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from polls import views

app_name = "polls"

urlpatterns = [
    url(r'^$', views.demo, name="demo"),

    url(r'^smartButler/fire_rule/$', views.fire_rule, name='fire_rule'),
    url(r'^demo/percept/$', views.percept, name='percept'),
    url(r'^time/$', views.time, name='time'),

]
