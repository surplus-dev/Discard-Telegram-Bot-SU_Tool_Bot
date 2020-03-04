import telegram
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters

import urllib.parse
import datetime
import sqlite3
import urllib.request
import json
import time
import re

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
            print('Error')
            
            pass

updater = Updater(set_data['token'], use_context = True)
print(set_data['token'])

link = {
    '나무' : 'https://namu.wiki/w/',
    '리베' : 'http://rigvedawiki.net/w/',
    '디키' : 'https://wiki.dcinside.com/wiki/',
    '리브레' : 'https://librewiki.net/wiki/',
    '위백' : 'https://ko.wikipedia.org/wiki/', 
    'SCP' : "http://ko.scp-wiki.net/",
    
    '오픈테섭' : 'https://namu.ml/w/',
    '더시드' : 'https://theseed.io/w/',

    '네이버' : 'https://search.naver.com/search.naver?query=',
    '구글' : 'https://www.google.com/search?q=',
    '유튜브' : 'https://www.youtube.com/results?search_query=',
    '다음' : 'http://search.daum.net/search?q=',
    '덕덕고' : 'https://duckduckgo.com/?q=',

    '히토미' : 'https://hitomi.la/galleries/'
}

conn = sqlite3.connect('bot.db', check_same_thread = False)
curs = conn.cursor()

curs.execute("create table if not exists stats(id text, count text)")
curs.execute("create table if not exists setting(id text, data text)")
curs.execute("create table if not exists user_set(id text, user text, data text)")
conn.commit()

header = { 'User-Agent' : 'Mozila/5.0', 'referer' : 'https://namu.wiki/w/Test' }

curs.execute('select data from setting where id = "pw"')
if not curs.fetchall():
    print('Password : ', end = '')
    pw = input()
    
    curs.execute('insert into setting (id, data) values ("pw", ?)', [pw])
    conn.commit()

bot_version = '다용도봇-13'
print(bot_version)

def url_encode(data):
    return urllib.parse.quote(data).replace('/','%2F')

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

def get_zip(data):
    return re.sub('\n +', '', data)
    
def tool_send(update, context):
    try:
        chat_id = update.message.chat_id
        sender = update.message.from_user.id
        run_int = 1
            
        all_data = re.findall('(\[(?:(?:(?!\[|\]).)+)]|\[\[(?:(?:(?!]]).)+)]])', str(update.message.text))
        for main_data in all_data:
            print(main_data)
            print('run : ' + str(run_int))
            
            if re.search('\[버전]', main_data):
                insert_db('version')
                
                update.message.reply_text(bot_version)

            if re.search('\[통계]', main_data):
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
                
            re_set = re.search('\[통계 초기화\(((?:(?!\)).)+)\)]', main_data)
            if re_set:
                re_set = re_set.groups()[0]

                curs.execute("select data from setting where id = 'pw'")
                if re_set == curs.fetchall()[0][0]:
                    curs.execute('delete from stats')
                    conn.commit()

                    update.message.reply_text('> 완료')

            set_data = re.search('\[설정\(([^,]+), ?([^,]+)\)]', main_data)
            if set_data:
                set_data = set_data.groups()
                
                insert_db('set')

                ok_list = ['wiki']
                if set_data[0] in ok_list:
                    curs.execute('select id from user_set where id = ? and user = ?', [set_data[0], sender])
                    if curs.fetchall():
                        curs.execute("update user_set set data = ? where id = ? and user = ?", [set_data[1], set_data[0], sender])
                    else:
                        curs.execute('insert into user_set (id, user, data) values (?, ?, ?)', [set_data[0], sender, set_data[1]])

                conn.commit()

                update.message.reply_text('> 완료')

            if re.search('\[도움]', main_data):
                insert_db('help')

                context.bot.send_message(
                    chat_id = chat_id,
                    text =  get_zip('''
                        == `[[위키명:문서명]]` ==\n
                        === 위키 ===\n
                        > 나무, 리브레, 리베, 디키, 위백, SCP\n\n
                        === 일반 ===\n
                        > 네이버, 구글, 유튜브, 다음, 덕덕고\n\n
                        == `[설명(이름, 값)]` ==\n
                        > `wiki, 위키명` (인터위키 기본값)\n\n
                        == 기타 ==\n
                        > `[버전]`\n
                        > `[통계]`\n
                        > `[핑]`
                    '''),
                    parse_mode = 'Markdown'
                )

            inter = re.search('\[\[((?:(?!]]).)+)]]', main_data)
            if inter:
                insert_db('inter')

                inter = inter.groups()

                curs.execute('select data from user_set where id = "wiki" and user = ?', [sender])
                data = curs.fetchall()

                start = re.search('([^:]*):(.*)', inter[0])
                if start or data:
                    if start:
                        start = start.groups()
                    else:
                        start = [data[0][0], inter[0]]
                    
                    if not start[0] in link:
                        if data[0][0] in link:
                            start = [data[0][0], inter[0]]
                            pass_num = 1
                        else:
                            pass_num = 0
                    else:
                        pass_num = 1

                    if pass_num == 1:
                        insert_db('inter:' + start[0])

                        if start[0] == '히토미':
                            data = link[start[0]] + url_encode(start[1]) + '.html'
                        elif start[0] == 'SCP':
                            data = link[start[0]] + url_encode(start[1]).replace('%2F', '/')
                        else:
                            data = link[start[0]] + url_encode(start[1])

                        try:
                            link_data = urllib.request.urlopen(urllib.request.Request(data, headers = header))
                        except urllib.error.HTTPError as e:
                            if e.code == 404:
                                link_data = 404
                            else:
                                link_data = None

                        if link_data:
                            if link_data != 404:
                                context.bot.send_message(
                                    chat_id = chat_id, 
                                    text = "[" + start[0] + ":" + start[1] + "](" + data + ")",
                                    parse_mode = 'Markdown'
                                )
                            else:
                                data_link = re.search('^https?:\/\/([^/]+)', link[start[0]])
                                data_link = data_link.groups()[0]

                                context.bot.send_message(
                                    chat_id = chat_id, 
                                    text = get_zip('' + \
                                        start[0] + ''' 문서가 없습니다. [(바로가기)](''' + data + ''')\n\n
                                        > [구글](https://www.google.com/search?q=site:''' + data_link + ' ' + url_encode(start[1]) + ''')\n
                                        > [덕덕고](https://duckduckgo.com/?q=site:''' + data_link + ' ' + url_encode(start[1]) + ''')
                                    '''),
                                    parse_mode = 'Markdown'
                                )
                        else:
                            context.bot.send_message(
                                chat_id = chat_id, 
                                text = get_zip('''
                                    연결 실패. [(바로가기)](''' + data + ''')\n\n
                                    > [구글](https://www.google.com/search?q=''' + start[0] + ' ' + url_encode(start[1]) + ''')\n
                                    > [덕덕고](https://duckduckgo.com/?q=''' + start[0] + ' ' + url_encode(start[1]) + ''')
                                '''), 
                                parse_mode = 'Markdown'
                            )

            run_int += 1
    except Exception as e:
        print(e)
    
updater.dispatcher.add_handler(MessageHandler(Filters.regex('.'), tool_send))
updater.start_polling()
updater.idle()