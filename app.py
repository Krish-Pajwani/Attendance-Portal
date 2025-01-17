from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(10), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)


@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    professor = Professor.query.filter_by(email=email, password=password).first()
    if professor:
        session['professor_id'] = professor.id
        return redirect(url_for('dashboard'))
    else:
        return 'Invalid credentials, please try again.'

@app.route('/dashboard')
def dashboard():
    if 'professor_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/students', methods=['GET', 'POST', 'DELETE'])
def manage_students():
    if request.method == 'GET':
        division = request.args.get('division')
        students = Student.query.filter_by(division=division).all()
        return jsonify([{'id': s.id, 'name': s.name} for s in students])

    elif request.method == 'POST':
        name = request.form['name']
        division = request.form['division']
        new_student = Student(name=name, division=division)
        db.session.add(new_student)
        db.session.commit()
        return 'Student added successfully!'

    elif request.method == 'DELETE':
        student_id = request.form['id']
        student = Student.query.get(student_id)
        if student:
            db.session.delete(student)
            db.session.commit()
            return 'Student removed successfully!'
        else:
            return 'Student not found.'

@app.route('/attendance', methods=['POST'])
def mark_attendance():
    student_id = request.form['student_id']
    date = request.form['date']
    status = request.form['status']

    new_attendance = Attendance(student_id=student_id, date=datetime.strptime(date, '%Y-%m-%d'), status=status)
    db.session.add(new_attendance)
    db.session.commit()
    return 'Attendance marked successfully!'

@app.route('/attendance-summary')
def attendance_summary():
    if 'professor_id' not in session:
        return redirect(url_for('login_page'))

    month = request.args.get('month')
    students = Student.query.all()
    summary = {}

    for student in students:
        attendance_records = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.date.like(f'{month}-%')
        ).all()
        present_days = sum(1 for a in attendance_records if a.status == 'Present')
        absent_days = sum(1 for a in attendance_records if a.status == 'Absent')
        summary[student.name] = {
            'present_days': present_days,
            'absent_days': absent_days
        }

    return render_template('attendance_summary.html', month=month, summary=summary)

if __name__ == '__main__':
    db.create_all() 
    app.run(debug=True)
