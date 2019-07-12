# -*- coding: utf-8 -*-
import re
import json
import re
import requests

import urllib.request
import urllib.parse
import random
import threading

from bs4 import BeautifulSoup
from urllib.error import HTTPError
from string import punctuation
from flask import Flask, request
from slack import WebClient
from slackeventsapi import SlackEventAdapter


from slack.web.classes import extract_json
from slack.web.classes.blocks import *
from slack.web.classes.elements import *
from slack.web.classes.interactions import MessageInteractiveEvent

# OAuth & Permissions로 들어가서
# Bot User OAuth Access Token을 복사하여 문자열로 붙여넣습니다
SLACK_TOKEN = 'xoxb-689663245013-694624077094-RQYCeKuznpIBI9a29XiIfvtk'
# Basic Information으로 들어가서
# Signing Secret 옆의 Show를 클릭한 다음, 복사하여 문자열로 붙여넣습니다
SLACK_SIGNING_SECRET = ''


app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)
mean_dict = {}
skill_dict = {}

# ====================
def response(channel, return_text):
    slack_web_client.chat_postMessage(
        channel=channel,
        text=return_text
    )

def response_json(channel, message_blocks):
    # 메시지를 채널에 올립니다
    slack_web_client.chat_postMessage(
        channel=channel,
        blocks=extract_json(message_blocks)
    )

def introduce_msg():
    return '''
    안녕하세요? algobot 입니다.  
알고리즘 개념은 `@algobot -a topic` 으로 검색해주세요.
문제 링크는 `@algobot -prob 문제 이름` 으로 검색해주세요.
랜덤 문제는 `@algobot -random` 으로 검색해주세요.
    '''

def error_msg():
    return '''명령어가 잘못되었습니다.
알고리즘 개념은 `@algobot -a topic` 으로 검색해주세요.
"topic 목록" ("stack", "...")
문제 링크는 `@algobot -prob 문제 이름` 으로 검색해주세요.
랜덤 문제는 `@algobot -random` 으로 검색해주세요.        '''

def get_problem():
    url = "https://www.acmicpc.net/problemset"
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    print(soup)

def mean_fun(text):
    if text in mean_dict.keys():
        list_mean = get_mean_list(text)
        url = set_skill_problem_url(text)
        list_problem = crawling_skill_problem(url,text)
        return list_mean + [' '] +list_problem
    else:
        return ['다시 입력해주세요.']
    

def crawling_mean():
    # 크롤링 부분
    url = "https://swexpertacademy.com/main/code/referenceCode/referenceCodeList.do"
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    names = []
    classification = []
    means = []

    total = soup.find("div", class_="row reference_list data")
    for i, body in enumerate(total.find_all("div", class_="widget-box-sub")):
        if i < 18 :
            names.append(skill_dict[body.find("div", class_="header-caption").get_text().strip().lower()])
            names.append(body.find("div", class_="header-caption").get_text().strip().lower())
            classification.append(body.find("div", class_="widget-toolbar-sub").get_text().strip())
            classification.append(body.find("div", class_="widget-toolbar-sub").get_text().strip())
            means.append(body.find("div", class_="inner-txt").get_text().strip())
            means.append(body.find("div", class_="inner-txt").get_text().strip())
    
    for i in range(0,36):
        keyword = []
        keyword.append(classification[i])
        keyword.append(means[i])
        mean_dict[names[i]] = keyword

    del mean_dict['permutation & combination']
    mean_dict['조합'], mean_dict['combination'] = ["Algorithm","조합은 집합에서 일부 원소를 취해 부분 집합을 만드는 방법을 말한다."]
    mean_dict['순열'], mean_dict['permutation'] = ["Algorithm","순열은 순서가 부여된 임의의 집합을 다른 순서로 뒤섞는 연산이다"]


def get_mean_list(text):
    mean_list = []
    mean_list.append(text)
    mean_list.append(' ')
    mean_list.append("분류 : " + mean_dict[text][0])
    mean_list.append(mean_dict[text][1])
    return mean_list


