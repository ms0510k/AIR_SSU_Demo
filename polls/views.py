from django.http import HttpResponse
from django.shortcuts import render
from DjangoTest.settings import BASE_DIR
import json
import codecs
import socket
import webbrowser
import urllib.request
import pytz

from sklearn.mixture import GaussianMixture

import numpy as np
import math
import csv
import os
import pandas as pd
from datetime import datetime

"""바른기술 측에서 넘겨주는 음성명령어를 담고 있는 변수"""
butler_command = ""

port = 10002
address = "192.168.1.20"

""" @181021 페이지를 연결하기위한 함수"""


def demo(request):
    return render(request, "../templates/demo.html")


''' @jaeseung 
Function Definition: 
   주어진 디렉터리를 recursive 하게 탐색하며
   csv 파일들을 확인하고 같이 주어진 리스트에 
   찾아낸 csv파일의 주소를 추가해주는 함수
Input:
    dirname: 탐색할 디렉터리 주소를 담고 있는 변수
    file_list : 탐색한 디렉터리에서 찾아낸 csv 파일의 경로를 담고 있는 변수
Return:
'''


def search_dir(dirname, file_list):
    for (path, dir, files) in os.walk(dirname):
        for filename in files:
            ext = os.path.splitext(filename)[-1]
            if ext == '.csv':
                # print("%s/%s" % (path, filename))
                tmp = path + '/' + filename
                # print(tmp)
                file_list.append(tmp)


''' @jaeseung
Function Definition: 
    생성할 데이터를 저장하기 전에 미리 데이터가 저장될
    디렉터리들을 생성해주는 함수
Input:
Return:
'''


def make_dir():
    root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")
    user_list = ['park', 'kim', 'choi']
    device_list = ['airconditioner', 'aircleaner', 'bulb', 'robotcleaner', 'tv']
    season_list = ['spring', 'summer', 'fall', 'winter']
    week_list = ['weekdays', 'weekend']
    weather_list = ['sunny', 'blur', 'rainy']
    choose_list = []

    for i in range(len(user_list)):
        for j in range(len(season_list)):
            for k in range(len(week_list)):
                for n in range(len(device_list)):
                    choose_list.append(
                        root_dir + "/" + user_list[i] + "/" + season_list[j] + "/"
                        + week_list[k] + "/" + device_list[n])

    for i in choose_list:
        if not os.path.exists(i):
            os.makedirs(i)


'''
Function Definition: 
    웹 상에서 받은 정보들을 JESS Engine의 입력에 맞도록
    Parsing 한 후, JESS Engine과 통신하여 결과를 얻어내 
    다시 웹 상에 정보를 보내주는 함수
Input:
    request: 웹 상에서 넘겨주는 정보들을 담고 있는 변수
Return:
    웹 상에 다시 출력해줄 정보들을 담고 있는 변수
'''
# @jaeseung
num_stamp = 0
start = 0
end = 0

def fire_rule(request):
    # print("test")
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        # print("good")
        # JESS Engine에 연결한 후, 웹 상에서 넘어온 정보들을 Parsing
        engine = connect_jess_engine(21000)
        # @jaeseung : give engine file_name
        results = engine.run_engine(file_name)
        # print(results)

        time_list, response_df = parse_results(results)

        # global num_stamp
        # if num_stamp < response_df.shape[0]:
        #     num_stamp += 1
        #
        # print(time_list[num_stamp])
        # print(response_df.iloc[[num_stamp]])

        result = response_df.iloc[num_stamp].to_json(orient="records")
        # print(response_df.iloc[num_stamp].to_json(orient="records"))

        global end
        result = response_df.iloc[end].to_json(orient="records")
        return HttpResponse(result, content_type="application/json")


