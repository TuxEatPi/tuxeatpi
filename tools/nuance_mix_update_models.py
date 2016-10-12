#!/usr/bin/env python

import sys
import json
import time
import glob

import requests
import os

MODEL_BASE_NAME = "tuxeatpi"

langs = {"certified": ["en_US", "en_AU", "en_GB"],
         "beta": ["fr_FR", "fr_CA", "it_IT", "pt_BR", "pt_PT", "es_ES"],
         "alpha": ["nl_NL", "de_DE", "ja_JP", "ko_KR", "zh_CN", "sv_SE"],
         }


def _login():
    # Login
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    username = input("Username: ")
    password = input("Mix password: ")
    data_login = {"username": username,
                  "password": password}
    result = requests.post("https://developer.nuance.com/mix/nlu/bolt/login", data=json.dumps(data_login), headers=headers)
    if not result.json().get('status', False):
        raise Exception("Can not connect")
    return result.cookies

def _login1():
    # Login
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    username = input("Username: ")
    password = input("Mix password: ")
    data_login = {"form": "login",
                  "command": "login",
                  "next": "",
                  "username": username,
                  "password": password,
                  "login": "",
                  }
    params = {"task": "login"}
    url = "https://developer.nuance.com/public/index.php"
    result = requests.post(url, params=params, data=data_login, allow_redirects=True)
    # TODO do it
    #if not result.json().get('status', False):
    #    raise Exception("Can not connect")
    return result.cookies

def _create_models(langs,  cookies):
    # Login
    print("Create models")
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    for lang in langs:
        model_name = MODEL_BASE_NAME + "-" + lang
        data = {"name": model_name, "domains": [] , "locale": lang}
        res = requests.post("https://developer.nuance.com/mix/nlu/api/v1/projects",
                      data=json.dumps(data),
                      headers=headers,
                      cookies=cookies)
        time.sleep(2)

def _get_models(cookies):
    # models
    result = requests.get("https://developer.nuance.com/mix/nlu/api/v1/projects", cookies=cookies)
    models = {}
    for model in result.json().get('data', []):
        if model['name'].startswith(MODEL_BASE_NAME):
            models[model['locale']] = str(model['id'])
            print("{} = {} - {}".format(model['id'], model['name'], model['locale']))

    return models


def _get_trsx_files(langs):
    trsx_files = {}
    main_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    for file_name in glob.iglob(main_folder + '/**/*.trsx', recursive=True):
        lang = os.path.basename(file_name)[:-5]
        if lang in langs:
           trsx_files[file_name] = lang
    return trsx_files
    

def update():
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    langs = ["en-US", "fr-FR"]
    trsx_files = _get_trsx_files(langs)
    # login
    cookies = _login()
    # get models
    models = _get_models(cookies)
    if len(models) == 0:
        _create_models(langs, cookies)
        while len(langs) > len(models):
            models = _get_models(cookies)
            time.sleep(2)

    # Send file
    for trsx_file, lang in trsx_files.items():
        print("Sending: {}".format(trsx_file))
        model_id = models[lang.replace("-", "_")]
        url = "https://developer.nuance.com/mix/nlu/api/v1/data/{}/import".format(model_id)
        files = {'file': open(trsx_file, 'rb')}
        result = requests.post(url, files=files, cookies=cookies)

    # Save
    for model_lang, model_id in models.items():
        print("Saving: {}".format(model_lang))
        url = "https://developer.nuance.com/mix/nlu/api/v1/project/{}".format(model_id)
        requests.put(url, cookies=cookies)
        time.sleep(1)

    time.sleep(10)
    # Train model
    for model_lang, model_id in models.items():
        print("Training: {}".format(model_lang))
        url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/annotations/train".format(model_id)
        requests.post(url, cookies=cookies)
        time.sleep(1)
    
    # TODO wait for 
    time.sleep(30)

    # Create version
    for model_lang, model_id in models.items():
        print("Versionning: {}".format(model_lang))
        url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/engine".format(model_id)
        #url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/engine?notes=&type=Default&with_asr=true".format(model_id)
        params = {"notes": "", "type": "Default", "with_asr": "true"}
        requests.post(url, params=params, cookies=cookies)
        time.sleep(1)

    # TODO wait for 
    time.sleep(30)

    attach(cookies)

def attach(cookies=None):
    if cookies is None:
        cookies = _login()
    # attach version to sandboxapp 
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    models = _get_models(cookies)
    url = "https://developer.nuance.com/mix/nlu/bolt/applications"
    params = {"configurations": "true"}
    result = requests.get(url, params=params, cookies=cookies)
    app_id = None
    for app in result.json().get("applications"):
        if app['name'] == 'Sandbox App':
            app_id = app['id']
            break
    # nmaid
    url = "https://developer.nuance.com/mix/nlu/bolt/nmaids"
    result = requests.get(url, cookies=cookies)
    nmaids = [app['nmaid'] for app in result.json()['data'] if app['app_id'] == app_id]
    if len(nmaids) < 1:
        raise Exception("Can not get nmaid")
    nmaid = nmaids[0]

    for model_lang, model_id in models.items():
        print("attaching: {}".format(model_lang))
        data = {"nmaid": nmaid,
                "project_id": model_id, "tag": "master"}
        url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations".format(app_id)
        result = requests.post(url, data=json.dumps(data), cookies=cookies, headers=headers)
        conf_id = result.json().get("id")
        if conf_id is None:
            continue

        data = {"page": "/model/{}/publish".format(model_id),
                "query_params": {},
                "host":"developer.nuance.com",
                "port":443,
                "protocol":"https",
                "category":"publish",
                "action":"associate-to-app",
                "label":"finish",
                "value":""}
        url = "https://developer.nuance.com/mix/nlu/bolt/ubt"
        result = requests.post(url, data=json.dumps(data), cookies=cookies, headers=headers)

        url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations/{}/settings".format(app_id, conf_id)
        result = requests.put(url, data=json.dumps({}), cookies=cookies, headers=headers)

        url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations/{}/models".format(app_id, conf_id)
        data = [{"model_id": "{}".format(model_id)}] 
        result = requests.put(url, data=json.dumps(data), cookies=cookies, headers=headers)

def delete():
    cookies = _login
    # Detele model
    url = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    request.delete(url, cookies=cookies)

if __name__ == "__main__":
    update()
