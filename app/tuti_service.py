import flask
from flask import Flask, flash, send_file, send_from_directory, redirect, url_for, make_response, request, Blueprint, render_template
import json
from pathlib import Path
import os
import zipfile
from werkzeug.utils import secure_filename
from datetime import datetime

from flask_login import login_required, current_user
from .auto_backupdata import AutoBackupData, onTimerTicked
from app import basedir
from . import db
from .models import Action

from sqlalchemy import and_, func
import boto3


S3_SETTING_FOLDER_ROOT = 'http://s3.amazonaws.com/tuti/Setting'

# versionfile = os.path.join(basedir, 'update/latest_version.txt')
# jsonfile = os.path.join(basedir, 'database/data_storage.json')
# bin_upload_folder = os.path.join(basedir,'update/release')

jsonfile = os.path.join(S3_SETTING_FOLDER_ROOT,'setting.json')
bin_upload_folder = os.path.join(S3_SETTING_FOLDER_ROOT,'release')

ALLOWED_EXTENSIONS = {'json', 'apk'}

tuti_service = Blueprint('tuti_service', __name__)

# get setting from json:
# statistic_mode
# time_record
# apk_version
# apk_release_note


def read_json_file_from_s3():

    s3 = boto3.client('s3')

    response = s3.get_object(Bucket='tuti', Key='Setting/setting.json')
    json_body = response["Body"].read().decode()
    print("data read from amazone S3: {0}".format(json_body))
    return json_body

def write_json_file_to_s3(json_string):
    s3 = boto3.client('s3')
    # dump to amazone S3:
    json_data = json.dumps(json_string, ensure_ascii=False)
    s3.put_object(Bucket='tuti', Key='Setting/setting.json', Body=json_data)


def get_setting(param):
    jsonStr = read_json_file_from_s3()
    if jsonStr is not None:
        data_on_server = json.loads(jsonStr)
        value = data_on_server[param]
        return value
    else:
        return 0

def update_setting(param, value):  
    jsonStr = read_json_file_from_s3()
    if jsonStr is not None:
        data_on_server=json.loads(jsonStr)
        data_on_server[param] = value
        # update to zmazone server:
        write_json_file_to_s3(data_on_server)

def checkNewApkVersion(client_version):
    #version format: ver.sub.date (ex: 1.0.20200423)
    onserver_version = get_setting('apk_version')
    onserver_release_date = onserver_version.split('.')[-1]
    client_release_date = client_version.split('.')[-1]
    if float(client_release_date) < float(onserver_release_date):
        return True
    else:
        return False

def zipFile(path, zname):
    zf = zipfile.ZipFile(zname, "w")
    for dirname, subdirs, files in os.walk(path):
        zf.write(dirname)
        for filename in files:
            zf.write(os.path.join(dirname, filename))
    zf.close()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#
# insert new action:
#
def insert_new_action(jAction):
    user_id = jAction['user_id']
    results = Action.query.filter_by(user_id=user_id).all()

    is_latest = True

    insert_to =jAction['insert_to']

    if len(results) == 0:
        last_action_id = 0
    elif insert_to is None or insert_to <= 0:
        # insert to end 
        latest_action = Action.query.filter_by(user_id=user_id, is_latest_action = True).first()
        if latest_action is not None:
            last_action_id = latest_action.action_id
            latest_action.is_latest_action = False

    else:
        is_latest = False
        last_action_id = insert_to
        action = Action.query.filter_by(user_id=user_id, action_id=insert_to).first()
        if action is None:
            print("Insert new action to database failed, no action have id [{0}] found to insert".format(last_action_id))
            return { "result": "failed", "reason": "no action have id [{0}] found to insert".format(last_action_id) }
        if action.action_id == insert_to and action.is_latest_action == True:
            last_action_id = action.action_id
            action.is_latest_action = False
            is_latest = True
    
    new_action = Action(jAction['user_id'], last_action_id, jAction['action_type'], jAction['time_start'], jAction['description'], is_latest)
    db.session.add(new_action)
    db.session.commit()
  
    # find next action and change last_id of it:
    results = Action.query.filter_by(user_id=user_id, last_action_id=insert_to).all()
    if len(results) == 2:
        next_action = results[0]
        insert_action = results[-1]
        next_action.last_action_id = insert_action.action_id
        # insert_action.last_action_id = insert_to
        db.session.flush()
        db.session.commit()
        update_setting ('time_record', int(datetime.today().timestamp()*1000))
        print("Insert new action to database sucessful, position: [{0}]".format(insert_to))
        # return { "result": "success" }
        return get_db_to_json(user_id, get_setting('statistic_mode'), 0, 0)
    elif len(results) == 1: 
        #insert to end:
        update_setting ('time_record', int(datetime.today().timestamp()*1000))
        print("Insert new action to database sucessful, position: end of list")
        # return { "result": "success" }
        return get_db_to_json(user_id, get_setting('statistic_mode'), 0, 0)

    #else: error occured:
    db.session.delete(results[-1])
    db.session.commit()
    print("Insert new action to database failed, Unknown error.")
    return { "result": "failed", "reason": "error while insert new row to database" }

