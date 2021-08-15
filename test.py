import json
from datetime import datetime

from app import app
from app import tuti_service

# 
# 
# 

now = int(datetime.today().timestamp()*1000)

jAction = { 
    "user_id": 0, 
    "action_id": 180, 
    "last_action_id": 2, 
    "action_type": 3, 
    "time_start": now, 
    "description": "tắm mát",
    'insert_to': 0, #insert to possition 2.
     }



# test POST/RECECVED service:
import requests

url = "http://127.0.0.1:5000/sync-with-server"

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

# data = {
#         'client': 'tuan.na3', 
#         'REQUEST': 'GET_SYNC_DATA',
#         'DATA': {'time_record': 1591710556136,'user_id': 0, 'statistic_mode': 1, 'time_from': 1591635600918, 'time_to': 1591712933918} }


data = {
        'client': 'tuan.na3', 
        'REQUEST': 'NEW_ACTION',
        'DATA': { 
                "user_id": 0, 
                "action_id": 180, 
                "last_action_id": 2, 
                "action_type": 3, 
                "time_start": now, 
                "description": "tắm mát",
                'insert_to': 0 } 
                }

response = requests.post(url, data=json.dumps(data), headers=headers)
print (response.text)

