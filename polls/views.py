
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
import datetime

"""바른기술 측에서 넘겨주는 음성명령어를 담고 있는 변수"""
butler_command = ""

port = 10002
address = "192.168.1.20"

""" @181021 페이지를 연결하기위한 함수"""
def demo(request):
    return render(request, "../templates/demo.html")

def index(request):
    return render(request, "../templates/index.html")

def layout_index(request):
    return render(request, "../templates/layout_index.html")

def profilelearner(request): # @minsung
    return render(request, "../templates/profilelearner.html")

def layout_index_goingout(request):
    return render(request, "../templates/layout_index_goingout.html")

def layout_index_comeback(request):
    return render(request, "../templates/layout_index_comeback.html")

# @jaeseung : 접근 가능한 URL 추가
def layout_index_popup(request):
    return render(request, "../templates/popup.html")
def generator_layout(request):
    return render(request, "../templates/generator_layout.html")

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
   주어진 period와 weight, mean, dev를 가지고 
   Gaussian Mixture를 계산하고 이를 리스트로 반환하는 함수

Input:
    min_list : period가 담긴 변수
    w : weight의 리스트가 담긴 변수
    m : mean의 리스트가 담긴 변수
    d : dev의 리스트가 담긴 변수

Return:
    result : Gaussian Mixture가 계산된 리스트가 담긴 변수

'''
def calculate_gaussian(min_list, w, m, d):
    result = []

    listProbabilities = []
    for i in range(len(w)):
        prob = []
        new_prob = []
        for j in range(1440):
            u = ((j - m[i]) / np.abs(d[i]))
            y = (1 / (math.sqrt(2 * math.pi) * np.abs(d[i]))) * math.exp(-u * u / 2)
            prob.append(y)

        # DEBUG
        sum = 0.0
        for asd in prob:
            sum += asd
        #print("Before####ratio ", i, " = " , sum)

        for k in range(1440):
            probability = prob[k] * w[i]
            new_prob.append(probability)

        # DEBUG
        sum = 0.0
        for qwe in new_prob:
            sum += qwe
        #print("After####ratio ", i, " = " , sum)
        listProbabilities.append(new_prob)

    for i in range(1440):
        tempProb = 0.0
        for j in range(len(listProbabilities)):
            tempProbs = listProbabilities[j]
            tempProb += tempProbs[i]
        result.append(tempProb)

    # DEBUG
    sum = 0.0
    for rty in result:
        sum += rty
    print("SUM!!!! = ", sum)

    result = result[int(min_list[0]):int(min_list[-1]) + 1]

    return result


''' @sangwoon 
Function Definition: 
   주어진 Min / Max 값에 따라 values를 rescale 하는 함수
   계절에 따른 Min / Max 값으로 Gaussian Probability를 rescale 하는 함수

Input:
    values : Gaussian Probability의 리스트가 담긴 변수 
    new_min : 계절에 따른 Min 수치가 담긴 변수
    new_max : 계절에 따른 Max 수치가 담긴 변수

Return:
    rescale_output : Rescale 된 Gaussian Probability가 담긴 변수

'''
def rescale(values, new_min, new_max):
    rescale_output = []
    old_min, old_max = min(values), max(values)

    for v in values:
        # rescale
        new_v = (new_max - new_min) / (old_max - old_min) * (v - old_min) + new_min
        # rounds
        round_new_v = round(new_v, 2)
        rescale_output.append(round_new_v)

    return rescale_output


''' @sangwoon 
Function Definition: 
   x축을 시간, y축을 온도 / x축을 시간, y축을 미세먼지 농도로
   하는 Gaussian Mixture를 계산하기 위한 함수 

Input:
    min_list : 데이터를 생성할 period가 담긴 변수

Return:
    temp_prob : 시간에 따른 온도의 Gaussian Mixture가 담긴 변수
    dust_prob : 시간에 따른 미세먼지 농도의 Gaussian Mixture가 담긴 변수

'''
def temperatureDustInfo(min_list):
    temperature_weight = [1.0]
    temperature_mean = [840.0]  # 14:00
    temperature_dev = [150.0]

    finedust_weight = [0.6, 0.4]
    finedust_mean = [660.0, 1020.0]  # 11:00, 17:00
    finedust_dev = [150.0, 90.0]

    temp_prob = calculate_gaussian(min_list, temperature_weight, temperature_mean, temperature_dev)
    dust_prob = calculate_gaussian(min_list, finedust_weight, finedust_mean, finedust_dev)
    return temp_prob, dust_prob

''' @sangwoon 
Function Definition: 
    계절에 따른 온도의 최대값과 최소값을 갖고
    이를 rescale 한 결과를 반환하는 함수

Input:
    min_list : 데이터를 생성할 period가 담긴 변수

Return:
    temp_spring : 봄의 시간에 따른 온도 수치를 담고 있는 변수 
    temp_summer : 여름의 시간에 따른 온도 수치를 담고 있는 변수 
    temp_fall   : 가을의 시간에 따른 온도 수치를 담고 있는 변수 
    temp_winter : 겨울의 시간에 따른 온도 수치를 담고 있는 변수 

'''
def temperatureDataGenerate(min_list):
    tempSpringMin = 15
    tempSpringMax = 25

    tempSummerMin = 25
    tempSummerMax = 35

    tempFallMin = 15
    tempFallMax = 25

    tempWinterMin = -10
    tempWinterMax = 5

    #initialize rescale values
    temp_prob, dust_prob = temperatureDustInfo(min_list)
    # print(temp_prob)
    # print(dust_prob)
    temp_spring = rescale(temp_prob, tempSpringMin, tempSpringMax)
    temp_summer = rescale(temp_prob, tempSummerMin, tempSummerMax)
    temp_fall = rescale(temp_prob, tempFallMin, tempFallMax)
    temp_winter = rescale(temp_prob, tempWinterMin, tempWinterMax)
    return temp_spring, temp_summer, temp_fall, temp_winter

''' @sangwoon 
Function Definition: 
    계절에 따른 미세먼지 농도의 최대값과 최소값을 갖고
    이를 rescale 한 결과를 반환하는 함수

Input:
    min_list : 데이터를 생성할 period가 담긴 변수

Return:
    temp_spring : 봄의 시간에 따른 미세먼지농도 수치를 담고 있는 변수 
    temp_summer : 여름의 시간에 따른 미세먼지농도 수치를 담고 있는 변수 
    temp_fall   : 가을의 시간에 따른 미세먼지농도 수치를 담고 있는 변수 
    temp_winter : 겨울의 시간에 따른 미세먼지농도 수치를 담고 있는 변수 

'''
def finedustDataGenerate(min_list):
    # Set fine dust maximum and minimum values by season

    dustSpringMin = 35
    dustSpringMax = 70

    dustSummerMin = 25
    dustSummerMax = 45

    dustFallMin = 25
    dustFallMax = 45

    dustWinterMin = 35
    dustWinterMax = 70

    #initialize rescale values
    temp_prob, dust_prob = temperatureDustInfo(min_list)
    dust_spring = rescale(dust_prob, dustSpringMin, dustSpringMax)
    dust_summer = rescale(dust_prob, dustSummerMin, dustSummerMax)
    dust_fall = rescale(dust_prob, dustFallMin, dustFallMax)
    dust_winter = rescale(dust_prob, dustWinterMin, dustWinterMax)
    return dust_spring, dust_summer, dust_fall, dust_winter


''' @jaeseung & @sangwoon
Function Definition: 
    주어진 온도와 미세먼지농도 threshold에 따라 작동하는
    에어컨과 공기청정기의 On/Off 정보를 생성하고
    이를 파일로 지정된 위치에 저장해주는 함수  

Input:
    user    : UI 창에서 선택된 user의 이름을 담고 있는 변수 
    start   : UI 창에서 입력된 period의 시작 시간을 담고 있는 변수
    end     : UI 창에서 입력된 period의 종료 시간을 담고 있는 변수
    days    : UI 창에서 입력된 생성할 날짜의 수를 담고 있는 변수
    season  : UI 창에서 선택된 계절의 정보를 담고 있는 변수
    week    : UI 창에서 선택된 주중 / 주말 정보를 담고 있는 변수
    weather : UI 창에서 선택된 날씨 정보를 담고 있는 변수
    aircon_thres        : UI 창에서 입력된 에어컨의 threshold 값을 담고 있는 변수
    aircleaner_thres    : UI 창에서 입력된 공기청정기의 threshold 값을 담고 있는 변수

Return:
    반환하는 변수는 없지만 생성된 데이터를 파일로 지정된 위치에 저장