def modify_action(jAction):
    user_id = jAction['user_id']
    action_id = jAction['action_id']
    # last_action_id = jAction['last_action_id']
    action_type = jAction['action_type']
    time_start = jAction['time_start']
    description = jAction['description']

    action = Action.query.filter_by(user_id=user_id, action_id=action_id).first()
    if action is None:
        print("Modify action to database failed, no action have id [{0}] found.".format(action_id))
        return { "result": "failed", "reason": "no action have id [{0}] found".format(action_id) }
    # action.last_action_id = last_action_id
    action.action_type = action_type
    action.time_start = time_start
    action.description = description

    db.session.commit()
    update_setting ('time_record', int(datetime.today().timestamp()*1000))
    print("Modify action sucessful")
    # return { "result": "success" }
    return get_db_to_json(user_id, get_setting('statistic_mode'), 0, 0)

def delete_action(jAction):
    user_id = jAction['user_id']
    action_id = jAction['action_id']
    #find last id:
    action = Action.query.filter_by(user_id=user_id, action_id=action_id).first()
    if action is None:
        print("Delete action failed, action not found")
        return { "result": "failed", "reason": "action not found" }
    last_id = action.last_action_id
    
    # Set last action is latest (if needed)
    if action.is_latest_action == True:
        last_action = Action.query.filter_by(user_id=user_id, action_id=last_id).first()
        if last_action is not None:
            last_action.is_latest_action = True

    # find next id(option):
    next_action = Action.query.filter_by(user_id=user_id, last_action_id=action_id).first()
    if next_action is not None:
        next_action.last_action_id = last_id
    elif action.is_latest_action == False:
        print("Delete action failed, unknown error")
        return { "result": "failed", "reason": "unknown error" }

    db.session.delete(action)
    db.session.commit()
    update_setting ('time_record', int(datetime.today().timestamp()*1000))
    print("Delete action sucessful")
    # return { "result": "success" }
    return get_db_to_json(user_id, get_setting('statistic_mode'), 0, 0)

#for test:    
def json_to_db():
    with open(jsonfile, 'r') as json_file:
        count = 1
        data = json.load(json_file)
        action_list = data['action_list']
        for action in action_list:
            insert_new_action({ 'user_id': 0,
                                'action_type': action['action_type'],
                                'time_start': action['time_start'], 
                                'description': action['description'], 
                                'insert_to': 0})
            # print('insert {0} items to database'.format(count))
            count += 1
        return { "result": "success" }
    return { "result": "failed", "reason": "can't load json file" }


def db_list_to_json(db_list):
    json_list = []

    # sort by action life-time:
    current_action = None
    # find the latest action:
    for action in db_list:
        if action.is_latest_action == True:
            current_action = action
            break
    # back-tracking to the oldest action
    for i in range(len(db_list)):
        item = {'user_id': current_action.user_id,
                'action_id': current_action.action_id,
                'last_action_id':current_action.last_action_id,
                'action_type': current_action.action_type,
                'time_start': current_action.time_start,
                'description': current_action.description,
                'is_latest_action': current_action.is_latest_action
                }
        json_list.insert(0, item)

        if current_action.last_action_id == 0:
            break

        # find before action:
        for iter in db_list:
            if iter.action_id == current_action.last_action_id:
                current_action = iter
                break
    return json_list

def get_db_to_json(user_id = 0, statistic_mode = 1, time_from = 0, time_to = 0):

    latest_sync_time = get_setting('time_record')
    print("return sync data version: {0}".format(latest_sync_time))

    jData = {'time_record': latest_sync_time, 'action_list': []}
    
    if statistic_mode == 0:
        time_from =0
        time_to = 0
    elif statistic_mode == 1:
        # get today data:
        time_from = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0).timestamp()*1000
        time_to = datetime.now().timestamp()*1000

    if time_from > 0 and time_to > 0:
        action_list = Action.query.filter(
        and_(Action.user_id == user_id, Action.time_start >= int(time_from), Action.time_start <= int(time_to)))
    else:
        action_list = Action.query.filter_by(user_id=user_id).all()  
        
    # short actions list by timeline:
    action_list = sorted(action_list, key=lambda x: x.time_start, reverse=False) 
    jData['action_list'] = db_list_to_json(action_list)
    
    return {"result": "success", "data": jData}




 ############################################################################################
 #                                                                                          #
 #                                                                                          #
 #                                                                                          #
 ############################################################################################

