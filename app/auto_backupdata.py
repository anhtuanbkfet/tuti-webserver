from threading import Timer, Thread, Event
from datetime import datetime
import time
from pathlib import Path
import json


#
# timeInterval: secounds
# onTimeTicker: function to run on time ticker.
#

global isBackupThreadRunning
isBackupThreadRunning = False

class AutoBackupData():
    def __init__(self, timeInterval, onTimeTicker):
        global isBackupThreadRunning
        self.timeInterval = timeInterval
        self.onTimeTicker = onTimeTicker
        self.thread = Timer(self.timeInterval, self.handle_function)
        isBackupThreadRunning = False

    def handle_function(self):
        self.onTimeTicker()
        self.thread = Timer(self.timeInterval, self.handle_function)
        self.thread.start()

    def start(self):
        global isBackupThreadRunning
        if isBackupThreadRunning == False:
            print(f"Start thread to run auto backup data on server, time interval to backup: {self.timeInterval/3600} hours")
            isBackupThreadRunning = True
            self.thread.start()

    def cancel(self):
        global isBackupThreadRunning
        print(f"Stop auto backup data thread on server")
        isBackupThreadRunning = False
        self.thread.cancel()



def checkTimeInDay(datetime, year, month, day):
    return datetime.year == year and datetime.month ==month and datetime.day == day

def onTimerTicked():
    today = datetime.today()
    print(f"Start auto backup data on server....")

    my_file = Path("data_storage.json")
    if my_file.exists():
        with open("data_storage.json", 'r') as json_file:
            data = json.load(json_file)

            data_today = json.loads('{"time_record": 0, "action_list":[]}')
            data_today['time_record'] = today.timestamp()

            for action in data['action_list']:
                timeStart = action['time_start']
                timeStart = float(timeStart)
                timeStart = datetime.fromtimestamp(timeStart / 1000)

                timeEnd = action['time_end']
                timeEnd = float(timeEnd)
                if timeEnd > 0:
                    timeEnd = datetime.fromtimestamp(timeEnd / 1000)
                else:
                    timeEnd = datetime.now()

                if checkTimeInDay(timeStart, today.year, today.month, today.day)  or  checkTimeInDay(timeEnd, today.year, today.month, today.day):
                    data_today['action_list'].append(action)

                # print(f"Action time start: {timeStart.day}/{timeStart.month}/{timeStart.year}  {timeStart.hour}:{timeStart.minute}:{timeStart.second}")
                # print(f"Action time end: {timeEnd.day}/{timeEnd.month}/{timeEnd.year}  {timeEnd.hour}:{timeEnd.minute}:{timeEnd.second}")
                # print(f"checkTimeInDay: {checkTimeInDay(timeStart, 2020,4,24)}")
            
            # check action list is empty?
            if len(data_today['action_list']) < 2:
                print("Today we have no action to save!")
                return
            # else
            # dump to file backup:
            filename = "{:4d}-{:02d}-{:02d}".format(today.year, today.month, today.day)
            with open(f"backup/{filename}.json", 'w') as json_file:
                json.dump(data_today, json_file)
                print(f"Auto backup data on server completed, time to backup: {today.replace(microsecond=0).isoformat(' ')}, file name: backup/{filename}.json")


# for test:
# onTimerTicked()
# backup = AutoBackupData(5, onTimerTicked)
# backup.start()