'''
def thresholdGenerator(user, start, end, days, season, week, weather, aircon_thres, aircleaner_thres):

    day_start = "0:00"
    day_s = datetime.datetime.strptime(day_start, '%H:%M')
    s = datetime.datetime.strptime(start, '%H:%M')
    e = datetime.datetime.strptime(end, '%H:%M')

    time = []
    min_list = []
    while s < e:
        time.append(s)
        min_list.append((s - day_s).seconds / 60)
        s += datetime.timedelta(minutes=1)

    time = [t.strftime("%H:%M") for t in time]

    temp_spring, temp_summer, temp_fall, temp_winter = temperatureDataGenerate(min_list)
    dust_spring, dust_summer, dust_fall, dust_winter = finedustDataGenerate(min_list)
    Temperature = []
    if season.lower() == "spring":
        Temperature = temp_spring
        Fine_dust = dust_spring
    if season.lower() == "summer":
        Temperature = temp_summer
        Fine_dust = dust_summer
    if season.lower() == "fall":
        Temperature = temp_fall
        Fine_dust = dust_fall
    if season.lower() == "winter":
        Temperature = temp_winter
        Fine_dust = dust_winter

    Temp_1and0 = []
    Dust_1and0 = []

    Temp_onoff = []
    Dust_onoff = []

    for i in range(len(Temperature)):
        if Temperature[i] >= aircon_thres:
            Temp_1and0.append(1)
            Temp_onoff.append('On')
        else:
            Temp_1and0.append(0)
            Temp_onoff.append('Off')

        if Fine_dust[i] >= aircleaner_thres:
            Dust_1and0.append(1)
            Dust_onoff.append('On')
        else:
            Dust_1and0.append(0)
            Dust_onoff.append('Off')


    root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")

    for i in range(days):
        write_loc = root_dir + user.lower() + "/" + season.lower() + "/" + week.lower() + "/" + "Airconditioner".lower() \
                    + "/" + str(i) + ".csv"
        f = open(write_loc, 'w', encoding='utf-8', newline='')
        wr = csv.writer(f, delimiter='\t')

        for i in range(len(time)):
            wr.writerow([time[i], min_list[i], user, "Airconditioner", "1", Temperature[i], Temp_onoff[i], season, week, weather])
        f.close()

    for i in range(days):
        write_loc = root_dir + user.lower() + "/" + season.lower() + "/" + week.lower() + "/" + "Aircleaner".lower() \
                    + "/" + str(i) + ".csv"
        f = open(write_loc, 'w', encoding='utf-8', newline='')
        wr = csv.writer(f, delimiter='\t')

        for i in range(len(time)):
            wr.writerow([time[i], min_list[i], user, "Aircleaner", "2", Fine_dust[i], Dust_onoff[i], season, week, weather])
        f.close()

''' @jaeseung & @sangwoon
Function Definition: 
    주어진 정보와 weight, mean, dev 값에 따라 
    Gaussian Mixture를 계산하여 데이터를 생성하고
    이를 파일로 지정된 위치에 저장해주는 함수  

Input:
    user    : UI 창에서 선택된 user의 이름을 담고 있는 변수 
    start   : UI 창에서 입력된 period의 시작 시간을 담고 있는 변수
    end     : UI 창에서 입력된 period의 종료 시간을 담고 있는 변수
    days    : UI 창에서 입력된 생성할 날짜의 수를 담고 있는 변수
    season  : UI 창에서 선택된 계절의 정보를 담고 있는 변수
    week    : UI 창에서 선택된 주중 / 주말 정보를 담고 있는 변수
    weather : UI 창에서 선택된 날씨 정보를 담고 있는 변수
    device  : 생성할 device 데이터의 이름을 담고 있는 변수
    weight  : UI 창에서 입력된 device의 weight 리스트를 담고 있는 변수
    mean    : UI 창에서 입력된 device의 mean 리스트를 담고 있는 변수
    dev     : UI 창에서 입력된 device의 dev 리스트를 담고 있는 변수

Return:
    반환하는 변수는 없지만 생성된 데이터를 파일로 지정된 위치에 저장

'''
def gaussian_generetor(user, start, end, days, season, week, weather, device, weight, mean, dev):
    print("gaussian_generetor start!")
    # col0 Time data generate. (24*60 = 1440 minute)
    day_start = "0:00"
    day_s = datetime.datetime.strptime(day_start, '%H:%M')
    s = datetime.datetime.strptime(start, '%H:%M')
    e = datetime.datetime.strptime(end, '%H:%M')

    time = []
    min_list = []
    while s < e:
        time.append(s)
        min_list.append((s - day_s).seconds / 60)
        s += datetime.timedelta(minutes=1)

    time = [t.strftime("%H:%M") for t in time]

    # col1 User_id data generate.
    # col2 Device data generate. (TV, Bulb, RobotCleaner, AirCleaner, AirConditioner)
    # col3 n-components data generate. (number of gaussian mixtures)
    n_com = str(len(weight))
    # col4 Gaussian Mixture Probability data generate. (extract to calculateGaussian Function)
    prob = []

    prob = calculate_gaussian(min_list, weight, mean, dev)
    #print(len(prob))
    #print(prob)

    # col5 ON/OFF data generate.
    temporary_on_off = []
    on_off = []
    on_range_min = []
    on_range_max = []
    for i in range(len(mean)):
        on_range_min.append(mean[i] - (dev[i]))
        on_range_max.append(mean[i] + (dev[i]))

    for j in range(1440):
        check_on = False
        for i in range(len(mean)):
            if on_range_min[i] <= j and j <= on_range_max[i]:
                check_on = True
            else:
                continue

        if check_on:
            temporary_on_off.append("On")
        else:
            temporary_on_off.append("Off")

    on_off = temporary_on_off[int(min_list[0]):int(min_list[-1])+1]

    # col6 Season data generate. (Spring, Summer, Fall, Winter)
    # col7 Week data generate. (Weekdays, Weekend)
    # col8 Weather data generate. (Sunny, Blur, Rainy)

    # write the csv file
    root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")

    print("Generate " + device + " Data Start!")

    for i in range(days):
        write_loc = root_dir + user.lower() + "/" + season.lower() + "/" + week.lower() + "/" + device.lower() \
                    + "/" + str(i) + ".csv"
        f = open(write_loc, 'w', encoding='utf-8', newline='')
        wr = csv.writer(f, delimiter='\t')

        for i in range(len(time)):
            wr.writerow([time[i], min_list[i], user, device, n_com, prob[i], on_off[i], season, week, weather])

        f.close()

    print("Generate " + device + " Data End!")

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


''' @jaeseung 
Function Definition: 
    request를 통해 UI 창으로부터 받은 수치에 따라 
    모든 device의 데이터를 생성하고 저장하는 함수
    데이터 생성과 저장이 완료되었을 경우 
    UI 창에서 생성된 데이터를 visualize 하기위해 필요한 데이터를 
    response로 전달하는 함수 

Input:
    request : UI 창에 입력된 수치들을 python함수에 전달할 수 있도록 
              POST 형식으로 값을 가지고 있는 변수

Return:
    데이터 visualize를 위해 필요한 그래프 데이터를 HttpResponse형태로 반환

