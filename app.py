# 패키지 불러오기
import telegram
from telegram.ext import Updater, RegexHandler, CommandHandler

import urllib.parse
import sqlite3
import requests
import json
import pytz
import time
import re

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
            print('값이 이상합니다.')
            
            pass

# 봇 토큰 삽입
my_token = set_data['token']
updater = Updater(my_token)

print(set_data['token'])

# 인터위키 딕셔너리 생성
link = {
    '나무' : 'https://namu.wiki/w/',
    '알파' : 'https://www.alphawiki.org/w/',
    '리베' : 'http://rigvedawiki.net/w/',
    '리브레' : 'https://librewiki.net/wiki/',
    '백괴' : 'https://uncyclopedia.kr/wiki/',
    '위백' : 'https://ko.wikipedia.org/wiki/', 
    '진보' : 'https://jinbowiki.org/wiki/index.php/',
    '구스' : 'http://goos.wiki/index.php?title=',
    '디시' : 'http://wiki.dcinside.com/wiki/',
    '유리' : 'https://yuri.wiki/w/index.php?title=',
    
    '오픈테섭' : 'https://namu.ml/w/',
    '더시드' : 'https://theseed.io/w/',

    '네이버' : 'https://search.naver.com/search.naver?query=',
    '구글' : 'https://www.google.com/search?q=',
    '유튜브' : 'https://www.youtube.com/results?search_query=',
    '다음' : 'http://search.daum.net/search?q=',
    '덕덕고' : 'https://duckduckgo.com/?q='
}

# 디비 연결
conn = sqlite3.connect('bot.db', check_same_thread = False)
curs = conn.cursor()

# 테이블 생성
curs.execute("create table if not exists stats(id text, count text)")
curs.execute("create table if not exists setting(id text, data text)")
conn.commit()

curs.execute('select data from setting where id = "pw"')
if not curs.fetchall():
    print('비밀번호? : ', end = '')
    pw = input()
    
    curs.execute('insert into setting (id, data) values ("pw", ?)', [pw])
    conn.commit()

# 버전 정리
bot_version = '다용도봇-07'
print(bot_version)

# URL 인코딩 함수
def url_encode(data):
    return urllib.parse.quote(data).replace('/','%2F')

# 시간 가져오기
def get_time():
    now = time.localtime()
    date = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

    return date

def insert_db(data):
    curs.execute('select count from stats where id = ?', [data])
    count = curs.fetchall()
    if count:
        curs.execute("update stats set count = ? where id = ?", [str(int(count[0][0]) + 1), data])
    else:
        curs.execute('insert into stats (id, count) values (?, "1")', [data])
    
    conn.commit()
    
# 메인 함수
def tool_send(bot, update):
    print(str(update.message.text))

    delay_time = int(re.sub('-|:| ', '', get_time())) - int(re.sub('-|:| ', '', str(update.message.date)))
    print(delay_time)

    if delay_time < 120:        
        chat_id = update.message.chat_id

        if re.search('^\[핑]$', str(update.message.text)):
            insert_db('ping')

            update.message.reply_text(str(delay_time) + '초')
        
        if re.search('^\[버전]$', str(update.message.text)):
            insert_db('version')
            
            update.message.reply_text(bot_version)

        if re.search('^\[통계]$', str(update.message.text)):
            insert_db('count')

            curs.execute("select id, count from stats order by id asc")
            count = curs.fetchall()
            if count:
                data = ''
                for plus_data in count:
                    data += '> ' + plus_data[0] + ' : ' + plus_data[1] + '\n'
            else:
                data = '> 통계 없음'

            update.message.reply_text(data)
            
        re_set = re.search('^\[통계 초기화\(((?:(?!\)).)+)\)]$', str(update.message.text))
        if re_set:
            re_set = re_set.groups()[0]

            curs.execute("select data from setting where id = 'pw'")
            if re_set == curs.fetchall()[0][0]:
                curs.execute('delete from stats')
                conn.commit()

                update.message.reply_text('> 완료')
            
        time_re = re.search('^\[시간대\(((?:(?!\)).)+)\)]$', str(update.message.text))
        if time_re:
            time_re = time_re.groups()[0]

            try:
                update.message.reply_text(pytz.timezone(time_re).localize(datetime.datetime.today()).strftime("%Y-%m-%d %H:%M:%S"))
            except:
                update.message.reply_text('http://technote.kr/202\n\n타임존 정보')

        if re.search('^\[도움]$', str(update.message.text)):
            insert_db('help')

            update.message.reply_text('= 지원하는 커맨드 =\n== [[위키명:문서명]] ==\n=== 위키 ===\n> 나무, 리브레, 리베, 위백, 구스, 진보, 백괴, 유리\n\n=== 일반 ===\n> 네이버, 구글, 유튜브, 다음\n\n== 기타 ==\n> [버전]\n> [통계]')

        inter = re.search('^\[\[((?:(?!]]).)+)]]$', str(update.message.text))
        if inter:
            insert_db('inter')

            inter = inter.groups()

            start = re.search('^([^:]*):(.*)$', inter[0])
            if start:
                start = start.groups()
                
                if start[0] in link:
                    insert_db('inter:' + start[0])

                    if requests.get(link[start[0]] + url_encode(start[1])).status_code != 404:
                        bot.send_message(
                            chat_id = chat_id, 
                            text = "[" + inter[0] + "](" + link[start[0]] + url_encode(start[1]) + ")", 
                            parse_mode = telegram.urllib.parseMode.MARKDOWN
                        )
                    else:
                        bot.send_message(
                            chat_id = chat_id, 
                            text = "문서가 없습니다.\n\n> [구글](https://www.google.com/search?q=" + start[0] + ' ' + url_encode(start[1]) + ")\n> [덕덕고](https://duckduckgo.com/?q=" + start[0] + ' ' + url_encode(start[1]) + ")", 
                            parse_mode = telegram.urllib.parseMode.MARKDOWN
                        )

# 이 정규식을 포함하는 채팅만 인식하도록
data_list = ['^\[(?:((?!\]).)+)]$', '^\[\[((?:(?!]]).)+)]]$']
for data in data_list:
    updater.dispatcher.add_handler(RegexHandler(data, tool_send))
    
updater.start_polling()
updater.idle()