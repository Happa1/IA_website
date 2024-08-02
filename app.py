import os
from datetime import datetime, timedelta, time
from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask, render_template, request, redirect, url_for, make_response
import re
from tools import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
# app.permanent_session_lifetime=timedelta(minutes=30)

@app.route('/', methods=['GET','POST'])
def hello_world():  # put application's code here
    db_connection = DatabaseWorker("IA_database")
    appointment_day_set()
    query = f"""
        SELECT * FROM news"""
    news = db_connection.search(query=query, multiple=True)
    db_connection.close()

    return render_template('home.html', news=news)

@app.route('/select_app')
def select_app():
    return render_template('appointment_select.html')

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
        patient_id = user_id
        symptom = request.form.get('symptom')
        temperature = request.form.get('temperature1')
        note = request.form.get('note')
        time= db_connection.search(query=f"""
        SELECT start_time, end_time FROM appointments WHERE id = {appointment_id}""", multiple=False)

        query=f"""
        INSERT INTO record (patient_id, date, start_time, end_time, symptom, temperature, note)
        values ({user_id},'{app_date}','{time[0]}','{time[1]}','{symptom}','{temperature}','{note}')
        """
        db_connection.run_query(query=query)

        record_id_query = f"""
        SELECT id FROM record WHERE patient_id = {patient_id} AND start_time='{time[0]}'
        """
        record_id = db_connection.search(query=record_id_query, multiple=False)[0]

        query_appointment=f"""
        UPDATE appointments 
        SET patient_id={patient_id}, survey_id={record_id}, date="{app_date}" WHERE id={appointment_id}
        """
        print(app_date)
        print(type(app_date))
        db_connection.run_query(query=query_appointment)
        db_connection.close()
        return redirect(url_for('appointment_check'))

    print('error at survey')
    db_connection.close()
    return render_template('survey.html',appointment_id=appointment_id, app_date=app_date)

@app.route('/appointment_check')
def appointment_check():
    return render_template('appointment_check.html')

@app.route('/staff_register',methods=['GET','POST'])
def staff_register():
    db_connection = DatabaseWorker("IA_database")
    if request.method == "POST":
        uname = request.form.get('uname')
        password = request.form.get('psw')
        conf_password = request.form.get('psw_conf')

        valid = True
        user_err=False
        psw_err=False
        psw_cnf_err = False

        staff_table = db_connection.search(query="SELECT * FROM staff", multiple=True)

        for row in staff_table:
            if row[1]==uname:
                user_err=True
                print("the user name already exist")
                valid=False
                break

        if len(password)<8:
            psw_err=True
            valid = False
        if password!=conf_password:
            psw_cnf_err=True
            valid = False

        hash_text=f"name{uname}, pass{password}"
        hash=make_hash(hash_text)

        if valid:
            query = f"""INSERT INTO staff (name,signature)
            values ('{uname}','{hash}');
            """
            db_connection.run_query(query=query)
            db_connection.close()
            return redirect(url_for('staff_login'))

        db_connection.close()
        return render_template('staff_register.html', psw_err=psw_err, psw_cnf_err=psw_cnf_err, user_err=user_err)

    db_connection.close()
    return render_template('staff_register.html')

@app.route('/staff_login',methods=['GET','POST'])
def staff_login():
    db_connection = DatabaseWorker("IA_database")
    login_err = False
    if request.method == 'POST':
        uname = request.form.get('uname')
        password = request.form.get('psw')
        results = db_connection.search(query="""SELECT * FROM staff""", multiple=True)
        for row in results:
            signature = row[2]  # hash text
            hash_text = f"name{uname}, pass{password}"
            valid = check_hash(hashed_text=signature, text=hash_text)
            if valid:
                user_id = row[0]
                session['user_id'] = user_id
                username=db_connection.search(query=f"""
                SELECT name FROM staff WHERE id={user_id}""")[0]
                return redirect(url_for('owner_home', username=username))
            else:
                login_err = True
    db_connection.close()
    return render_template('staff_login.html', login_err=login_err)