'''
def generate_data(request):
    print("def LoadData success")
    if request.method == 'POST':
        print("def LoadData POST success")
        user = request.POST.get('user')
        start = request.POST.get('start')
        end = request.POST.get('end')
        days = int(request.POST.get('days'))
        season = request.POST.get('season')
        week = request.POST.get('week')
        weather = request.POST.get('weather')

        bulb_weight = list(map(float, request.POST.get('bulb_weight').replace(",", "").split()))
        bulb_mean = list(map(str, request.POST.get('bulb_mean').replace(",", "").split()))
        bulb_dev = list(map(float, request.POST.get('bulb_dev').replace(",", "").split()))
        robot_weight = list(map(float, request.POST.get('robot_weight').replace(",", "").split()))
        robot_mean = list(map(str, request.POST.get('robot_mean').replace(",", "").split()))
        robot_dev = list(map(float, request.POST.get('robot_dev').replace(",", "").split()))
        tv_weight = list(map(float, request.POST.get('tv_weight').replace(",", "").split()))
        tv_mean = list(map(str, request.POST.get('tv_mean').replace(",", "").split()))
        tv_dev = list(map(float, request.POST.get('tv_dev').replace(",", "").split()))

        aircon_thres = int(request.POST.get('aircon_thres'))
        aircleaner_thres = int(request.POST.get('aircleaner_thres'))

        day_start = "0:00"
        day_s = datetime.datetime.strptime(day_start, '%H:%M')

        bulb_mean_value = []
        for i in bulb_mean:
            min_val = datetime.datetime.strptime(i, '%H:%M')
            bulb_mean_value.append((min_val - day_s).seconds / 60)
        robot_mean_value = []
        for i in robot_mean:
            min_val = datetime.datetime.strptime(i, '%H:%M')
            robot_mean_value.append((min_val - day_s).seconds / 60)
        tv_mean_value = []
        for i in tv_mean:
            min_val = datetime.datetime.strptime(i, '%H:%M')
            tv_mean_value.append((min_val - day_s).seconds / 60)

        device = ["Airconditioner", "Aircleaner", "Bulb", "Robotcleaner", "TV"]

        print("Make Directory Structure Started!")
        make_dir()

        print("Make Directory Structure Finished!")
        gaussian_generetor(user, start, end, days, season, week, weather, device[2], bulb_weight, bulb_mean_value, bulb_dev)
        print("Bulb Data Generated!")
        gaussian_generetor(user, start, end, days, season, week, weather, device[3], robot_weight, robot_mean_value, robot_dev)
        print("RobotCleaner Data Generated!")
        gaussian_generetor(user, start, end, days, season, week, weather, device[4], tv_weight, tv_mean_value, tv_dev)
        print("TV Data Generated!")

        thresholdGenerator(user, start, end, days, season, week, weather,  aircon_thres, aircleaner_thres)
        print("Aircon, Aircleaner Data Generated!")

        temp_min = 15
        temp_max = 25
        dust_min = 35
        dust_max = 70
        if weather == "spring":
            temp_min = 15
            temp_max = 25
            dust_min = 35
            dust_max = 70
        elif weather == "summer":
            temp_min = 25
            temp_max = 35
            dust_min = 25
            dust_max = 45
        elif weather == "fall":
            temp_min = 15
            temp_max = 25
            dust_min = 25
            dust_max = 45
        elif weather == "winter":
            temp_min = -10
            temp_max = 5
            dust_min = 35
            dust_max = 70

        temp_list = []
        temp_list.append(temp_min)
        temp_list.append(temp_max)
        temp_list.append(aircon_thres)

        temp_list.append(dust_min)
        temp_list.append(dust_max)
        temp_list.append(aircleaner_thres)

        # print(temp_list)
        header_list = ["Temp_Min", "Temp_Max", "Temp_Thres", "Dust_Min", "Dust_Max", "Dust_Thres"]
        temp_df = pd.DataFrame([temp_list], columns=header_list)
        # print(temp_df)
        root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")
        write_loc = root_dir + user.lower() + "/" + season.lower() + "/" + week.lower() + "/" + "context_threshold.csv"
        temp_df.to_csv(write_loc, sep='\t')

        #result = "Generate SUCCESS"
        #response = HttpResponse(result, content_type='text/html')
        #return response
        return draw_generate(user, season, week)

def parse_json(request):
    if request.method == 'POST':
        dir_json = os.path.join(BASE_DIR, "jsonSet/device_info.json")

        with open(dir_json, 'r') as json_data:
            dev_info = json.load(json_data)

        return HttpResponse(
            json.dumps(dev_info),
            content_type="application/json")

""" 바른기술 측에서 넘어오는 자연어 입력을 받는 서버 """
def init_server_for_input(request):
    if request.method == 'POST':
        # port = 10002

        global port
        global address
        global butler_command

        # Set host
        server_address = (address, port + 1)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print("Get Host Name: " + socket.gethostname())

        sock.bind(server_address)
        sock.listen(5)

        print("TCP Server is waiting for client on port to get natural language input " + str(port + 1))

        while True:
            # wait to accept a connection - blocking call
            conn, addr = sock.accept()

            conn.settimeout(2.0)
            print("Connected with " + addr[0] + ":" + str(addr[1]))

            rbuff = b""

            while True:
                try:
                    print("Before Receive")
                    ret = conn.recv(1024)
                    print("After Receive: " + str(ret))

                    if not ret:
                        print("Break!")
                        break

                    rbuff += ret
                    print(str(len(rbuff)))
                except Exception as e:
                    print(str(e))
                    break

            order = rbuff.decode('euc-kr')

            # 바른기술측에서 넘어온 Device 정보들을 받아서 Parsing한 후, File로 쓸까..?
            conn.send(rbuff + bytes(" Received", 'utf-8'))

            dir_json = os.path.join(BASE_DIR, "jsonSet/" + 'order.txt')
            with open(dir_json, 'w') as outfile:
                # 입력받은 명령을 전역변수에 저장
                butler_command = order.strip().replace(" ", "")
                print("Received Butler Command: " + str(butler_command))
                outfile.write(order)
                outfile.close()

            # 연결 끊음
            conn.close()

    return HttpResponse(json.dumps("Success"),
                        content_type="application/json")


"""Motion Sensor로부터 값을 읽어들여서 던짐"""
def get_motion_sensor_value(request):
    if request.method == 'POST':
        dic_all_holds = {}

        # print("Get Motion Sensor Value from JSON")

        json_file = "device_info.json"

        device_info = read_json(json_file)
        # "Device" Key안에 여러 Device들이 존재하고 있음
        device_info_with_keys = device_info["Device"]

        device_keys = device_info_with_keys.keys()

        dev_state = ""

        # Hue Lamp, ...
        for device_key in device_keys:
            device_info = device_info_with_keys[device_key]

            # Hue라는 단어가 Device Key에 존재하는 경우
            if "동체센서" in device_key:
                # 하나의 Device (Hue 전구 내에서도 하나)
                # []로 묶여 있어서 for문으로 풀어줘야함
                for single_device_info in device_info:
                    dev_state = single_device_info["motion"]
            else:
                continue

        print("Motion Sensor: " + str(dev_state))

        dic_all_holds["Motion"] = [dev_state]

        return HttpResponse(json.dumps(dic_all_holds),
                            content_type="application/json")


"""Door Sensor로부터 값을 읽어들여서 던짐"""
def get_door_sensor_value(request):
    if request.method == 'POST':
        dic_all_holds = {}

        print("Get Motion Sensor Value from JSON")

        json_file = "device_info.json"

        device_info = read_json(json_file)
        # "Device" Key안에 여러 Device들이 존재하고 있음
        device_info_with_keys = device_info["Device"]

        device_keys = device_info_with_keys.keys()

        dev_state = ""

        # Hue Lamp, ...
        for device_key in device_keys:
            device_info = device_info_with_keys[device_key]

            # 도어센서1 단어가 Device Key에 존재하는 경우
            if "도어센서1" in device_key:
                # 하나의 Device (Hue 전구 내에서도 하나)
                # []로 묶여 있어서 for문으로 풀어줘야함
                for single_device_info in device_info:
                    dev_state = single_device_info["isOpen"]
            else:
                continue

        dic_all_holds["Door"] = [dev_state]

        return HttpResponse(json.dumps(dic_all_holds),
                            content_type="application/json")



"""
건내받은 Butler Command를 변수에 할당
"""
def set_butler_command(request):
    if request.method == 'POST':
        command = str(request.POST.get('command')).strip()

        print("Butler Command: " + str(command))

        global butler_command

        butler_command = command

        print("Set Butler Command: " + str(butler_command))

        return HttpResponse(json.dumps("Success"),
                            content_type="application/json")


def get_weather_data_for_UI(request):
    if request.method == 'POST':
        dic_all_holds = {}

        parsed_weather = get_weather_data()

        print(json.dumps(parsed_weather))

        cloud_state = parsed_weather["SKY"]
        # 강수 확률
        rain_prob = parsed_weather["POP"]
        # 습도
        humidity_state = parsed_weather["REH"]
        # 온도
        temperature_state = parsed_weather["T3H"]
        # 강수 형태
        rain_state = parsed_weather["PTY"]

        if cloud_state == 1:
            cloud_state = "맑음"
        elif cloud_state == 2:
            cloud_state = "구름 조금"
        elif cloud_state == 3:
            cloud_state = "구름 많음"
        elif cloud_state == 4:
            cloud_state = "흐림"

        if rain_state == 0:
            rain_state = "없음"
        elif rain_state == 1:
            rain_state = "비"
        elif rain_state == 2:
            rain_state = "진눈개비"
        elif rain_state == 3:
            rain_state = "눈"

        dic_all_holds["Cloud"] = [cloud_state]
        dic_all_holds["RainProb"] = [rain_prob]
        dic_all_holds["Humidity"] = [humidity_state]
        dic_all_holds["Temperature"] = [temperature_state]
        dic_all_holds["Rain"] = [rain_state]

        return HttpResponse(json.dumps(dic_all_holds),
                            content_type="application/json")


def get_input(request):
    if request.method == 'POST':
        # print("Get Input Request!!")
        dic_all_holds = {}

        # dic_all_holds["Input"] = butler_command

        global butler_command

        print("Butler Input from Server: " + str(butler_command))

        dic_all_holds["Input"] = [butler_command]

        return HttpResponse(json.dumps(dic_all_holds),
                            content_type="application/json")

# @jaeseung : API 작성 필요 openhap으로 부터 받은 파일을 device_info.json으로 저장
# 바른 기술과 통신하기 위해 필요한 모듈
def init_server(request):
    if request.method == 'POST':
        global port
        global address

        # Set host
        server_address = (address, port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print("Get Host Name: " + socket.gethostname())

        sock.bind(server_address)
        sock.listen(5)

        print("TCP Server is waiting for client on port " + str(port))

        while True:
            # wait to accept a connection - blocking call
            conn, addr = sock.accept()

            conn.settimeout(2.0)
            print("Connected with " + addr[0] + ":" + str(addr[1]))

            rbuff = b""

            while True:
                try:
                    print("Before Receive")
                    ret = conn.recv(1024)
                    print("After Receive: " + str(ret))

                    if not ret:
                        print("Break!")
                        break

                    rbuff += ret
                    print(str(len(rbuff)))
                except Exception as e:
                    print(str(e))
                    break

            jdata = json.loads(rbuff.decode('euc-kr'))

            if str(rbuff) == 'Q' or str(rbuff) == 'q':
                conn.send(bytes("Quit", 'utf-8'))
                conn.close()
                break

            # 바른기술측에서 넘어온 Device 정보들을 받아서 Parsing한 후, File로 쓸까..?
            else:
                conn.send(rbuff + bytes(" Received", 'utf-8'))

                dir_json = os.path.join(BASE_DIR, "jsonSet/" + 'device_info_RAW.json')
                with open(dir_json, 'w') as outfile:
                    json.dump(jdata, outfile, ensure_ascii=False)
                # butler_command = data
                # print("Saved Data: " + butler_command)
                device_json = convert_device_json_given_by_OPENHAB(jdata)

                # 받아온 정보들을 파일로 씀
                dir_json = os.path.join(BASE_DIR, "jsonSet/" + 'device_info.json')
                with open(dir_json, 'w') as outfile:
                    json.dump(device_json, outfile, ensure_ascii=False)

                conn.close()

        return HttpResponse(json.dumps("Success"),
                            content_type="application/json")


# 바른 기술과 통신하기 위해 필요한 모듈
def get_reasoning_input(request):
    if request.method == 'POST':
        connect_address = ('address', 2222)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 우리가 만든 서버에 접속해서, 바른기술에서 넘어온 Input Data를 받아옴
        client.connect(connect_address)

        # 우리가 만든 서버에 특정 keyword로 통신을 시도하면,
        # 바른기술에서 넘어온 Input 데이터를 Response 해주는 방식으로
        # client.send(json.dumps(devices_info_json).encode('utf-8'))
        print("After Sending JSON")

        response = client.recv(4096).decode()
        print("Response: ", response)

        client.close()

        return HttpResponse(json.dumps(response),
                            content_type="application/json")

def set_context(request):
    if request.method == 'POST':
        # engine = connect_jess_engine(20000)

        month = request.POST.get('month')
        hour = request.POST.get('hour')
        minute = request.POST.get('minute')
        season = ""

        month = int(month)

        if month >= 4 and 5 >= month:
            season = "봄"
        elif month >= 6 and 9 >= month:
            season = "여름"
        elif month == 10:
            season = "가을"
        elif month >= 11 and 3 >= month:
            season = "겨울"

        # engine.resultOfCommand("(assert (price waffles " + str(price) + "))")

        return HttpResponse(json.dumps("success"),
                            content_type="application/json")


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

def fire_rule(request):
    print("test")
    if request.method == 'POST':
        print("good")
        # JESS Engine에 연결한 후, 웹 상에서 넘어온 정보들을 Parsing
        engine = connect_jess_engine(21000)
        results = engine.run_engine()
        # print(results)
        response_df = parse_results(results)
        # results_line = results.split("\n")
        # for i in results_line:
        #     if "DEBUG" in i:
        #         print(i)
        global num_stamp
        print(response_df.iloc[[num_stamp]])
        # print("aaaaaa",response_df.iloc[[num_stamp]][0])
        # print("aaaaaa", response_df.iloc[[num_stamp]][1])
        # print("aaaaaa", response_df.iloc[[num_stamp]][2])
        num_stamp += 1
        ############################# minsung : need to call
        result = response_df.iloc[num_stamp].to_json(orient="records")
        print(response_df.iloc[num_stamp].to_json(orient="records"))
        return HttpResponse(result,
                            content_type="application/json")

def parse_results(results):
    results_line = results.split("\n")
    time_list = []
    data_list = []
    value_list =[]
    for i in results_line:
        time_list.append(i[:16])
        data_list.append(i[24:])

    # for i, j in zip(time_list, data_list):
    #     print("time : ", i)
    #     print("data : ", j)
    for d in data_list[:-1]:
        tmp_list =[]
        for i,c in enumerate(d):
            if "="==c:
                tmp_list.append(d[i+1])
        value_list.append(tmp_list)

    header = ["PrepareMeal", "Meal", "Refreshment", "WatchingTV", "CommunicationWithPerson", "Communication", "Reading", "Cleaning", "ArrangeThing", "Smoking", "HealthCare", "Drink", "Clothing"]
    df = pd.DataFrame(value_list, columns=header)
    df.pop('PrepareMeal')
    df.pop('Refreshment')
    df.pop('Smoking')
    print(df.head())
    return df




'''
JESS Engine에서 받아온 결과가 Home Device 제어일 경우, 
바른기술 측에서 받은 json 파일을 추론된 결과에 맞게 수정하는 함수

