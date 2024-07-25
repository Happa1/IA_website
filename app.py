import os
from datetime import datetime, timedelta, time

from flask import Flask, render_template, request, redirect, url_for, make_response
import re
from tools import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
# app.permanent_session_lifetime=timedelta(minutes=30)

@app.route('/', methods=['GET','POST'])
def hello_world():  # put application's code here
    print()
    db_connection = DatabaseWorker("IA_database")
    db_connection.close()
    return render_template('home.html')

@app.route('/pre_app')
def pre_app():
    return render_template('pre_appointment.html')

@app.route('/login',methods=['GET','POST'])
def login():
    db_connection = DatabaseWorker("IA_database")
    login_err = False
    if request.method =='POST':
        patient_id = request.form.get('patient_id')
        birthday = str(request.form.get('birthday'))
        print(patient_id)
        print(type(birthday))
        results = db_connection.search(query="""
        SELECT * FROM patients""", multiple=True)
        for row in results:
            signature=row[1]
            hash_text = f"patient_id_number{patient_id}, birthday{birthday}"
            valid = check_hash(hashed_text=signature, text=hash_text)
            if valid:
                if row[8]==1: #patient page (appointment)
                    user_id = row[0]
                    session['user_id'] = user_id
                    return redirect(url_for('appointment'))
                if row[8] == 2: #owner page
                    user_id = row[0]
                    session['user_id'] = user_id
                    return redirect(url_for('owner_home'))
                if row[8] == 3: #staff page
                    user_id = row[0]
                    session['user_id'] = user_id
                    return redirect(url_for('staff_home'))

            else:
                login_err=True
                print("login error")
    db_connection.close()
    return render_template('login.html', login_err=login_err)

@app.route('/register',methods=['GET','POST'])
def register():
    db_connection = DatabaseWorker("IA_database")
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        match = re.match('[A-Za-z0-9._+]+@[A-Za-z]+.[A-Za-z]', email)
        sex = request.form.get('sex')
        today = datetime.now().strftime('%Y%m%d')
        birthday = request.form.get('birthday')
        str_birth = birthday.replace('-', '')
        print(f"str_birth{str_birth}")
        age = (int(today) - int(str_birth)) // 10000
        allergy = request.form.get('allergy')
        valid = True
        email_err = False

        if match is None:
            email_err=True
            valid = False
            print('email error')
            db_connection.close()
            return render_template('register.html', email_err=email_err)

        if valid:
            hash_birth = str_birth[4:]
            last_id_query = f"""
                SELECT max(id) FROM patients"""
            last_id = db_connection.search(query=last_id_query, multiple=False)[0]
            if last_id==None:
                last_id=0
            patient_id = str(last_id+1).zfill(6)
            print(patient_id)
            print(hash_birth)
            hash_text = f"patient_id_number{int(patient_id)}, birthday{int(hash_birth)}"
            hash = make_hash(hash_text)
            query = f"""INSERT INTO patients (signature,name,sex,age,email,birthday,allergy, type)
                            values ('{hash}','{name}','{sex}','{age}','{email}','{birthday}','{allergy}',1);
                            """
            db_connection.run_query(query=query)
            db_connection.close()
            return redirect(url_for('appointment'))

    db_connection.close()
    return render_template('register.html')

@app.route('/appointment', methods=['GET','POST'])
def appointment():
    user_id = session['user_id']
    db_connection = DatabaseWorker("IA_database")

    # 現在の時刻を取得
    current_time = datetime.now().time()

    # 午後5時から深夜12時の間かどうかを確認
    app_start_time = time(17, 0)  # 午後5時
    app_end_time = time(23, 59)   # 深夜12時

    if (app_start_time <= current_time <= app_end_time):
        app_date = (datetime.today() + timedelta(days=1)).date()
    else:
        app_date=datetime.today().date()

    appointment_slot=db_connection.search(query=f"""
    SELECT * FROM appointments""", multiple=True)

    return render_template('appointment.html', appointments=appointment_slot, app_date=app_date)

@app.route('/survey/<int:appointment_id>/<app_date>', methods=['GET','POST'])
def survey(appointment_id, app_date):
    user_id = session['user_id']
    db_connection = DatabaseWorker("IA_database")
    print(app_date)
    print(type(app_date))
    if request.method=="POST":
        print('here')
        patient_id = user_id
        symptom = request.form.get('symptom')
        temperature1 = request.form.get('temperature1')
        temperature2 = request.form.get('temperature2')
        temperature = float(f"{temperature1}.{temperature2}")
        note = request.form.get('note')
        print('here')
        time= db_connection.search(query=f"""
        SELECT start_time, end_time FROM appointments WHERE id = {appointment_id}""", multiple=False)

        query=f"""
        INSERT INTO record ('patient_id','date','start_time','end_time','symptom','temperature','note')
        values ({user_id},'{app_date}','{time[0]}','{time[1]}','{symptom}','{temperature}','{note}')
        """
        db_connection.run_query(query=query)

        record_id_query = f"""
        SELECT id FROM record WHERE patient_id = {patient_id} AND start_time='{time[0]}'
        """
        record_id = db_connection.search(query=record_id_query, multiple=False)[0]
        print(record_id)
        query_appointment=f"""
        UPDATE appointments 
        SET patient_id={patient_id}, survey_id={record_id}, date={app_date} WHERE id={appointment_id}
        """
        db_connection.run_query(query=query_appointment)
        db_connection.close()
        return redirect(url_for('appointment_check'))

    print('error at survey')
    db_connection.close()
    return render_template('survey.html',appointment_id=appointment_id, app_date=app_date)

@app.route('/appointment_check')
def appointment_check():
    return render_template('appointment_check.html')

@app.route('/')



@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html')

if __name__ == '__main__':
    app.run()