def rand_problem(channel):
    url = "https://www.acmicpc.net/problem/recent/accepted/"
    rand_page = random.randrange(1,11)
    print("rand_page : " + str(rand_page))
    rand_num = random.sample(range(1, 101), 10 )
    print("rand_num : " + str(rand_num))
    rand_prob = []

    req = urllib.request.Request(url + str(rand_page), headers={'User-Agent': 'Mozilla/5.0'})
    sourcecode = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    col_md = soup.find("div",class_="col-md-12")
    div_tag = col_md.find("div", class_="table-responsive")
    count = 0
    for i, tr_tag in enumerate(div_tag.find_all("tr")):
        if(i in rand_num):
            td_list = []
            for j, td_tag in enumerate(tr_tag.find_all("td")):
                if j != 2 and j != 3:
                    td_list.append(td_tag.get_text())
            rand_prob.append(td_list)

    print(rand_prob)
    pro_url = "https://www.acmicpc.net/problem/"
    return_list = []
    for i in rand_prob:
        i[0] = pro_url + i[0]

    rand_prob = sorted(rand_prob, key = lambda x : int(x[2]), reverse = True)
    for i in rand_prob:
        return_list.append("<"+ i[0] + "|" + i[1] + "> \t *제출수* : " + str(i[2]) + " * / 정답비율* : " + i[3])
        #return_list.append("< %10s | %5s > \t *제출수* : %5s *정답비율* : %5s" %(i[0],i[1],i[2],i[3]))

    response(channel, list_to_str(return_list))


def set_skill_problem_url(text):
    url = "https://www.acmicpc.net/problem/tag/"
    url += urllib.parse.quote_plus(skill_dict[text])
    return url


def crawling_skill_problem(url,text):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    sourcecode = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    prob_name_list = []
    prob_url_list = []

    for div_tag in soup.find_all("div", class_="table-responsive"):
        tbody = div_tag.find("tbody")
        for tr_tag in tbody.find_all("tr"):
            prob_name_list.append(tr_tag.find("a").get_text())

        for td in div_tag.find_all("td", class_="list_problem_id"):
            prob_url_list.append("https://www.acmicpc.net/problem/"+td.get_text())

    prob_list = []
    if text == 'counting sort' or text == 'parametric search' or text =='quick sort' :
        prob_list.append(text + "관련 문제는 준비되지 않아 정렬 관련 랜덤 문제 리스트입니다.")
    else:
        prob_list.append(text + " 관련 랜덤 문제 리스트입니다. ")

    for i in random.sample(range(1, len(prob_name_list)),3):
        prob_list.append("*"+prob_name_list[i] +"* : "+ prob_url_list[i])

    prob_list.append("*더 많은 "+ text + " 관련 문제 ->* " + url)

    return prob_list

def list_to_str(list_):
    text = ''
    for l in list_:
        text += l + '\n'
    return text