Return:
    device_info.json 파일의 내용
'''

# @jaeseung : FACT을 JSON형태로 변환
def convert_device_state_in_json(jess_results):
    dir_json = os.path.join(BASE_DIR, "jsonSet/" + "device_info.json")

    with codecs.open(dir_json, 'r', 'utf-8') as json_data:
        # 디바이스 정보들을 json으로 받아옴
        devices = json.load(json_data)
        response = ""

        # JESS에서 넘어온 Device 정보들을 Parsing
        for i in range(0, len(jess_results)):
            # 하나의 Jess Result를 받아옴
            # ID State: state 로 되어있어서, 공백으로 Split하여 Device id와 State를 구분해야함
            # print("Before Split: " + str(jess_results[i]))

            # 비어있지 않은 경우에만
            if str(jess_results[i]).strip() != "":

                jess_result = str(jess_results[i]).strip().split(" ")

                device = str(jess_result[0]).strip().replace("_", " ")
                device_state = jess_result[2]

                # print("Device: " + str(device))
                # print("Device State: " + str(device_state))

                json_devices = {}

                if "스마트플러그" in jess_result[1]:
                    print("스마트플러그-")
                    continue

                if "Lamp" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        color_states = json_device["color"].split(",")
                        json_device["color"] = color_states[0] + "," + color_states[1] + "," + device_state

                elif "공기청정기" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        if device_state == "예약모드":
                            json_device["power"] = "OFF"
                        else:
                            json_device["power"] = device_state

                elif "로봇청소기" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        if device_state == "예약모드":
                            json_device["control"] = "dock"
                        else:
                            json_device["control"] = device_state

                elif "보일러" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        if device_state == "겨울설정온도":
                            print("보일러 겨울설정온도")
                            json_device["setpoint"] = "26.0"
                        elif device_state == "OFF":
                            print("보일러 OFF")
                            json_device["setpoint"] = "9.0"
                        else:
                            json_device["setpoint"] = device_state

                elif "WeMo" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        json_device["state"] = device_state

                elif "샤오미 스마트" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        json_device["power"] = device_state

                elif "TV" in device:
                    json_devices = devices["Device"][device]

                    # 모든 디바이스에 대한 State를 JESS에서 온 Output으로 대체
                    for json_device in json_devices:
                        json_device["buttonPress"] = device_state

    print("Converting End")
    print(json.dumps(devices))

    # 파일 내부의 내용들을 바꿈
    return devices


'''
{
"Value": []
"Item": []
}
형태로 변환해줘서 서버쪽에 전송해야 함
'''

# @jaeseung : FACT->JSON-> OPENHAP에서 쓰는 형태의 JSON으로 변경
def convert_json_to_send_format(devices, command):
    result = {"Value": [], "Item": []}

    json_keys = devices["Device"].keys()

    for json_key in json_keys:

        # []로 감싸져있기 때문에 for문을 한번더 돔
        for device in devices["Device"][json_key]:
            # Hue 전구인 경우
            if command == "외출모드":
                if "Hue" in json_key:
                    result["Value"].append(device["color"])
                    result["Item"].append(device["colorItem"])
                elif "공기청정기" in json_key:
                    result["Value"].append(device["power"])
                    result["Item"].append(device["powerItem"])
                elif "로봇청소기" in json_key:
                    result["Value"].append(device["control"])
                    result["Item"].append(device["controlItem"])
                elif "WeMo" in json_key:
                    result["Value"].append(device["state"])
                    result["Item"].append(device["stateItem"])
                elif "샤오미 스마트" in json_key:
                    result["Value"].append(device["power"])
                    result["Item"].append(device["powerItem"])
                elif "보일러" in json_key:
                    result["Value"].append(device["setpoint"])
                    result["Item"].append(device["setpointItem"])
                elif "TV" in json_key:
                    result["Value"].append(device["buttonPress"])
                    result["Item"].append(device["buttonPressItem"])

            elif command == "귀가전날":
                if "공기청정기" in json_key:
                    result["Value"].append(device["power"])
                    result["Item"].append(device["powerItem"])
                elif "로봇청소기" in json_key:
                    result["Value"].append(device["control"])
                    result["Item"].append(device["controlItem"])

            elif command == "방범모드" or command == "방범모드종료":
                if "Hue" in json_key:
                    result["Value"].append(device["color"])
                    result["Item"].append(device["colorItem"])
                elif "TV" in json_key:
                    print("방범모드 TV: " + str(device["buttonPress"]))
                    result["Value"].append(device["buttonPress"])
                    result["Item"].append(device["buttonPressItem"])

            elif command == "귀가당일":
                if "Hue" in json_key:
                    result["Value"].append(device["color"])
                    result["Item"].append(device["colorItem"])
                elif "공기청정기" in json_key:
                    result["Value"].append(device["power"])
                    result["Item"].append(device["powerItem"])
                elif "로봇청소기" in json_key:
                    result["Value"].append(device["control"])
                    result["Item"].append(device["controlItem"])
                elif "WeMo" in json_key:
                    result["Value"].append(device["state"])
                    result["Item"].append(device["stateItem"])
                elif "샤오미 스마트" in json_key:
                    result["Value"].append(device["power"])
                    result["Item"].append(device["powerItem"])
                elif "보일러" in json_key:
                    result["Value"].append(device["setpoint"])
                    result["Item"].append(device["setpointItem"])



    return result


'''
JESS에서 추론된 결과로 바뀐 Device JSON 파일을
바른 기술측으로 보내는 함수
'''


def send_device_json_to_server(device_json):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("192.168.1.52", 25001))

    print("Sending Contents", json.dumps(device_json))

    client.send(json.dumps(device_json).encode('utf-8'))
    print("After Sending JSON")

    # response = client.recv(4096).decode()
    # print("Response: ", response)

    client.close()


'''
바른 기술측에서 받은 Device 정보들을 
JESS Fact로 바꿀 수 있는 json 형태로 변환해주는 함수
'''


def convert_device_json_given_by_OPENHAB(device_json):
    device = {"Device": {}}

    # List형태의 JSON을 하나씩 추출
    for i in range(0, len(device_json)):
        device_flag = False

        # Item: Value 형태의 Dictionary로 저장하기 위해
        device_properties_values = {}

        device_information = device_json[i]

        device_name = device_information["DeviceName"]
        device_items = device_information["Item"]
        device_values = device_information["Value"]

        # Item 목록 안에서 제일 뒤의 Property만 떼어내야 함
        for j in range(0, len(device_items)):
            # print("Before Split: " + str(device_items[j]))

            if str(device_items[j]).strip() != "":
                # Item들은 _ 로 구분
                # 제일 마지막 부분의 글자를 Split해서 Key로 사용
                device_item = str(device_items[j]).strip().split("_")
                # Get last one
                device_properties_values[device_item[-1]] = device_values[j]
                device_properties_values[device_item[-1] + "Item"] = device_items[j]

        # print(json.dumps(device_properties_values))
        # 위 추출한 정보들을 재조합해서
        # JESS Fact로 Converting 될 수 있는 json 형태로 바꿔야 함

        # Get Keys
        device_keys = device["Device"].keys()

        # Key Check
        for key in device_keys:
            # print(str(key))
            if key == device_name:
                device_flag = True
                break

        # 해당 Key가 있으면 Append 해주고 아닐 경우에는 Assign
        if device_flag:
            device["Device"][device_name] += [device_properties_values]
        else:
            device["Device"][device_name] = [device_properties_values]

    return device


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
    시스템에서 받아온 시간정보(시, 분, 월, 일)들을 바탕으로 
    계절, 아침/점심/저녁, 주중/주말 로 Parsing하여 Return하는 함수

Input:
    hour: 시간
    minute: 분
    month: 월
    day: 일
Return:
    계절, 아침/점심/저녁, 주중/주말
'''
def parse_time_information(hour, minute, month, day):
    hour = int(hour)
    # minute = int(minute)
    month = int(month)
    day = int(day)

    season = ""
    time = ""
    date = ""

    if 4 <= month <= 5:
        season = "봄"
    elif 6 <= month <= 9:
        season = "여름"
    elif month == 10:
        season = "가을"
    else:
        season = "겨울"

    if 0 <= hour <= 10:
        time = "아침"
    elif 11 <= hour <= 15:
        time = "점심"
    elif 16 <= hour <= 24:
        time = "저녁"

    if day <= 5:
        date = "주중"
    elif day >= 6:
        date = "주말"

    return season, time, date


