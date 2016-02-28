#!/usr/bin/env python
# coding=utf-8

from daemon import Daemon
from googleplaces import GooglePlaces, types, lang
import time, subprocess, telepot, sys

hostname = subprocess.check_output(['hostname']).lower().strip()
longitude = None
latitude = None

class daemon_server(Daemon):
    def run(self):
        main()

def get_conf():
    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read('telegenesys.conf')
    google_api = config.get('API','google_api')
    telegram_api = config.get('API','telegram_api')
    admins = config.get('Admins','admin')
    language = config.get('Global','language')
    voice_folder = config.get('Global','voice_folder')
    document_folder = config.get('Global','document_folder')
    return google_api,telegram_api, admins, language, voice_folder, document_folder

def handle_message(msg):
    user_id = str(msg['from']['id'])
    username = str(msg['from']['username'])
    nome = str(msg['from']['first_name'])
    try:
        sobrenome = str(msg['from']['last_name'])
    except:
        sobrenome = ""
    content_type, chat_type, chat_id = telepot.glance2(msg)

    if username in admins:
        if content_type is 'photo':
            file_id = msg['photo'][len(msg['photo'])-1]['file_id']
            bot.downloadFile(file_id, 'photos/'+file_id+'.jpg')

    else:
        bot.sendMessage(user_id, 'Desculpe '+nome+' '+sobrenome+' nao tenho permissao para falar com voce!')

def get_text_from_audio(file_name_wav,user_id):
    import speech_recognition as sr
    r = sr.Recognizer()
    with sr.WavFile(file_name_wav) as source:
        audio = r.record(source)
    try:
        command = r.recognize_google(audio,language = language)
        subprocess.check_output(['rm','-f',file_name_wav])
        bot.sendMessage(user_id, 'Request:\n'+command)
        actions(user_id,command)
    except:
        pass

def google_maps(longitude,latitude,user_id,keyword):
    query_result = google_places.nearby_search(language='pt_BR',lat_lng={'lat':latitude,'lng':longitude},keyword=keyword)
    for place in query_result.places:
        place.get_details()
        name = place.name.encode('utf-8')
        address = place.details['formatted_address'].encode('utf-8')
        phone = place.local_phone_number.encode('utf-8')
        try:
            website = place.website.encode('utf-8')
        except:
            website = ''
        bot.sendMessage(user_id, name+'\n'+address+'\n'+phone+'\n'+website)
        bot.sendLocation(user_id, place.geo_location['lat'], place.geo_location['lng'])
    bot.sendMessage(user_id,'Foi enviado todos os locais referente a: '+keyword)

def actions(user_id,command):
    command = command.lower()
    if command == '/hostnames':
        bot.sendMessage(user_id, hostname)

    elif 'mostrar' in command and 'servidores' in command:
        bot.sendMessage(user_id,'Response:\n'+hostname)

    elif 'encontrar' in command:
        command = command.split(' ',1)
        if longitude and latitude:
            google_maps(longitude,latitude,user_id,command[1])

    elif len(command.split(' ',2)) >= 3:
        command = command.split(' ',2)
        if command[0] == '/shell' and command[1] in hostname or command[1] in 'all':
            execute = command[2].split()
            system = subprocess.check_output(execute)
            bot.sendMessage(user_id, hostname+'\n\n'+system)

def main():
    bot.notifyOnMessage(handle_message)
    while 1:
        time.sleep(10)

daemon_service = daemon_server('/var/run/TeleGenesys.pid')

if len(sys.argv) >= 2:
    if sys.argv[1] == 'start':
        google_api, telegram_api, admins, language, voice_folder, document_folder = get_conf()
        google_places = GooglePlaces(google_api)
        bot = telepot.Bot(telegram_api)
        daemon_service.start()

    elif sys.argv[1] == 'stop':
        daemon_service.stop()

    elif sys.argv[1] == 'restart':
        daemon_service.restart()

    elif sys.argv[1] == 'status':
        daemon_service.is_running()
else:
    print 'Usage:',sys.argv[0],'star | stop | restart | status'