@tuti_service.route('/sync-with-server', methods=['GET', 'POST'])
def sync_request():
    jsonReceived = flask.request.get_json()

    if jsonReceived is None:
        print({ "result": "failed", "reason": "no json data received"  })
        return { "result": "failed", "reason": "no json data received"  }

    print(jsonReceived)

    request_type = jsonReceived['REQUEST']
    if request_type is None:
        print({ "result": "failed", "reason": "no request found"  })
        return { "result": "failed", "reason": "no request found"  }

    # 2. Request need attachs action json
    # get action data:
    jAction = jsonReceived['DATA']
    if jAction is None:
        print({ "result": "failed", "reason": "no action data attached"  })
        return { "result": "failed", "reason": "no action data attached"  }

    if request_type == 'NEW_ACTION':           
        return insert_new_action(jAction=jAction)

    elif request_type == 'INSERT_ACTION':
        return insert_new_action(jAction=jAction)

    elif request_type == 'MODIFY_ACTION':
        return modify_action(jAction=jAction)

    elif request_type == 'DELETE_ACTION':
        return delete_action(jAction=jAction)

    elif request_type == 'GET_SYNC_DATA':
        local_version = jAction['time_record']
        latest_sync_time = get_setting('time_record')

        user_id = jAction['user_id']
        statistic_mode = jAction['statistic_mode']
        time_from = jAction['time_from']
        time_to = jAction['time_to']

        if statistic_mode is None:
            statistic_mode = 1 # auto is today view mode 
        if user_id is None:
            user_id = 0
        if time_from is None:
            time_from = 0
        if time_to is None:
            time_to = 0
        
        if local_version == latest_sync_time and statistic_mode == get_setting('statistic_mode'): 
            print("Local data version is latest, do not send anything")
            return {"result": "failed", "reason": "local data version is latest"}
        else:
            update_setting('statistic_mode', statistic_mode)
            return get_db_to_json(user_id, statistic_mode, time_from, time_to)

    print({ "result": "failed", "reason": "unknow request"  })
    return { "result": "failed", "reason": "unknow request"  }


@tuti_service.route('/update', methods=['GET', 'POST'])
def update_request():
    jsonReveived = flask.request.get_json()
    if jsonReveived is None:
        print("Can not check client version because server has been not received any version information data from client")
        return "Can not check client version!"

    client_version = jsonReveived['current_version']
    if len(client_version) > 0 and checkNewApkVersion(client_version):
        #return new version on server
        server_version = get_setting('apk_version')
        release_note = get_setting('apk_release_note')

        print(f"App version on client is out of date, send update link to client! (OnClient: {client_version}/OnServer: {server_version})")
        return { "result": "success", "server_version": server_version, "release_note": release_note}
    # else
    print(f"App version on client is latest! (OnClient: {client_version})")
    return { "result": "failed", "reason": "client version is latest" }

@tuti_service.route('/download', methods=['GET', 'POST'])
@tuti_service.route('/download-apk', methods=['GET', 'POST'])
def download_apk():
    # return send_file(os.path.join(bin_upload_folder,"app-release.apk"), as_attachment=True)
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('get_object', Params = {'Bucket': 'tuti', 'Key': 'Setting/release/app-release.apk'}, ExpiresIn = 100)
    return redirect(url, code=302)


@tuti_service.route('/backup-database', methods=['GET', 'POST'])
@login_required
def download_backup():
    zipFile('database','tuti-backup.zip')
    return send_file(os.path.join(basedir,"tuti-backup.zip"), as_attachment=True)


@tuti_service.route('/upload-bin', methods=['GET', 'POST'])
@login_required
def upload_bin():
    if request.method == 'POST':
        # get version text is fillted:    
        text = request.form['text']
        version = text.upper()
        release_note = "Fix some issue"

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            # file.save(os.path.join(bin_upload_folder, filename))

            client = boto3.client('s3')

            filename = secure_filename(file.filename)  # This is convenient to validate your filename, otherwise just use file.filename

            client.put_object(Body=file,
                            Bucket='tuti',
                            Key='Setting/release/app-release.apk',
                            ContentType=request.mimetype)

            #save latest version on text file:
            update_setting('apk_version', version)
            update_setting('apk_release_note', release_note)
            
            flash('Your apk file is uploaded!')
            return redirect(url_for('main.index'))

    return render_template('upload.html')


@tuti_service.route('/show-actions')
def show_all_actions():
    return render_template('show_all.html',
        action_list=Action.query.filter_by(user_id=0).all()
    )