'''
Function Definition: 
    현재 시각을 바탕으로 얻어진 정보들 (계절, 월, 아침/점심/저녁, 주중/주말)을 
    JESS Engine의 Fact 형태로 Parsing 하여 Assert 해주는 함수

Input:
    season: 계절
    month: 월
    time: 아침/점심/저녁
    date: 주중/주말
    engine: JESS Engine의 주소를 담고 있는 변수

Return:

'''
def assert_temporal_to_fact(season, month, time, date, engine):
    # season: 계절
    # month: 월
    # time: 아침/점심/저녁
    # date: 주중/주말

    fact = "(assert (temporalContext (month " + month + ")(date " + date + ")(time " + time + ")(season " + season + ")))"
    print("Temporal Fact: " + fact)

    engine.resultOfCommand(fact)


'''
Function Definition: 
    JSON file 이름에 따라서 안의 내용들을 프로그램에 필요한
    JESS Engine의 Fact 형태로 파싱해주는 함수.

Input:
    json_file: JSON File의 이름

Return:
    JESS Engine Fact들을 저장하고 있는 Array
'''
# @jaeseung : device_info.json을 읽어서 추론에 필요한 속성들을 빼서 FACT로 변경
def parse_json_to_fact(json_file):
    facts = []

    # 선호음식 JSON 읽어서 Fact로 파싱
    if json_file == "preferred_food.json":
        preferred_menus_with_time = read_json(json_file)
        time_scopes = preferred_menus_with_time["선호음식"].keys()

        for time_scope in time_scopes:
            # date_time = [0]: 주중/주말 [1]: 아침/점심/저녁
            date_time = time_scope.split(" ")
            print("Time Scope: " + str(time_scope))
            preferred_menus = preferred_menus_with_time["선호음식"][time_scope]

            for preferred_menu in preferred_menus:
                unused = "x"
                fact = "(assert (preferred_food (food_name " + preferred_menu + ")(date " + date_time[
                    0] + ")(meal_type " + date_time[1] + ")(used " + unused + ")))"
                facts.append(fact)

    # 음식에 필요한 재료 JSON 읽어서 Fact로 파싱
    elif json_file == "menu_ingredient.json":
        menu_ingredients_with_name = read_json(json_file)

        menu_names = menu_ingredients_with_name.keys()

        for menu_name in menu_names:
            menu_ingredients = menu_ingredients_with_name[menu_name]

            for menu_ingredient in menu_ingredients:
                fact = "(assert (recipe_ingred (food_name " + menu_name + ") (ingred " + menu_ingredient + ")))"
                facts.append(fact)

    # 냉장고에 있는 재료 JSON 읽어서 Fact로 파싱
    elif json_file == "fridge_ingredient.json":
        fridge_ingredients = read_json(json_file)
        fridge_ingredients = fridge_ingredients["냉장고"]

        for fridge_ingredient in fridge_ingredients:
            fact = "(assert (stored_ingred (fridge 냉장고) (ingred " + fridge_ingredient + ")))"
            facts.append(fact)

    elif json_file == "device_info.json":
        # @jaeseung : 추론된 결과를 받아서 다시 추가정보를 달아줄때 ID 사용
        device_info = read_json(json_file)
        # "Device" Key안에 여러 Device들이 존재하고 있음
        device_info_with_keys = device_info["Device"]

        device_keys = device_info_with_keys.keys()

        # Hue Lamp, ...
        for device_key in device_keys:
            device_info = device_info_with_keys[device_key]

            dev_id = ""
            dev_state = ""

            # Hue라는 단어가 Device Key에 존재하는 경우
            if "Hue" in device_key:
                # 하나의 Device (Hue 전구 내에서도 하나)
                # []로 묶여 있어서 for문으로 풀어줘야함
                for single_device_info in device_info:
                    dev_id = single_device_info["colorItem"]
                    dev_state = single_device_info["color"]

            elif "공기청정기" in device_key:
                for single_device_info in device_info:
                    dev_id = single_device_info["powerItem"]
                    dev_state = single_device_info["power"]

            elif "로봇청소기" in device_key:
                for single_device_info in device_info:
                    dev_id = single_device_info["controlItem"]
                    dev_state = single_device_info["control"]

            elif "WeMo" in device_key:
                for single_device_info in device_info:
                    dev_id = single_device_info["stateItem"]
                    dev_state = single_device_info["state"]

            elif "샤오미 스마트" in device_key:
                for single_device_info in device_info:
                    dev_id = single_device_info["powerItem"]
                    dev_state = single_device_info["power"]

            elif "보일러" in device_key:
                for single_device_info in device_info:
                    dev_id = single_device_info["setpointItem"]
                    dev_state = single_device_info["setpoint"]

            elif "TV" in device_key:
                for single_device_info in device_info:
                    dev_id = single_device_info["buttonPressItem"]
                    dev_state = single_device_info["buttonPress"]
            else:
                continue

            # Device Key의 빈칸을 모두 _로 Replace
            device_key = str(device_key).strip().replace(" ", "_")

            print("Device Key: " + str(device_key))

            fact = "(assert (home_device (device_name " + device_key + ")(device_id " + dev_id + ")(device_state " + dev_state + ")))"
            facts.append(fact)

    elif json_file == "smartplug_device.json":
        smart_plug_device_info = read_json(json_file)
        smart_plug_device_info_with_keys = smart_plug_device_info["SmartPlug"]

        smart_plug_device_keys = smart_plug_device_info_with_keys.keys()

        dev_name = ""
        dev_state = ""

        for smart_plug_device_key in smart_plug_device_keys:
            dev_name = smart_plug_device_info_with_keys[smart_plug_device_key]["Device"]
            dev_state = smart_plug_device_info_with_keys[smart_plug_device_key]["DevState"]

            fact = "(assert (smart_plug_device (connected_device_name " + dev_name + ")(smart_plug_state " + dev_state + ")))"
            facts.append(fact)

    elif json_file == "forget_device.json":
        forget_devices = read_json(json_file)
        forget_devices = forget_devices["Forget"]

        for forget_device in forget_devices:
            fact = "(assert (forget_device (device_name " + forget_device + ")))"
            facts.append(fact)

    return facts


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


'''
Function Definition: 
    JESS Engine과 Fact 형태의 String들을 입력으로 받아서 
    JESS Engine의 Fact로 직접 Assert 해주는 함수

Input:
    - facts: Fact 형태의 String
    - engine: JESS Engine의 주소를 가지고 있는 변수

Return:

'''
def assert_facts_in_jess(facts, engine):
    for fact in facts:
        print("Fact: " + fact)
        engine.resultOfCommand(fact)


'''
Function Definition: 
    기상청에서 허가 받은 Key를 통해 현재 시각으로부터 
    3일 후의 기상 정보까지 받아오는 함수.

    이때, 기상청에서 받아온 모든 정보들을 사용하는 것이 아닌
    프로그램에 필요한 정보들만 Parsing하여 사용.

Input:

Return:
    기상청에서 받아온 JSON 형태의 결과값을 프로그램에 필요한 부분만 Parsing한 결과
'''
def get_weather_data():
    api_date, api_time = get_api_date()
    url = "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastSpaceData?"
    # key = "serviceKey=" + "rKRmx10C9rbUwziswuR5Ny5KXjAAXS3HFJHYiAtBauc36qWFht5VGWdpnqHkm6Xww2qORmubYPkBPoahoJQC1g%3D%3D"
    key = "serviceKey=" + "BT%2FHXKHekGZxplqdwEq14edU%2F1tSrnYjzRNYrRoiLPMjog1vx4BEmhuzFBxYttUBEQXt4OzjbL45ke9%2BBo7vsQ%3D%3D"
    date = "&base_date=" + api_date
    time = "&base_time=" + api_time
    nx = "&nx=97"
    ny = "&ny=76"
    numOfRows = "&numOfRows=100"
    type = "&_type=json"
    api_url = url + key + date + time + nx + ny + numOfRows + type

    data = urllib.request.urlopen(api_url).read().decode('utf8')
    data_json = json.loads(data)

    print(data_json)

    parsed_json = data_json['response']['body']['items']['item']

    # 가장 최근 데이터를 보는 것
    target_date = parsed_json[0]['fcstDate']  # get date and time
    target_time = parsed_json[0]['fcstTime']

    date_calibrate = target_date  # date of TMX, TMN
    # 오후 1시를 넘어서 받아올 경우, 다음 날짜의 정보들을 받아오도록
    if int(target_time) > int(1300):
        date_calibrate = str(int(target_date) + 1)

    passing_data = {}
    for one_parsed in parsed_json:
        if one_parsed['fcstDate'] == target_date and one_parsed['fcstTime'] == target_time:  # get today's data
            passing_data[one_parsed['category']] = one_parsed['fcstValue']

        # TMX: 낮 최고기온, TMN: 아침 최저기온
        if one_parsed['fcstDate'] == date_calibrate and (
                one_parsed['category'] == 'TMX' or one_parsed[
            'category'] == 'TMN'):  # TMX, TMN at calibrated day
            passing_data[one_parsed['category']] = one_parsed['fcstValue']

    return passing_data


