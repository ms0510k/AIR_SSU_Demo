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

    url(r'^layout_index/', views.layout_index, name="poll_layout"),
    url(r'^layout_index_GoingOut/', views.layout_index_goingout, name="poll_layout_goout"),
    url(r'^layout_index_ComingBack/', views.layout_index_comeback, name="poll_layout_comeback"),
    url(r'^jsontest/$', views.parse_json, name='jason_test'),
    url(r'^generator_layout/generate_data/$', views.generate_data, name='generate_data'),  # @jaeseung
    url(r'^profilelearner/LoadData/$', views.LoadData, name='LoadData'),  #민성 load data 버튼 누를시 ajax url
    url(r'^smartButler/set_context/$', views.set_context, name='set_context'),
    url(r'^smartButler/fire_rule/$', views.fire_rule, name='fire_rule'),
    url(r'^smartButler/init_server/$', views.init_server, name='init_server'),
    url(r'^smartButler/init_server_input/$', views.init_server_for_input, name='init_server_input'),
    url(r'^smartButler/get_input/$', views.get_input, name='get_input'),
    url(r'^smartButler/get_motion_value/$', views.get_motion_sensor_value, name='get_motion_value'),
    url(r'^smartButler/set_butler_command/$', views.set_butler_command, name='set_butler_command'),
    url(r'^smartButler/get_weather_data/$', views.get_weather_data_for_UI, name='get_weather_data'),
    url(r'^smartButler/get_door_value/$', views.get_door_sensor_value, name='get_door_value'),
    url(r'^demo/percept/$', views.percept, name='percept'),
    url(r'^popup/', views.layout_index_popup, name="poll_layout_popup"),
    url(r'^generator_layout/generate_submit/$', views.generate_submit, name='generate_submit'),  # 민성
    url(r'^generator_layout/', views.generator_layout, name="poll_generator_layout"),
    url(r'^profilelearner/LoadData/$', views.LoadData, name='LoadData'),  # 민성 load data 버튼 누를시 ajax url
    url(r'^profilelearner/RunProfileLearner/$', views.RunProfileLearner, name='RunProfileLearner'),
    # 민성 load data 버튼 누를시 ajax url
    url(r'^profilelearner/', views.profilelearner, name="poll_profilelearner"),  # 민성
    url(r'^smartButler/load_profile/$', views.load_profile, name='load_profile'),


]
