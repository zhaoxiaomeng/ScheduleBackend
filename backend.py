import json

from flask import Flask, request, jsonify
import csv
from workalendar.asia import China
from datetime import datetime, timedelta, date

app = Flask(__name__)

tokens = {
    'admin': {
        'token': 'admin-token'
    },
    'editor': {
        'token': 'editor-token'
    }
}

users = {
    'admin-token': {
        'roles': ['admin'],
        'introduction': 'I am a super administrator',
        'avatar': 'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif',
        'name': 'Super Admin'
    }
}


@app.route('/user/login', methods=['POST'])
def user_login():
    username = json.loads(request.get_data())['username']
    token = tokens[username]
    return jsonify({"code": 20000, "data": token})


@app.route('/user/info', methods=['GET'])
def user_info():
    token = request.args.get('token')
    info = users[token]
    return jsonify({"code": 20000, "data": info})


@app.route('/user/logout', methods=['POST'])
def user_logout():
    return jsonify({"code": 20000, "data": "success"})


@app.route('/people/list', methods=['GET'])
def people_list():

    type = request.args.get('type')
    limit = int(request.args.get('limit'))
    page = int(request.args.get('page'))-1

    peoplelist = []
    reader = None
    count = 0

    print (page,limit,count)
    if type == 'weekday':
        with open('工作日.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                peoplelist.append({'id': count, 'name': row[0], 'sex': row[1], 'unit': row[2]})
                count += 1
    elif type == 'weekend':
        with open('周末.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                peoplelist.append({'id': count, 'name': row[0], 'sex': row[1], 'unit': row[2]})
                count += 1
    elif type == 'holiday':
        with open('节假日.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                peoplelist.append({'id': count, 'name': row[0], 'sex': row[1], 'unit': row[2]})
                count += 1


    return jsonify({"code": 20000, "data": {"total": len(peoplelist), "items": peoplelist[page*limit:page*limit+limit]}})



def get_schedule_index():
    with open('上次排班索引.csv', 'r') as f:
        workday_index, weekendday_index, holiday_index = f.readline().split(',')
        print(workday_index ,weekendday_index ,holiday_index)
        return int(workday_index),int(weekendday_index),int(holiday_index)

def set_schedule_index( workday_index ,weekendday_index ,holiday_index):
    print(workday_index ,weekendday_index ,holiday_index)
    with open('上次排班索引.csv','w') as f:
        writer = csv.writer(f)
        writer.writerow([workday_index ,weekendday_index ,holiday_index])

@app.route('/schedule/new', methods=['GET'])
def schedule_new():
    today = date.today()
    year = eval(str(today).split("-")[0])
    cal = China()

    schedule_list = []
    workday_index ,weekendday_index ,holiday_index = get_schedule_index()

    holiday_list = []
    for i in cal.holidays(year):
        day = i[0].strftime('%Y-%m-%d')
        holiday_list.append(day)

    workday_people_list = []
    with open('工作日.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            workday_people_list.append({'name': row[0], 'sex': row[1], 'unit': row[2]})

    weekendday_people_list = []
    with open('周末.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            weekendday_people_list.append({'name': row[0], 'sex': row[1], 'unit': row[2]})

    holiday_people_list = []
    with open('节假日.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            holiday_people_list.append({'name': row[0], 'sex': row[1], 'unit': row[2]})

    schedule_last_day = today
    with open('排班表.csv', 'r') as f:
        schedule_last_day = datetime.strptime(f.readlines()[-1].split(',')[0], "%Y-%m-%d")

    for i in range(1, 30):
        schedule_day = schedule_last_day + timedelta(days=i)
        schedule_day_str = schedule_day.strftime('%Y-%m-%d')
        schedule_people = None
        if schedule_day_str in holiday_list:
            print(schedule_day)
            schedule_people = holiday_people_list[holiday_index % len(holiday_people_list)]
            holiday_index = (holiday_index + 1) % len(holiday_people_list)
            schedule_list.append([schedule_day_str,'节假日',schedule_people['name'],schedule_people['sex'],schedule_people['unit']])
        else:
            if cal.is_working_day(schedule_day):
                schedule_people = workday_people_list[workday_index % len(workday_people_list)]
                schedule_list.append([schedule_day_str,'工作日',schedule_people['name'],schedule_people['sex'],schedule_people['unit']])
                workday_index = (workday_index + 1) % len(workday_people_list)

            else:
                schedule_people = weekendday_people_list[weekendday_index % len(weekendday_people_list)]
                weekendday_index = (weekendday_index + 1) % len(weekendday_people_list)
                schedule_list.append([schedule_day_str,'周末',schedule_people['name'],schedule_people['sex'],schedule_people['unit']])

    with open(r'排班表.csv', mode='a', newline='') as f:
        writer = csv.writer(f)
        for schedule_item in schedule_list:
            writer.writerow(schedule_item)
    set_schedule_index(workday_index,weekendday_index,holiday_index)
    return jsonify({"code": 20000, "data": {"total": len(schedule_list), "items": schedule_list}})

@app.route('/schedule/list', methods=['GET'])
def schedule_list():
    schedule_list = []
    with open('排班表.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            schedule_list.append({'date': row[0],'type':row[1],'name': row[2],'sex': row[3],'unit': row[4]})
    return jsonify({"code": 20000, "data": {"total": len(schedule_list), "items": schedule_list}})



@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run()