'''
Function Definition: 
    현재 시각을 바탕으로 기상청으로부터 기상정보를 얻어올 시작 시간을 설정하는 함수

Input:

Return:
    기상청에서 기상정보를 받아오기 위한 입력 정보
'''
def get_api_date():
    standard_time = [2, 5, 8, 11, 14, 17, 20, 23]  # api response time
    time_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%H')  # get hour
    # print("Time Now: " + time_now)
    # check_time = int(time_now) - 1
    # print("Check Time: " + str(check_time))
    check_time = int(time_now)
    day_calibrate = 0

    # hour to api time
    while not check_time in standard_time:
        check_time -= 1
        if check_time < 2:
            day_calibrate = 1  # yesterday
            check_time = 23

    date_now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul')).strftime('%Y%m%d')  # get date
    check_date = int(date_now) - day_calibrate

    print("Check Date: " + str(check_date) + str(check_time) + '00')

    if check_time < 10:
        return (str(check_date), ('0' + str(check_time) + '00'))
    else:
        return (str(check_date), (str(check_time) + '00'))  # return date(yyyymmdd), tt00


def check_question_in_result(results):
    for result in results:
        if "?" in str(result).strip():
            return True

    return False


def check_menu_json_in_result(results):
    for result in results:
        if "menu_recipe.json" in str(result).strip():
            return True

    return False


def get_menu_json_index(results):
    for i in range(0, len(results)):
        if "menu_recipe.json" in str(results[i]).strip():
            return i

    return -1


def get_question_index(results):
    for i in range(0, len(results)):
        if "?" in str(results[i]).strip():
            return i

    return -1


'''
Function Definition: 
    프로그램에서 필요한 정보만을 Parsing한 기상청 정보에서
    강수확률에 대한 정보를 얻어오기 위한 함수

Input:
    parsed_weather: Parsing된 Dictionary 형태의 기상정보들

Return:
    JESS Fact 형태의 강수확률에 대한 정보
'''
def parse_weather_to_fact(parsed_weather):
    rain_probability = parsed_weather['POP']
    cloud_state = parsed_weather['SKY']
    print("Cloud: " + str(cloud_state))

    facts = []
    if int(rain_probability) >= 50:
        fact = "(assert (weatherContext (weather 비)"
        # facts.append(fact)
    else:
        fact = "(assert (weatherContext (weather 비안옴)"
        # facts.append(fact)

    if cloud_state == 1:
        fact += "(cloud 맑음)))"

    elif cloud_state == 2:
        fact += "(cloud 구름조금)))"

    elif cloud_state == 3:
        fact += "(cloud 구름많음)))"

    elif cloud_state == 4:
        fact += "(cloud 흐림)))"

    facts.append(fact)

    return facts




################  @minsung ########################

''' @minsung & @jaeseung 
Function Definition: 
    프로그램에서 필요한 정보만을 Parsing한 기상청 정보에서
    강수확률에 대한 정보를 얻어오기 위한 함수

Input:
    parsed_weather: Parsing된 Dictionary 형태의 기상정보들

Return:
    JESS Fact 형태의 강수확률에 대한 정보
'''
def LoadData(request): #민성 load data 버튼 누를시 ajax
    print("def LoadData success")
    if request.method == 'POST':
        print("def LoadData POST success")
        sel1 = request.POST.get('sel1')
        sel2 = request.POST.get('sel2')
        sel3 = request.POST.get('sel3')
        msg = sel1 + sel2 + sel3
        print("msg: ",msg)
        if 'select' not in msg:
            print("good!")
            file_list = []
            df_list = []
            count = 0
            header_name = ["Time", "UID", "Device", "Prob", "Season", "Week", "Weather"]
            header_name2 = ["#", "Time", "UID", "Device", "Prob", "Season", "Week", "Weather"]
            root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")
            device_list = ['airconditioner', 'aircleaner', 'bulb', 'robotcleaner', 'tv']

            device_dir = []
            for i in device_list:
                device_dir.append(root_dir + "/" + sel1 + "/" + sel2 + "/" + sel3 + "/" + i.lower())

            dev1_tmp_list = []
            dev2_tmp_list = []
            dev3_tmp_list = []
            dev4_tmp_list = []
            dev5_tmp_list = []
            dev_tmp_list = [dev1_tmp_list, dev2_tmp_list, dev3_tmp_list, dev4_tmp_list, dev5_tmp_list]

            dev1_df = []
            dev2_df = []
            dev3_df = []
            dev4_df = []
            dev5_df = []
            dev_df = [dev1_df, dev2_df, dev3_df, dev4_df, dev5_df]

            print(device_dir)

            for i,j in zip(device_dir, dev_tmp_list):
                search_dir(i, j)

            header_list = ["Time", "Min", "User", "Device", "N_Com", "Prob", "On/Off", "Season", "Week", "Weather"]
            header_list2 = ["Time", "Min", "User", "Device", "N_Com", "Temp", "On/Off", "Season", "Week", "Weather"]
            header_list3 = ["Time", "Min", "User", "Device", "N_Com", "Dust", "On/Off", "Season", "Week", "Weather"]
            df_tmp_cnt = 0
            for i in dev_tmp_list:
                #print(i)
                for j in i:
                    #print(j)
                    if (df_tmp_cnt == 0):
                        dev_df[df_tmp_cnt].append(
                            pd.read_csv(j, delimiter='\t', header=None, names=header_list2, index_col=None, encoding='CP949',
                                        engine="python").drop(["Min","N_Com"],axis=1))
                    elif (df_tmp_cnt == 1):
                        dev_df[df_tmp_cnt].append(
                            pd.read_csv(j, delimiter='\t', header=None, names=header_list3, index_col=None, encoding='CP949',
                                        engine="python").drop(["Min","N_Com"],axis=1))
                    else:
                        dev_df[df_tmp_cnt].append(
                            pd.read_csv(j, delimiter='\t', header=None, names=header_list, index_col=None, encoding='CP949',
                                        engine="python").drop(["Min","N_Com"],axis=1))
                df_tmp_cnt += 1

            final_dev_df = []
            for i in dev_df:
                final_dev_df.append(i[0].to_html(classes='table table-bordered table-fixed'))

            response = HttpResponse(final_dev_df, content_type='text/html')
            print(response)
            return response


#learned 코드 시작
def load_file(path):
    data = []
    f = open(path, 'r', encoding='utf-8')
    rdr = csv.reader(f)

    for line in rdr:
        data.append(float(line[0]))

    return data

def fit_gmm(data, n_com):
    # Fit GMM
    gmm = GaussianMixture(n_components=n_com, covariance_type="diag", tol=0.001)
    gmm = gmm.fit(X=np.expand_dims(data, 1))

    return gmm