@app.route('/owner_home')
def owner_home():
    return render_template('staff_home.html')

@app.route('/appointment_view')
def appointment_view():
    db_connection = DatabaseWorker("IA_database")
    query=f"""SELECT * FROM appointments
    """
    appointment_data=db_connection.search(query=query, multiple=True)

    current_time = datetime.now().time()
    app_start_time = time(17, 0)  # 午後5時
    app_end_time = time(23, 59)   # 深夜12時
    if (app_start_time <= current_time <= app_end_time):
        app_date = (datetime.today() + timedelta(days=1)).date()
    else:
        app_date=datetime.today().date()

    appointment_list = []
    index=0
    for a in appointment_data:
        appointment_list.append(list(a))
        if a[1] != 0:
            patient_name = db_connection.search(query=f"SELECT name FROM patients WHERE id = {a[1]}", multiple=False)[0]
            appointment_list[index].append(patient_name)
            index += 1
        else:
            appointment_list[index].append('None')
            index += 1
    print(appointment_list)
    return render_template('appointment_view.html',appointments=appointment_list, app_date=app_date)

@app.route('/app_edit/<int:record_id>', methods=['GET','POST'])
def app_edit(record_id):
    db_connection = DatabaseWorker("IA_database")
    record = db_connection.search(query=f"""
    SELECT * FROM record WHERE id={record_id}""")
    if request.method == "POST":
        new_symptom = request.form.get('symptom')
        new_temperature = request.form.get('temperature1')
        new_note = request.form.get('note')
        query = f"""
                UPDATE record SET symptom ='{new_symptom}',temperature={new_temperature},note='{new_note}'
                """
        db_connection.run_query(query=query)
        return redirect(url_for('appointment_view'))
    return render_template('staff_appointment_edit.html', record=record)

@app.route('/app_cancel/<int:appointment_id>')
def app_cancel(appointment_id):
    db_connection = DatabaseWorker("IA_database")
    print(appointment_id)
    record_id=db_connection.search(query=f"""
    SELECT survey_id FROM appointments WHERE id={appointment_id}""", multiple=False)[0]
    db_connection.run_query(query=f"""
    DELETE FROM record WHERE id={record_id}""")
    db_connection.run_query(query=f"""
    UPDATE appointments SET patient_id=0, survey_id=0 WHERE id ={appointment_id} """)
    db_connection.close()
    return redirect(url_for('appointment_view'))

@app.route('/record_detail/<int:record_id>/<int:patient_id>', methods=['GET','POST'])
def record_detail(record_id,patient_id):
    db_connection = DatabaseWorker("IA_database")
    query=f"""
    SELECT * FROM record WHERE id={record_id}"""
    app_detail=db_connection.search(query=query, multiple=False)
    patient_data=db_connection.search(query=f"""
    SELECT * FROM patients WHERE id={patient_id}""",multiple=False)
    return render_template('staff_record_detail.html', app_detail=app_detail, patient=patient_data)

@app.route('/patient_search',methods=['GET','POST'])
def patient_search():
    db_connection = DatabaseWorker("IA_database")
    record_list = []
    if request.method == "POST":
        id = request.form.get('search_id')
        print(id)
        date = request.form.get('search_date')
        print(date)
        no_record = False
        if id=="" and date=="":
            print('enter something')
            no_record=True
        elif id!="" and date=="":
            records=db_connection.search(f"""
            SELECT * FROM record WHERE patient_id={int(id)}""", multiple=True)
            if not records:
                no_record=True
                print(f"No records found for id: {id}")
        elif id=="" and date!="":
            records = db_connection.search(f"""
                        SELECT * FROM record WHERE date='{date}'""", multiple=True)
            if not records:
                no_record=True
                print(f"No records found for date: {date}")
        else:
            records = db_connection.search(f"""
                                    SELECT * FROM record WHERE patient_id={int(id)} AND date='{date}'""", multiple=True)
            if not records:
                no_record=True
                print(f"No records")

        if no_record == False:
            for r in records:
                r=list(r)
                print(r)
                patient_id= str(r[1]).zfill(6)
                print(r[1])
                patient_name=db_connection.search(query=f"""
                SELECT name FROM patients WHERE id={r[1]}""",multiple=False)[0]
                r.append(patient_id) #id 10
                r.append(patient_name) #id 11
                record_list.append(r)
            print(record_list)
        return render_template('staff_patient_search.html', no_record=no_record, records=record_list)

    return render_template('staff_patient_search.html')