def set_skill():
    skill_dict['stack'] = '스택'
    skill_dict['recursion'] = '재귀 호출'
    skill_dict['queue'] = '큐'
    skill_dict['priority queue'] = '우선 순위 큐'
    skill_dict['hash'] = '해싱'
    skill_dict['tree'] = '트리'
    skill_dict['graph'] = '그래프 이론'
    skill_dict['linked list'] = '링크드 리스트'
    skill_dict['insertion sort'] = '정렬'
    skill_dict['quick sort'] = '정렬' # 문제 분류가 되어있지 않습니다. -> '정렬' 로
    skill_dict['counting sort'] = '정렬' # 문제 분류가 되어있지 않습니다. -> '정렬' 로
    skill_dict['parametric search'] = '정렬' # 문제 분류가 되어있지 않습니다. -> '정렬' 로
    skill_dict['binary search'] = '이분 탐색'
    skill_dict['dfs searching'] = 'DFS'
    skill_dict['bfs searching'] = 'BFS'
    skill_dict['dynamic programming'] = '다이나믹 프로그래밍'
    skill_dict['permutation'] = '순열'
    skill_dict['combination'] = '조합'
    skill_dict['dijkstra'] = '다익스트라 알고리즘'

    skill_dict['스택'] = '스택'
    skill_dict['큐'] = '큐'
    skill_dict['DFS'] = 'DFS'
    skill_dict['dfs'] = 'DFS'
    skill_dict['BFS'] = 'BFS'
    skill_dict['bfs'] = 'BFS'
    skill_dict['재귀 호출'] = '재귀 호출'
    skill_dict['우선순위큐'] = '우선 순위 큐'
    skill_dict['그래프'] = '그래프 이론'
    skill_dict['순열'] = '순열'
    skill_dict['조합'] = '조합'
    skill_dict['이분 탐색'] = '이분 탐색'
    skill_dict['링크드리스트'] = '링크드 리스트'
    skill_dict['트리'] = '트리'
    skill_dict['해싱'] = '해싱'
    skill_dict['정렬'] = '정렬'
    skill_dict['permutation & combination'] = 'permutation & combination'

def _algo_prob_selection(text):
   if text == "":
       return "`@<봇이름> 스택` 과 같이 멘션해주세요."

   else:
       url = "https://www.acmicpc.net/problemset?search="
       url2 = urllib.parse.quote_plus(text) # 일단 한글만! ex 스택,큐
       url += url2
       url = url.replace('%3C%40UKY7PS0GK%3E+','')

       #print(url.replace('%3C%40UKY7PS0GK%3E+',''))
       req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
       source_code = urllib.request.urlopen(req).read()
       soup = BeautifulSoup(source_code, "html.parser")

       messages = []
       #prob_url = "https://icpc.me/"
       prob_url = "https://www.acmicpc.net/problem/"
       prob_url_list = []

       prob_name= []
       prob_name_list = []
       for msg in soup.find_all("div", class_="table-responsive"):
           for atag in msg.find_all("a"):
               prob_name.append(atag.get_text())

           for td in msg.find_all("td", class_="list_problem_id"):
               messages.append(td.get_text())
               prob_url_list.append(prob_url+td.get_text())

       for i,name in enumerate(prob_name):
           if i==0 or i%3==0:
               prob_name_list.append(name)


       result = []
       for i in range(0,len(prob_name_list)):
           if i<10:
               result.append("*"+prob_name_list[i] + "* : " + prob_url_list[i])
           else:
               result.append("*검색 내용 더 보기 ->*" + url )
               break
        

#        #print(prob_name_list)   # 문제이름 모음
#        #print(messages)         # 문제번호 모음
#        #print(prob_url_list)    # URL 모음

   return u'\n'.join(result)

# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]
    return_text = "안녕하세요? algobot입니다. 명령어를 입력해주세요."

    print(text)
    # main cmd
    if len(text) > 12:
        cmd = text.split()[1]
    else:
        cmd = "-intro"

    # sub_cmd
    if cmd == '-a': # 개념 함수 실행
        sub_cmd = " ".join(text.split()[2:]).replace('"','').lower()
        if sub_cmd == '': # 버튼
            return_value = button_test(list(mean_dict.keys()))
            print(type(return_value))
            response_json(channel,return_value)
        else :
            return_text = list_to_str(mean_fun(sub_cmd))
    elif cmd == '-prob': # 문제 검색 함수 실행 
        sub_cmd = " ".join(text.split()[2:]).replace('"','').lower()
        return_text = _algo_prob_selection(sub_cmd)
    elif cmd == '-random': # 랜덤 함수 실행
        th = threading.Thread(target = rand_problem, args=[channel])
        th.start()
        response(channel, "문제를 랜덤 검색 중 입니다... :)")
        return "OK", 200
    elif cmd == '-intro':
        return_text = introduce_msg()
    else:
        return_text = error_msg()

    # 슬랙 챗봇이 대답합니다.
    response(channel, return_text)


# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

set_skill()
crawling_mean()


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)