def RunProfileLearner(request):  # 민성 RunProfileLearner 버튼 누를시 ajax
    print("def RunProfileLearner success")
    if request.method == 'POST':
        print("def RunProfileLearner POST success")
        sel1 = request.POST.get('sel1')
        sel2 = request.POST.get('sel2')
        sel3 = request.POST.get('sel3')
        msg = sel1 + sel2 + sel3
        print("msg: ", msg)

        if 'select' not in msg:
            # Python Code Start
            ######################################################################################################
            root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")
            device_list = ['airconditioner', 'aircleaner', 'bulb', 'robotcleaner', 'tv']

            device_dir = []
            print("1")
            for i in device_list:
                device_dir.append(root_dir + "/" + sel1 + "/" + sel2 + "/" + sel3 + "/" + i.lower())

            dev1_tmp_list = []
            dev2_tmp_list = []
            dev3_tmp_list = []
            dev4_tmp_list = []
            dev5_tmp_list = []
            dev_tmp_list = [dev1_tmp_list, dev2_tmp_list, dev3_tmp_list, dev4_tmp_list, dev5_tmp_list]

            dev1_df = []
            dev2_df = []
            dev3_df = []
            dev4_df = []
            dev5_df = []
            dev_df = [dev1_df, dev2_df, dev3_df, dev4_df, dev5_df]
            print("2")

            print(device_dir)

            for i, j in zip(device_dir, dev_tmp_list):
                search_dir(i, j)

            header_list = ["Time", "Min", "User", "Device", "N_Com", "Prob", "On", "Season", "Week", "Weather"]
            print("3")
            df_tmp_cnt = 0
            for i in dev_tmp_list:
                for j in i:
                    dev_df[df_tmp_cnt].append(
                        pd.read_csv(j, delimiter='\t', header=None, names=header_list, index_col=None, encoding='CP949',
                                    engine="python"))
                df_tmp_cnt += 1

            dev_graph1_df = []
            ###### 여기에 on인 시간만 담김
            train_data = []
            thres_data = []
            n_com = []
            for i in dev_df:
                first = 0
                tmp_data = []
                tmp_min_check = []
                for j in i:
                    if first == 0:
                        first_df = j.drop(["Min", "User", "Device", "N_Com", "On", "Season", "Week", "Weather"], axis=1)
                        dev_graph1_df.append(first_df)
                        n_com.append(j['N_Com'][0])
                        first = 1

                    # @jaeseung : need to get on time
                    for index, row in j.iterrows():
                        if row["On"] == "On":
                            tmp_data.append(row["Min"])
                            tmp_min_check.append(row["Prob"])

                train_data.append(tmp_data)
                thres_data.append(tmp_min_check)

            ######################################################################################################################
            model_list = []
            # Time, Prob
            learned_df = []
            print("min make")
            # print(dev_graph1_df[0]["Time"].tolist()[-1])
            day_start = "0:00"
            day_s = datetime.datetime.strptime(day_start, '%H:%M')
            s = datetime.datetime.strptime(dev_graph1_df[0]["Time"].tolist()[0], '%H:%M')
            e = datetime.datetime.strptime(dev_graph1_df[0]["Time"].tolist()[-1], '%H:%M')
            e += datetime.timedelta(minutes=1)

            time = []
            min_list = []
            while s < e:
                time.append(s)
                min_list.append((s - day_s).seconds / 60)
                s += datetime.timedelta(minutes=1)

            print("train data len : ", len(train_data))
            for i, j in zip(train_data, n_com):
                print(len(i))
                model = fit_gmm(i, j)
                model_list.append(model)

                print('weight:', model.weights_)
                print('mean:', model.means_)
                print('cov:', np.sqrt(model.covariances_))
                # @jaeseung : need to calculate gaussian

                tmp_prob = calculate_gaussian(min_list, model.weights_, model.means_, np.sqrt(model.covariances_))
                #print(len(tmp_prob))
                #print(type(tmp_prob))

                tmp_df = pd.DataFrame(dev_graph1_df[0]["Time"]).join(pd.DataFrame(tmp_prob, columns=["Prob"]))
                #print(tmp_df)
                learned_df.append(tmp_df)


            #need fix
            # print('mean:', model.means_ / 60, ":", model.means_ % 60)
            # print('cov:', np.sqrt(model.covariances_) / 60, ":", np.sqrt(model.covariances_) % 60)

            # Python Code End
            file_name = root_dir + sel1.lower() + "/" + sel2.lower() + "/" + sel3.lower() + "/" + "context_threshold.csv"
            header_list = ["Temp_Min", "Temp_Max", "Temp_Thres", "Dust_Min", "Dust_Max", "Dust_Thres"]
            step_df = pd.read_csv(file_name, delimiter='\t', header=None, names=header_list, index_col=None,
                                  encoding='CP949', engine="python")

            temp_header = [['On/Off', 'Generated', 'Learned']]
            # print("##################################### TEMP DF CHECK")
            # print(step_df["Temp_Min"][0], step_df["Temp_Max"][0], step_df["Temp_Thres"][0])
            # print(type(step_df["Temp_Thres"][0]))
            temp_x = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
            temp_y = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
            temp_y[temp_x <= int(step_df["Temp_Thres"][0])] = 0
            temp_y[temp_x > int(step_df["Temp_Thres"][0])] = 1
            temp_y2 = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
            temp_y2[temp_x <= min(thres_data[0])] = 0
            temp_y2[temp_x > min(thres_data[0])] = 1
            print(min(thres_data[0]))
            print(temp_y2)
            temp_list = np.c_[temp_x, temp_y]
            temp_list = np.c_[temp_list, temp_y2]
            temp_list = temp_list.tolist()
            temp_df = temp_header + temp_list

            dust_header = [['On/Off', 'Generated', 'Learned']]  # AirCleaner Draw
            dust_x = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
            dust_y = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
            dust_y[dust_x <= int(step_df["Dust_Thres"][0])] = 0
            dust_y[dust_x > int(step_df["Dust_Thres"][0])] = 1
            dust_y2 = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
            dust_y2[dust_x <= min(thres_data[1])] = 0
            dust_y2[dust_x > min(thres_data[1])] = 1
            print(min(thres_data[1]))
            dust_list = np.c_[dust_x, dust_y]
            dust_list = np.c_[dust_list, dust_y2]
            dust_list = dust_list.tolist()
            dust_df = dust_header + dust_list

            data3 = [['x', 'Generated','Learned']]  # Bulb Draw
            x3 = dev_graph1_df[2]["Time"].tolist()
            generated3 = dev_graph1_df[2]["Prob"].tolist()
            learned3 = learned_df[2]["Prob"].tolist()
            for i in range(len(x3)):
                tmp_list = []
                tmp_list.append(x3[i])
                tmp_list.append(generated3[i])
                tmp_list.append(learned3[i])
                data3.append(tmp_list)

            data4 = [['x', 'Generated','Learned']]  # RobotCleaner Draw
            x4 = dev_graph1_df[3]["Time"].tolist()
            generated4 = dev_graph1_df[3]["Prob"].tolist()
            learned4 = learned_df[3]["Prob"].tolist()
            for i in range(len(x4)):
                tmp_list = []
                tmp_list.append(x4[i])
                tmp_list.append(generated4[i])
                tmp_list.append(learned4[i])
                data4.append(tmp_list)

            data5 = [['x', 'Generated','Learned']]  # TV Draw
            x5 = dev_graph1_df[4]["Time"].tolist()
            generated5 = dev_graph1_df[4]["Prob"].tolist()
            learned5 = learned_df[4]["Prob"].tolist()
            for i in range(len(x5)):
                tmp_list = []
                tmp_list.append(x5[i])
                tmp_list.append(generated5[i])
                tmp_list.append(learned5[i])
                data5.append(tmp_list)

            DrawData = [temp_df,dust_df,data3,data4,data5]
            for i in DrawData:
                print(i)
            return HttpResponse(json.dumps(DrawData), content_type="application/json")


def draw_generate(user, season, week):  # 민성 generator_layout Generate 버튼 누를시 ajax
    print("def RunProfileLearner success")

    # Python Code Start
    ######################################################################################################
    root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")
    device_list = ['airconditioner', 'aircleaner', 'bulb', 'robotcleaner', 'tv']

    device_dir = []
    print("1")
    for i in device_list:
        device_dir.append(root_dir + "/" + user + "/" + season + "/" + week + "/" + i.lower())

    dev1_tmp_list = []
    dev2_tmp_list = []
    dev3_tmp_list = []
    dev4_tmp_list = []
    dev5_tmp_list = []
    dev_tmp_list = [dev1_tmp_list, dev2_tmp_list, dev3_tmp_list, dev4_tmp_list, dev5_tmp_list]

    dev1_df = []
    dev2_df = []
    dev3_df = []
    dev4_df = []
    dev5_df = []
    dev_df = [dev1_df, dev2_df, dev3_df, dev4_df, dev5_df]
    print("2")

    print(device_dir)

    for i, j in zip(device_dir, dev_tmp_list):
        search_dir(i, j)

    header_list = ["Time", "Min", "User", "Device", "N_Com", "Prob", "On", "Season", "Week", "Weather"]
    print("3")
    df_tmp_cnt = 0
    for i in dev_tmp_list:
        for j in i:
            dev_df[df_tmp_cnt].append(
                pd.read_csv(j, delimiter='\t', header=None, names=header_list, index_col=None, encoding='CP949',
                            engine="python"))
        df_tmp_cnt += 1

    dev_graph1_df = []
    ###### 여기에 on인 시간만 담김
    train_data = []
    n_com = []
    for i in dev_df:
        first = 0
        tmp_data = []
        for j in i:
            if first == 0:
                first_df = j.drop(["Min", "User", "Device", "N_Com", "On", "Season", "Week", "Weather"], axis=1)
                dev_graph1_df.append(first_df)
                n_com.append(j['N_Com'][0])
                first = 1
    ######################################################################################################################

    #need fix
    # print('mean:', model.means_ / 60, ":", model.means_ % 60)
    # print('cov:', np.sqrt(model.covariances_) / 60, ":", np.sqrt(model.covariances_) % 60)

    # Python Code End
    file_name = root_dir + user.lower() + "/" + season.lower() + "/" + week.lower() + "/" + "context_threshold.csv"
    header_list = ["Temp_Min", "Temp_Max", "Temp_Thres", "Dust_Min", "Dust_Max", "Dust_Thres"]
    step_df = pd.read_csv(file_name, delimiter='\t', header=None, names=header_list, index_col=None, encoding='CP949',engine="python")

    temp_header = [['On/Off', 'Generated']]
    print("##################################### TEMP DF CHECK")
    print(step_df["Temp_Min"][0], step_df["Temp_Max"][0], step_df["Temp_Thres"][0])
    print(type(step_df["Temp_Thres"][0]))
    temp_x = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
    temp_y = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
    temp_y[temp_x <= int(step_df["Temp_Thres"][0])] = 0
    temp_y[temp_x > int(step_df["Temp_Thres"][0])] = 1
    temp_x = temp_x.reshape(-1, temp_x.shape[0])
    temp_list = np.c_[temp_x[0], temp_y]
    temp_list = temp_list.tolist()
    temp_df = temp_header+temp_list

    dust_header =[['On/Off', 'Generated']]  # AirCleaner Draw
    dust_x = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
    dust_y = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
    dust_y[dust_x <= int(step_df["Dust_Thres"][0])] = 0
    dust_y[dust_x > int(step_df["Dust_Thres"][0])] = 1
    dust_x = dust_x.reshape(-1, dust_x.shape[0])
    dust_list = np.c_[dust_x[0], dust_y]
    dust_list = dust_list.tolist()
    dust_df = dust_header+dust_list

    data3 = [['x', 'Generated']]  # Bulb Draw
    x3 = dev_graph1_df[2]["Time"].tolist()
    generated3 = dev_graph1_df[2]["Prob"].tolist()
    for i in range(len(x3)):
        tmp_list = []
        tmp_list.append(x3[i])
        tmp_list.append(generated3[i])
        data3.append(tmp_list)

    data4 = [['x', 'Generated']]  # RobotCleaner Draw
    x4 = dev_graph1_df[3]["Time"].tolist()
    generated4 = dev_graph1_df[3]["Prob"].tolist()
    for i in range(len(x4)):
        tmp_list = []
        tmp_list.append(x4[i])
        tmp_list.append(generated4[i])
        data4.append(tmp_list)

    data5 = [['x', 'Generated']]  # TV Draw
    x5 = dev_graph1_df[4]["Time"].tolist()
    generated5 = dev_graph1_df[4]["Prob"].tolist()
    for i in range(len(x5)):
        tmp_list = []
        tmp_list.append(x5[i])
        tmp_list.append(generated5[i])
        data5.append(tmp_list)


    DrawData = [temp_df,dust_df,data3,data4,data5]
    for i in DrawData:
        print(i)
    return HttpResponse(json.dumps(DrawData), content_type="application/json")