@app.route('/patient_detail/<int:patient_id>')
def patient_detail(patient_id):
    db_connection = DatabaseWorker("IA_database")
    patient_data = db_connection.search(query=f"""
        SELECT * FROM patients WHERE id={patient_id}""", multiple=False)
    patient_record = db_connection.search(query=f"""
    SELECT * FROM record WHERE patient_id = {patient_id}""",multiple=True)
    print(patient_record)
    return render_template('patient_detail.html',patient_data=patient_data, patient_record=patient_record)

@app.route('/owner_news')
def owner_news():
    db_connection = DatabaseWorker("IA_database")
    news = db_connection.search(query=f"""
    SELECT * FROM news""", multiple=True)
    return render_template('staff_news_all.html', news=news)

@app.route('/news_create',methods=['GET','POST'])
def news_create():
    db_connection = DatabaseWorker("IA_database")
    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        type = request.form.get('type')
        date = datetime.now().strftime('%Y-%m-%d')

        query=f"""
        INSERT INTO news ('date','title','content','type')
        values ('{date}','{title}','{content}','{type}')"""

        db_connection.run_query(query=query)
        db_connection.close()
        return redirect(url_for('owner_news'))

    return render_template('staff_news_create.html')

@app.route('/news_edit/<int:news_id>',methods=['GET','POST'])
def news_edit(news_id):
    db_connection = DatabaseWorker("IA_database")
    news_data=db_connection.search(query= f"""
    SELECT * FROM news where id={news_id}""", multiple=False)
    if request.method == "POST":
        new_title = request.form.get('title')
        new_content = request.form.get('content')
        new_type = request.form.get('type')
        query=f"""
        UPDATE news SET title='{new_title}',content='{new_content}',type='{new_type}' WHERE id = {news_id}"""
        db_connection.run_query(query=query)
        db_connection.close()
        return redirect(url_for('owner_news'))
    db_connection.close()
    return render_template('staff_news_edit.html', news=news_data)

@app.route('/news_delete/<int:news_id>/delete',methods=['GET','POST'])
def news_delete(news_id):
    db_connection = DatabaseWorker("IA_database")
    query=f"""
    DELETE FROM news where id={news_id}"""
    db_connection.run_query(query=query)
    db_connection.close()
    return redirect(url_for('owner_news'))

@app.route('/medical_info')
def medical_info():
    return render_template('medical_info.html')

@app.route('/clinic_info')
def clinic_info():
    return render_template('clinic_info.html')

@app.route('/greetings')
def greetings():
    return render_template('greetings.html')

@app.route('/news/<int:news_id>')
def news(news_id):
    db_connection = DatabaseWorker("IA_database")
    query=f"""
    SELECT * FROM news"""
    news=db_connection.search(query=query,multiple=True)
    return render_template('news.html', news=news)

@app.route('/news_all')
def news_all():
    db_connection = DatabaseWorker("IA_database")
    return render_template('news_all.html')

@app.route('/access')
def access():
    return render_template('access.html')


@app.route('/pre_password')
def pre_password():
    return render_template('pre_password_edit.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html')

if __name__ == '__main__':
    app.run()
