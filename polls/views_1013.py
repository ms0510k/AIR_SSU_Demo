from io import StringIO

from django.http import HttpResponse
from django.shortcuts import render
from DjangoTest.settings import BASE_DIR
import json
import codecs
import socket
import webbrowser
import urllib.request
import datetime
import pytz

import csv
from django.http import StreamingHttpResponse
import os
import sys
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
from time import sleep

"""바른기술 측에서 넘겨주는 음성명령어를 담고 있는 변수"""
butler_command = ""

port = 10002
address = "192.168.1.20"

def index(request):
    return render(request, "../templates/index.html")

def layout_index(request):
    return render(request, "../templates/layout_index.html")

def profilelearner(request): #민성
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


def search_dir(dirname, file_list):
    for (path, dir, files) in os.walk(dirname):
        for filename in files:
            ext = os.path.splitext(filename)[-1]
            if ext == '.csv':
                # print("%s/%s" % (path, filename))
                tmp = path + '/' + filename
                # print(tmp)
                file_list.append(tmp)


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def LoadData(request): #민성 load data 버튼 누를시 ajax
    print("def LoadData success")
    if request.method == 'POST':
        print("def LoadData POST success")
        sel1 = request.POST.get('sel1')
        sel2 = request.POST.get('sel2')
        sel3 = request.POST.get('sel3')
        msg=sel1+sel2+sel3
        print(msg)

        root_dir = os.path.join(BASE_DIR, "polls/static/data_test/")
        user_list = ['park', 'kim', 'choi']
        device_list = ['airconditioner', 'aircleaner', 'bulb', 'robotcleaner', 'tv']
        season_list = ['spring', 'summer', 'fall', 'winter']
        week_list = ['weekdays', 'weekend']
        choose_list = []

        for i in range(len(user_list)):
            for j in range(len(device_list)):
                for k in range(len(season_list)):
                    for n in range(len(week_list)):
                        choose_list.append(
                            root_dir + "/" + user_list[i] + "/" + device_list[j] + "/"
                            + season_list[k] + "/" + week_list[n])

        file_list = []
        df_list = []
        count = 0
        header_name = ["Time", "UID", "Device", "Prob", "Season", "Week", "Weather"]

        search_dir(choose_list[0], file_list)

        header_list=["Time", "UID", "Device", "Prob", "Season", "Week", "Weather"]


        for i in file_list:
            #print(i)
            df_list.append(pd.read_csv(i, delimiter='\t', header=None, names=header_name, index_col=None, encoding='CP949', engine="python"))

        for i in df_list:
            #print(i)
            count += 1
        #
        # new_file = file_list[0]+".xlsx"
        # sio = StringIO()
        # PandasDataFrame = df_list[0]
        # PandasWriter = pd.ExcelWriter(sio, engine='xlsxwriter')
        # PandasDataFrame.to_excel(PandasWriter, sheet_name=new_file)
        # PandasWriter.save()
        #
        # sio.seek(0)
        # workbook = sio.getvalue()
        #
        # response = StreamingHttpResponse(workbook,
        #                                  content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # response['Content-Disposition'] = 'attachment; filename=%s' % new_file

        final_df = pd.DataFrame(df_list[0])

        final_df = pd.concat(df_list)

        #print(final_df)

        response = HttpResponse(final_df.to_html(classes='table table-bordered'), content_type='text/html')
        # response['Content-Disposition'] = 'attachment; filename=%s', file_list[0]
        #
        # writer = csv.writer(response)

        # reader = csv.reader(StringIO(file_list[0]))
        #response = HttpResponse(df_list[0].to_csv(), content_type='text/csv')
        print(response)
        return response

        #return HttpResponse(json.dumps(df_list[0].to_json(orient='records')), content_type="application/json")



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
def fire_rule(request):
    if request.method == 'POST':
        # JESS Engine에 연결한 후, 웹 상에서 넘어온 정보들을 Parsing
        engine = connect_jess_engine(20000)
        answer_case = str(request.POST.get('answerCase')).strip()
        command = str(request.POST.get('command')).strip()
        hour = str(request.POST.get('hour')).strip()
        minute = str(request.POST.get('minute')).strip()
        month = str(request.POST.get('month')).strip()
        day = str(request.POST.get('day')).strip()

        print("Answer Case: " + answer_case)
        print("Command: " + command)

        results = ""
        results_without_debug = []
        results_question = []
        answer_set = ""
        question_case = ""
        dic_all_holds = {}
        debug_string = ""

        # @jaeseung : command가 우리가 입력하는 내용 - 외출모드, 맞아, 5일, 그래
        # answer_case : command에 대한 정답을 담고 있는 것
        if answer_case == "":
            # 처음 시작해서 모드 설정하는 경우
            engine.reset()
            engine.resultOfCommand("(watch all)")

            if "외출모드" in str(command).strip():
                home_device_facts = parse_json_to_fact("device_info.json")
                # smart_plug_facts = parse_json_to_fact("smartplug_device.json")
                # forget_facts = parse_json_to_fact("forget_device.json")

                # Assert Facts in JESSㄹ
                assert_facts_in_jess(home_device_facts, engine)
                # assert_facts_in_jess(smart_plug_facts, engine)
                # assert_facts_in_jess(forget_facts, engine)

                # Weather Context
                # 날씨 정보 받아오기
                parsed_weather = get_weather_data()

                weather_facts = parse_weather_to_fact(parsed_weather)
                assert_facts_in_jess(weather_facts, engine)

                # start_barun_demo()

            elif "귀가전날" in str(command).strip() or "방범모드" in str(command).strip() \
                    or "문열림" in str(command).strip():
                home_device_facts = parse_json_to_fact("device_info.json")
                # smart_plug_facts = parse_json_to_fact("smartplug_device.json")
                # forget_facts = parse_json_to_fact("forget_device.json")

                # Assert Facts in JESSㄹ
                assert_facts_in_jess(home_device_facts, engine)
                # assert_facts_in_jess(smart_plug_facts, engine)
                # assert_facts_in_jess(forget_facts, engine)

            # @jaeseung : 공통부분
            # Temporal Context
            season, time, date = parse_time_information(hour, minute, month, day)

            # Assert Temporal Context Fact in JESS
            assert_temporal_to_fact(season, month, time, date, engine)

            # @jaeseung : JESS 실행에 필수
            '''명령 실행'''
            facts = engine.resultOfCommand("(assert (order-butler (command \"" + command + "\")))")
            results = engine.resultOfCommand("(run)")

            results = results.split('\n')
            facts = facts.split('\n')

            '''웹 상의 Debug 창에 출력될 정보들을 Parsing 하는 부분'''
            for i in range(0, len(results)):
                if "==>" in str(results[i]).strip() or "<==" in str(results[i]).strip() or "FIRE" in str(
                        results[i]).strip() or "<=>" in str(results[i]).strip():
                    print("Debug String: " + results[i])
                    facts.append(results[i])
                else:
                    print("Result String: " + results[i])
                    results_without_debug.append(results[i])

            debug_string = facts

        # @jaeseung : 맞아 부터
        else:
            # 사용자에 대한 답변이 있는 경우
            # Context에 의해 음식 추천해주는 경우에서
            # No인 경우에는 JESS 상에서 다른 음식을 물어야 한다.
            if answer_case == "type_meal_by_context" and command == "no":
                fact = "(assert (ask-menu (reply " + command + ")))"
            else:
                fact = "(assert (answer (ident " + answer_case + ")(text " + command + ")))"

            facts = engine.resultOfCommand(fact)
            results = engine.resultOfCommand("(run)")

            results = results.split('\n')
            facts = facts.split('\n')

            # Debug 결과와 Rule Fire 결과를 분리하는 코드
            for i in range(0, len(results)):
                if "==>" in str(results[i]).strip() or "<==" in str(results[i]).strip() or "FIRE" in str(
                        results[i]).strip() or "<=>" in str(results[i]).strip():
                    print("Debug String: " + results[i])
                    facts.append(results[i])
                else:
                    print("Result String: " + results[i])
                    results_without_debug.append(results[i])

            debug_string = facts

        # @jaeseung : JESS 결과가 질문일때
        # Rule Fire 결과가 질문일 경우
        if check_question_in_result(results_without_debug):
            question_index = get_question_index(results_without_debug)
            print("Before Answer Split: " + results_without_debug[question_index])
            # Question Index + 1 => Valid Answer Set
            # Question Index + 2 => Question Identification
            answer_set = str(results_without_debug[question_index + 1]).strip().split(" ")
            print(answer_set)
            question_case = results_without_debug[question_index + 2]
            print(question_case)

            # 질문까지 포함된 문장으로 재구성
            results_without_debug = results_without_debug[:question_index + 1]
            dic_all_holds["Question"] = results_without_debug

        # 각 질문 타입에 따라 넣어줘야할 Fact가 다르기 때문에, case를 지정해서 다시 Response 해야함
        # 질문에 대한 최종 결과일 경우
        else:
            answer_set = []
            question_case = ""

            if "주문하기" in str(results_without_debug[0]).strip():
                webbrowser.open("http://ailab.synology.me:10080/demoShop/index.html")
                dic_all_holds["Result"] = ["사이트에 연결합니다."]

            else:
                # Device 상태를 받아서 json으로 변환하는 코드를 이 부분에 작성해야 할 듯
                # ID State: ---
                device_state_facts = []
                common_results = []

                print("First Result Without Debug: " + str(results_without_debug[0]))

                # 외출 모드를 실행합니다. 로 시작하는 경우
                if "장기 외출모드를" in str(results_without_debug[0]).strip():
                    print("장기 외출 모드가-")
                    device_json = convert_device_state_in_json(results_without_debug[6:])
                    send_json = convert_json_to_send_format(device_json, "외출모드")

                    # @jaeseung : 바른기술로 JSON 던짐 - 주석처리
                    # 실질적으로 openhap과 통신
                    print("Send JSON: " + json.dumps(send_json))
                    #send_device_json_to_server(send_json)

                    # 이 뒤의 코드에서 바른기술 측으로 보내는 코드 작성하면 될 듯

                elif "단기 외출모드를" in str(results_without_debug[0]).strip():
                    print("단기 외출 모드가-")
                    device_json = convert_device_state_in_json(results_without_debug[5:])
                    send_json = convert_json_to_send_format(device_json, "외출모드")

                    print("Send JSON: " + json.dumps(send_json))
                    # send_device_json_to_server(send_json)

                    # 이 뒤의 코드에서 바른기술 측으로 보내는 코드 작성하면 될 듯

                elif "귀가 모드" in str(results_without_debug[0]).strip():
                    print("귀가당일")
                    device_json = convert_device_state_in_json(results_without_debug[2:])
                    send_json = convert_json_to_send_format(device_json, "귀가당일")

                    print("Send JSON: " + json.dumps(send_json))
                    #send_device_json_to_server(send_json)

                elif "예약 동작이" in str(results_without_debug[0]).strip():
                    print("귀가전날")
                    device_json = convert_device_state_in_json(results_without_debug[2:])
                    send_json = convert_json_to_send_format(device_json, "귀가전날")

                    print("Send JSON: " + json.dumps(send_json))
                    #send_device_json_to_server(send_json)

                elif "집안 인기척이" in str(results_without_debug[0]).strip() or \
                                "현관 앞 움직임" in str(results_without_debug[0]).strip():
                    print("방범모드")
                    device_json = convert_device_state_in_json(results_without_debug[1:])
                    send_json = convert_json_to_send_format(device_json, "방범모드")

                    print("Send JSON: " + json.dumps(send_json))
                    #send_device_json_to_server(send_json)

                """
                각 Device 상태들을 웹 화면에 뿌려주기 위한 과정
                각 디바이스 상태와 일반 결과를 분리하는 과정
                """
                for i in range(0, len(results_without_debug)):
                    if "State: ON" in str(results_without_debug[i]).strip() or "State: OFF" in str(
                            results_without_debug[i]).strip() or "State: 예약모드" in str(
                        results_without_debug[i]).strip() or "스마트플러그" in str(
                        results_without_debug[i]).strip() or "State: 0" in str(results_without_debug[i]).strip() or \
                                    "State: 100" in str(results_without_debug[i]).strip() or "State: dock" in str(
                        results_without_debug[i]).strip() or "State: vacuum" in str(results_without_debug[i]).strip() \
                            or "State: 외출모드" in str(results_without_debug[i]).strip() or "State: 겨울설정온도" in str(results_without_debug[i]).strip() \
                            or "State: 여름설정온도" in str(results_without_debug[i]).strip() or "State: Power" in str(results_without_debug[i]).strip():

                        print("Device String: " + results_without_debug[i])

                        results_without_debug[i] = results_without_debug[i].replace("_", " ")
                        device_state_facts.append(results_without_debug[i])

                    else:
                        print("Recommend Result String: " + results_without_debug[i])
                        common_results.append(results_without_debug[i])

                dic_all_holds["Result"] = common_results
                dic_all_holds["Recommend_without_json"] = device_state_facts

                dic_all_holds["Out"] = ["device_info.json"]
                dic_all_holds["Response"] = ["device_info_OPENHAB.json"]

        dic_all_holds["answerSet"] = answer_set
        dic_all_holds["questionCase"] = [question_case]
        dic_all_holds["Debug"] = debug_string

        return HttpResponse(json.dumps(dic_all_holds),
                            content_type="application/json")


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