def load_profile(request):  # 민성 RunProfileLearner 버튼 누를시 ajax
    print("def load_profile success")
    if request.method == 'POST':
        print("def load_profile POST success")
        sel1 = request.POST.get('sel1')
        sel2 = request.POST.get('sel2')
        sel3 = request.POST.get('sel3')
        msg = sel1 + sel2 + sel3
        print("msg: ", msg)

        if 'select' not in msg:
            # Python Code Start
            ######################################################################################################
            root_dir = os.path.join(BASE_DIR, "polls/static/new_data/")
            device_list = ['airconditioner', 'aircleaner', 'bulb', 'robotcleaner', 'tv']

            device_dir = []
            print("1")
            for i in device_list:
                device_dir.append(root_dir + "/" + sel1 + "/" + sel2 + "/" + sel3 + "/" + i.lower())

            dev1_tmp_list = []
            dev2_tmp_list = []
            dev3_tmp_list = []
            dev4_tmp_list = []
            dev5_tmp_list = []
            dev_tmp_list = [dev1_tmp_list, dev2_tmp_list, dev3_tmp_list, dev4_tmp_list, dev5_tmp_list]

            dev1_df = []
            dev2_df = []
            dev3_df = []
            dev4_df = []
            dev5_df = []
            dev_df = [dev1_df, dev2_df, dev3_df, dev4_df, dev5_df]
            print("2")

            print(device_dir)

            for i, j in zip(device_dir, dev_tmp_list):
                search_dir(i, j)

            header_list = ["Time", "Min", "User", "Device", "N_Com", "Prob", "On", "Season", "Week", "Weather"]
            print("3")
            df_tmp_cnt = 0
            for i in dev_tmp_list:
                for j in i:
                    dev_df[df_tmp_cnt].append(
                        pd.read_csv(j, delimiter='\t', header=None, names=header_list, index_col=None, encoding='CP949',
                                    engine="python"))
                df_tmp_cnt += 1

            dev_graph1_df = []
            ###### 여기에 on인 시간만 담김
            train_data = []
            thres_data = []
            n_com = []
            for i in dev_df:
                first = 0
                tmp_data = []
                tmp_min_check = []
                for j in i:
                    if first == 0:
                        first_df = j.drop(["Min", "User", "Device", "N_Com", "On", "Season", "Week", "Weather"], axis=1)
                        dev_graph1_df.append(first_df)
                        n_com.append(j['N_Com'][0])
                        first = 1

                    # @jaeseung : need to get on time
                    for index, row in j.iterrows():
                        if row["On"] == "On":
                            tmp_data.append(row["Min"])
                            tmp_min_check.append(row["Prob"])

                train_data.append(tmp_data)
                thres_data.append(tmp_min_check)
            ######################################################################################################################
            model_list = []
            # Time, Prob
            learned_df = []

            day_start = "0:00"
            day_s = datetime.datetime.strptime(day_start, '%H:%M')
            s = datetime.datetime.strptime(dev_graph1_df[0]["Time"].tolist()[0], '%H:%M')
            e = datetime.datetime.strptime(dev_graph1_df[0]["Time"].tolist()[-1], '%H:%M')
            e += datetime.timedelta(minutes=1)

            time = []
            min_list = []
            while s < e:
                time.append(s)
                min_list.append((s - day_s).seconds / 60)
                s += datetime.timedelta(minutes=1)

            print("train data len : ", len(train_data))
            for i, j in zip(train_data, n_com):
                print(len(i))
                model = fit_gmm(i, j)
                model_list.append(model)

                print('weight:', model.weights_)
                print('mean:', model.means_)
                print('cov:', np.sqrt(model.covariances_))

                tmp_prob = calculate_gaussian(min_list, model.weights_, model.means_, np.sqrt(model.covariances_))
                tmp_df = pd.DataFrame(dev_graph1_df[0]["Time"]).join(pd.DataFrame(tmp_prob, columns=["Prob"]))
                learned_df.append(tmp_df)


            ########################################### @@@@@@@@jaeseung
            file_name = root_dir + sel1.lower() + "/" + sel2.lower() + "/" + sel3.lower() + "/" + "context_threshold.csv"
            header_list = ["Temp_Min", "Temp_Max", "Temp_Thres", "Dust_Min", "Dust_Max", "Dust_Thres"]
            step_df = pd.read_csv(file_name, delimiter='\t', header=None, names=header_list, index_col=None,
                                  encoding='CP949', engine="python")

            temp_header = [['On/Off', 'Learned']]
            temp_x = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
            temp_y2 = np.linspace(int(step_df["Temp_Min"][0]), int(step_df["Temp_Max"][0]), 1000)
            temp_y2[temp_x <= min(thres_data[0])] = 0
            temp_y2[temp_x > min(thres_data[0])] = 1
            temp_x = temp_x.reshape(-1, temp_x.shape[0])
            temp_list = np.c_[temp_x[0], temp_y2]
            temp_list = temp_list.tolist()
            temp_df = temp_header + temp_list

            dust_header = [['On/Off', 'Learned']]  # AirCleaner Draw
            dust_x = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
            dust_y2 = np.linspace(int(step_df["Dust_Min"][0]), int(step_df["Dust_Max"][0]), 1000)
            dust_y2[dust_x <= min(thres_data[1])] = 0
            dust_y2[dust_x > min(thres_data[1])] = 1
            dust_x = dust_x.reshape(-1, dust_x.shape[0])
            dust_list = np.c_[dust_x[0], dust_y2]
            dust_list = dust_list.tolist()
            dust_df = dust_header + dust_list

            data3 = [['x','Learned']]  # Bulb Draw
            x3 = dev_graph1_df[2]["Time"].tolist()
            learned3 = learned_df[2]["Prob"].tolist()
            for i in range(len(x3)):
                tmp_list = []
                tmp_list.append(x3[i])
                tmp_list.append(learned3[i])
                data3.append(tmp_list)

            data4 = [['x','Learned']]  # RobotCleaner Draw
            x4 = dev_graph1_df[3]["Time"].tolist()
            learned4 = learned_df[3]["Prob"].tolist()
            for i in range(len(x4)):
                tmp_list = []
                tmp_list.append(x4[i])
                tmp_list.append(learned4[i])
                data4.append(tmp_list)

            data5 = [['x', 'Learned']]  # TV Draw
            x5 = dev_graph1_df[4]["Time"].tolist()
            learned5 = learned_df[4]["Prob"].tolist()
            for i in range(len(x5)):
                tmp_list = []
                tmp_list.append(x5[i])
                tmp_list.append(learned5[i])
                data5.append(tmp_list)

            DrawData = [temp_df,dust_df,data3,data4,data5]
            for i in DrawData:
                print(i)

            return HttpResponse(json.dumps(DrawData), content_type="application/json")




def generate_submit(request): #generator_layout_submit ajax
    print("##############")
    if request.method == 'POST':
        print("in request post")
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        job = request.POST.get('job')
        season = request.POST.get('season')
        return HttpResponse(json.dumps("success!"), content_type="application/json")

from datetime import datetime

def convert_time(time):
    time_object = datetime.strptime(time, "%Y_%m_%d_%H_%M_%S_%f")
    cut_microsec = time_object.replace(microsecond=0)
    return cut_microsec.strftime("%Y-%m-%d %H:%M:%S")

def percept(request):   ##################### perceptajax
    print("def percept success")
    if request.method == 'POST':
        print("def percept POST success")
        file_name = request.POST.get('file_name')

        header_name = ["Start Time", "End Time", "Pose", "Action"]
        root_dir = os.path.join(BASE_DIR, "polls/static/percept/")
        file_loc = root_dir + file_name

        df_from_file = pd.read_csv(file_loc, delimiter='\t', header=None, names=header_name, index_col=None,
                                   encoding='UTF8', engine="python")
        df_time_converted = df_from_file
        df_time_converted["Start Time"] = df_from_file["Start Time"].apply(convert_time)
        df_time_converted["End Time"] = df_from_file["End Time"].apply(convert_time)
        response = HttpResponse(df_time_converted.to_html(classes='table table-bordered table-fixed'), content_type='text/html')
        print(response)
        return response