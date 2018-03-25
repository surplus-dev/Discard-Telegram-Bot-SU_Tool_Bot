# 패키지 불러오기
import telegram
from telegram.ext import Updater, RegexHandler, CommandHandler

from urllib import parse

import re
import sqlite3
import json

# set.json 설정 확인
try:
    json_data = open('set.json').read()
    set_data = json.loads(json_data)
except:
    while 1:
        print('Token : ', end = '')
        
        new_json = str(input())
        if new_json != '':
            with open("set.json", "w") as f:
                f.write('{ "token" : "' + new_json + '" }')
            
            json_data = open('set.json').read()
            set_data = json.loads(json_data)

            break

        else:
            print('Insert Values')
            
            pass

# 봇 토큰 삽입
my_token = set_data['token']
updater = Updater(my_token)

# 인터위키 딕셔너리 생성
link = {
    '나무위키' : 'https://namu.wiki/w/',
    '리브레위키' : 'https://librewiki.net/wiki/',
    '백괴사전' : 'https://uncyclopedia.kr/wiki/',
    '위키백과' : 'https://ko.wikipedia.org/wiki/', 
    '진보위키' : 'https://jinbowiki.org/wiki/index.php/',
    '구스위키' : 'http://goos.wiki/index.php?title=',
    '디시위키' : 'http://wiki.dcinside.com/wiki/',
    '네이버' : 'https://search.naver.com/search.naver?query=',
    '구글' : 'https://www.google.co.kr/search?q=',
    '유튜브' : 'https://www.youtube.com/results?search_query=',
    '다음' : 'http://search.daum.net/search?q='
}

# 디비 연결
conn = sqlite3.connect('bot.db', check_same_thread = False)
curs = conn.cursor()

# 테이블 생성
curs.execute("create table if not exists stats(id text, count text)")
conn.commit()

# 버전 정리
bot_version = '다용도봇 v0.0.1'
print(bot_version)

# URL 인코딩 함수
def url_encode(data):
    return parse.quote(data).replace('/','%2F')

def insert_stats(data):
    curs.execute('select count from stats where id = ?', [data])
    count = curs.fetchall()
    if count:
        count = int(count[0][0]) + 1
        curs.execute("update stats set count = ? where id = ?", [count, data])
    else:
        curs.execute('insert into stats (id, count) values (?, "1")', [data])
    
    conn.commit()

# 메인 함수
def tool_send(bot, update):
    # 내용 출력
    print(str(update.message.text))

    # 챗 아이디
    chat_id = update.message.chat_id
    
    # 만약 ^\[버전]$ 이 있으면
    if re.search('^\[버전]$', str(update.message.text)):
        # 버전을 리턴
        update.message.reply_text(bot_version)

    # 만약 ^\[통계]$ 가 있으면
    if re.search('^\[통계]$', str(update.message.text)):
        # 통계를 리턴
        curs.execute("select id, count from stats")
        count = curs.fetchall()
        if count:
            data = ''
            for plus_data in count:
                data += '* ' + plus_data[0] + ' : ' + plus_data[1] + '\n'
        else:
            data = '* 통계 없음'

        update.message.reply_text(data)

    # 만약 ^\[도움]$ 이 있으면
    if re.search('^\[도움]$', str(update.message.text)):
        # 도움말 리턴
        update.message.reply_text('== 지원하는 커맨드 ==\n> [[위키명:문서명]]\n>> 나무위키, 리브레위키, 위키백과, 구스위키, 진보위키, 백괴사전\n> [버전]\n> [통계]')

    # 인터위키 내용을 포함하면
    inter = re.search('^\[\[((?:(?!]]).)+)]]$', str(update.message.text))
    if inter:
        # 인터위키 통계 삽입
        insert_stats('inter')

        # 그룹화 해서
        inter = inter.groups()

        # 다시 사이트 부분과 문서명을 분리
        start = re.search('^([^:]*):(.*)$', inter[0])
        if start:
            # 다시 그룹화
            start = start.groups()
            
            # 만약 사이트가 딕셔너리 안에 있으면
            if start[0] in link:
                # 인코딩하고 마크다운으로 리턴
                bot.send_message(
                    chat_id = chat_id, 
                    text = "[" + inter[0] + "](" + link[start[0]] + url_encode(start[1]) + ")", 
                    parse_mode = telegram.ParseMode.MARKDOWN
                )

# 이 정규식을 포함하는 채팅만 인식하도록
data_list = ['^\[(?:버전|통계|도움)]$', '^\[\[((?:(?!]]).)+)]]$']
for data in data_list:
    updater.dispatcher.add_handler(RegexHandler(data, tool_send))
    
updater.start_polling()
updater.idle()