def parse_results(results):
    results_line = results.split("\n")
    time_list = []
    data_list = []
    value_list = []
    for i in results_line:
        time_list.append(i[:16])
        data_list.append(i[24:])

    for d in data_list[:-1]:
        tmp_list = []
        for i, c in enumerate(d):
            if "=" == c:
                tmp_list.append(d[i + 1])
        value_list.append(tmp_list)

    header = ["Refreshment", "Reading", "ArrangeThing", "Drink",  "Meal", "Clothing", "Cleaning",
               "CommunicationWithPerson",  "HealthCare", "PrepareMeal", "Smoking",  "Communication", "WatchingTV"]
    df = pd.DataFrame(value_list, columns=header)
    df.pop('Reading')
    df.pop('Clothing')
    df.pop('HealthCare')
    # print(df.head())
    return time_list, df


'''
Function Definition: 
    해당 포트로 열린 JESS Engine과 연결하여 그 Engine의 주소를 Return하는 함수
Input:
    port: JESS Engine에 연결하기 위한 포트
Return:
    연결된 JESS Engine
'''


def connect_jess_engine(port):
    from py4j.java_gateway import JavaGateway, GatewayParameters
    gateway = JavaGateway(gateway_parameters=GatewayParameters(port=port))
    engine = gateway.entry_point.getreteEngine()

    return engine


'''
Function Definition: 
    json 파일의 이름을 받아서 JSON File의 내용들을 Load하여 Return 하는 함수
Input:
    json_file: json file의 이름
Return:
    해당 json 파일의 내용
'''


def read_json(json_file):
    dir_json = os.path.join(BASE_DIR, "jsonSet/" + json_file)

    with codecs.open(dir_json, 'r', 'utf-8') as json_data:
        # 선택된 메뉴가 필요한 재료들
        json_result = json.load(json_data)

    return json_result


def convert_time(time):
    time_object = datetime.strptime(time, "%Y_%m_%d_%H_%M_%S_%f")
    cut_microsec = time_object.replace(microsecond=0)
    return cut_microsec.strftime("%Y-%m-%d %H:%M:%S")

def percept(request):  ##################### perceptajax
    if request.method == 'POST':
        # print("def percept POST success")
        file_name = request.POST.get('file_name')
        cur = request.POST.get('cur')
        cur = round(float(cur))

        dur = request.POST.get('dur')
        dur = round(float(dur))

        # print("percept : [", file_name, "]")
        # header_name = ["Start Time", "End Time", "Pose", "Action"]
        header_name = ["Time", "Pose", "Action"]
        root_dir = os.path.join(BASE_DIR, "polls/static/percept/")
        file_loc = root_dir + file_name
        print("file_loc"+file_loc)

        df_from_file = pd.read_csv(file_loc, delimiter='\t', header=None, names=header_name, index_col=None,
                                   encoding='UTF8', engine="python")
        df_time_converted = df_from_file
        df_time_converted["Time"] = df_from_file["Time"].apply(convert_time)
        # df_time_converted["Start Time"] = df_from_file["Start Time"].apply(convert_time)
        # df_time_converted["End Time"] = df_from_file["End Time"].apply(convert_time)

        global num_stamp
        global start
        global end

        start = cur*round(float(df_time_converted.shape[0]/dur))
        end = start + round(float(df_time_converted.shape[0]/dur))
        print(df_time_converted.shape)
        print("########################################################################")
        print(start, '\t', end)

        percept_row = pd.DataFrame(df_time_converted.iloc[start:end])
        response = HttpResponse(percept_row.to_html(index=False, classes='table table-bordered table-fixed'),
                                content_type='text/html')
        print(response)
        return response

def time(request):  #################### time 배속 구해주기
    print("time def")
    if request.method == 'POST':
        print("in post")
        file_name = request.POST.get('file_name')
        dur = request.POST.get('dur')
        root_dir = os.path.join(BASE_DIR, "polls/static/percept/")
        print("root_dir"+root_dir)
        file_loc = root_dir + file_name
        print("file_loc"+file_loc)
        file = pd.read_csv(file_loc, delimiter='\t', header=None, index_col=None,
                           encoding='UTF8', engine="python")
        print(file)
        print(len(file))
        dur = round(float(dur), 3)
        print(type(dur))
        result = round(dur/len(file), 5)*1000
        print(result)
        return HttpResponse(json.dumps(result), content_type="application/json")






















































    