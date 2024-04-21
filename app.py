from flask import Flask, render_template,request,flash,redirect,url_for,session,flash,jsonify
from flask_sqlalchemy import  SQLAlchemy
from datetime import datetime,timedelta,timezone
import smtplib
from email.mime.text import MIMEText
import random
import string
from flask_mail import Mail, Message
from urllib.parse import urlparse
from flask_migrate import Migrate
import paypalrestsdk



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms-system.db'
db= SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SECRET_KEY'] = 'your_secret_key_here'
# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'rajeshnrajeshn567@gmail.com'
app.config['MAIL_PASSWORD'] = 'ggyo umjk hqyo hjpt'
app.config['MAIL_DEFAULT_SENDER'] = 'rajeshnrajeshn567@gmail.com'
mail = Mail(app)

paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "AU62RKWjh4rT2f41ItdXLUfOs3LDojTwMnZuQaFIbRWQUz79RMr3Wune77BosNzWO_6p5JCp73T6xV9n",
  "client_secret": "EMQxQ1wPDr-VmZPQwJoCKcuZvrdWb4sHdhYPputGNr4-rNyfDTlg1DCGjhLw2UOeUfY44yBube_caEhX" })
# Define routes and views
class Teacher(db.Model):
    __tablename__ = 'teachers'
    teacher_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone=db.Column(db.BigInteger,unique=True)
class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    youtube_link = db.Column(db.String(200))  
    image_url = db.Column(db.String(200))  
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

class CourseContent(db.Model):
    __tablename__ = 'course_contents'
    content_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(10), nullable=False)  
    content = db.Column(db.String(100))  
    order = db.Column(db.Integer, nullable=False)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    purchase_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    name=db.column(db.String(30))
    
    

@app.route('/')
def index():
    student_name = None
    details=Course.query.all()
    if 'std_email' in session:
        email = session['std_email']
        student = Student.query.filter_by(email=email).first()
        if student:
            student_name = student.username
    
    return render_template('index.html', student_name=student_name,details=details)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
@app.route('/student_login', methods=['POST', 'GET'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pwd']

        student = Student.query.filter_by(email=email, password=password).first()
        if student:
            otp = ''.join(random.choices(string.digits, k=6))
            print(otp)
            send_otp_email(email, otp)
            session['std_otp'] = otp
            session['std_email'] = email
            return redirect(url_for('std_verify_otp'))
        else:
            flash("Invalid email or password. Please try again", "error")
            return render_template('student_login.html')
    return render_template('student_login.html')
@app.route('/std_verify_otp',methods=['GET','POST'])
def std_verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        stored_otp = session.get('std_otp')
        email = session.get('std_email')

        if user_otp == stored_otp:
            
            return redirect(url_for('index'))
        else:
            return "Invalid OTP. Please try again."

    return render_template('std_verify_otp.html')
    
@app.route('/student_register',methods=['GET','POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['uname']
        email = request.form['email']
        password = request.form['pwd']

        existing_student = Student.query.filter_by(email=email).first()
        if existing_student:
            flash("Email already exists. Please use a different email.", 'error')
            return render_template('student_register.html')

        new_student = Student(username=username, email=email, password=password)
        db.session.add(new_student)
        db.session.commit()

        return redirect(url_for('student_login'))
    else:
        return render_template('student_register.html')

def send_otp_email(email, otp):
    msg = Message('OTP Verification', sender='rajeshnrajeshn567@gmail.com', recipients=[email])
    msg.body = f'Enter OTP for student login is : {otp}'
    mail.send(msg)
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        stored_otp = session.get('otp')
        email = session.get('email')

        if user_otp == stored_otp:
            
            return redirect(url_for('teacher_dashboard'))
        else:
            return "Invalid OTP. Please try again."

    return render_template('verify_otp.html')


@app.route('/teacher_login',methods=['GET','POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pwd']

        teacher = Teacher.query.filter_by(email=email, password=password).first()
        if teacher:
            otp = ''.join(random.choices(string.digits, k=6))
            print(otp)
            send_otp_email(email, otp)
            session['otp'] = otp
            session['email'] = email
            session['teacher_name'] = teacher.username  # Assuming the teacher's name is stored in the 'name' attribute of the Teacher model
            return redirect(url_for('verify_otp'))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template('teacher_login.html')

    return render_template('teacher_login.html')


    



@app.route('/teacher_register',methods=['GET','POST'])
def teacher_register():
    if request.method == 'POST':
        username = request.form['uname']
        email = request.form['email']
        password = request.form['pwd']

        existing_teacher = Teacher.query.filter_by(email=email).first()
        if existing_teacher:
            flash("Email already exists. Please use a different email.", 'error')
            return render_template('teacher_register.html')

        new_teacher = Teacher(username=username, email=email, password=password)
        db.session.add(new_teacher)
        db.session.commit()

        return redirect(url_for('teacher_login'))  
    else:
        return render_template('teacher_register.html')
@app.route("/teacher_dashboard")
def teacher_dashboard():
    # if 'email' in session:
    #     email = session['email']
    #     teacher = Teacher.query.filter_by(email=email).first()
    #     if teacher:
    #         students = Student.query.all() 
    #         return render_template('teacher_dashboard.html', students=students)
    # return redirect(url_for('teacher_login'))
    if 'otp' in session:
        email = session['email']
        student_page = request.args.get('student_page', 1, type=int)
        course_page = request.args.get('course_page', 1, type=int)

        students = Student.query.paginate(page=student_page, per_page=10)
        courses = Course.query.paginate(page=course_page, per_page=10)
        total_students = Student.query.count()
        purchased= db.session.query(db.func.count(db.func.distinct(Purchase.student_id))).scalar()

        return render_template('teacher_dashboard.html', students=students, courses=courses,total_students=total_students,purchased=purchased)
    return redirect(url_for('teacher_login'))
   

@app.route('/courses')
def courses():
    if 'std_email' in session:
        courses = Course.query.all()
        return render_template("courses.html", courses=courses)
    else:
        flash("Please login to access.", "error")
        return redirect(url_for('student_login'))

@app.route('/courses/wd')
def courses_avaiable():
    std_email = session.get("std_email")
    print("Session contents:", session)
    if std_email:
        return render_template("Course_details.html")
    else:
        return 'Please login to view courses <a href="' + url_for("student_login") + '">Login</a>'


@app.route('/delete_student/<int:student_id>', methods=['POST','GET'])
def delete_student(student_id):
    if request.method == 'POST':
        student = Student.query.get(student_id)
        if student:
            db.session.delete(student)
            db.session.commit()
            flash('Student deleted successfully.', 'success')
        else:
            flash('Student not found.', 'error')
    return redirect(url_for('teacher_dashboard'))

@app.route('/update_student/<int:student_id>', methods=['GET', 'POST'])
def update_student(student_id):
    student = Student.query.get(student_id)
    if student:
        if request.method == 'POST':
            # Update student details based on form data
            student.username = request.form['username']
            student.email = request.form['email']
            student.password = request.form['password']
            db.session.commit()
            flash('Student updated successfully.', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('update_student.html', student=student)
    else:
        flash('Student not found.', 'error')
        return redirect(url_for('teacher_dashboard'))
    

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        teacher_id = session.get('teacher_id') 
        youtube_link = request.form['youtube_url']
        image_url = request.form['image_url']
        
        teacher_id = request.form['teacher_id']

        new_course = Course(title=title, description=description, price=price, teacher_id=teacher_id,
                            youtube_link=youtube_link, image_url=image_url)
        db.session.add(new_course)
        db.session.commit()
        students = Student.query.all()
        student_emails = [student.email for student in students]
        subject = 'New Course Added: {}'.format(title)
        body = 'A new course has been added:\n\nTitle: {}\nDescription: {}\nPrice: {}'.format(title, description, price)

        msg = Message(subject, recipients=student_emails)
        msg.body = body

        msg.sender = app.config['MAIL_DEFAULT_SENDER']

        mail.send(msg)

        flash('Course added successfully.', 'success')
        return redirect(url_for('teacher_dashboard'))
    else:
        return render_template('add_course.html')
@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get(course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash('deleted succesfully')
        return redirect(url_for('teacher_dashboard'))
    return 'Course not found', 404


@app.route('/update_course/<int:course_id>', methods=['POST','GET'])
def update_course(course_id):
    course = Course.query.get(course_id)
    if request.method == 'POST':
        course = Course.query.get(course_id)
        course.title = request.form['title']
        course.description = request.form['description']
        course.price = request.form['price']
        course.youtube_link = request.form['youtube_link']
        course.image_url = request.form['image_url']
        
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
@app.route('/about')
def about():    
    return render_template("about.html")
@app.route('/course_video')
def course_video():
    
    youtube_link = request.args.get('youtube_link', '')
    parsed_url = urlparse(youtube_link)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
    
    
    return render_template('course_details.html', youtube_link=base_url)


# @app.route('/purchase', methods=['POST','GET'])
# def buy():
#     if request.method == 'POST':
#         student_id = request.form.get('student_id')
#         course_id = request.form.get('course_id')
#         name=request.form.get('name')
        
        
#         new_purchase = Purchase(student_id=student_id, course_id=course_id,name=name)
        
#         db.session.add(new_purchase)
#         db.session.commit()
        
#         return redirect(url_for('courses'))
#     return render_template('purchase.html')
    
    
  


@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        results = Course.query.filter((Course.title.ilike(f'%{query}%')) | (Course.description.ilike(f'%{query}%'))).all()
        serialized_results = [{'title': course.title, 'description': course.description, 'image_url': course.image_url} for course in results]
        return jsonify(serialized_results)
    else:
        return jsonify([])
    
@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

@app.route('/payment', methods=['POST'])
def payment():

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment/execute",
            "cancel_url": "http://localhost:5000/"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "testitem",
                    "sku": "12345",
                    "price": "500.00",
                    "currency": "USD",
                    "quantity": 1}]},
            "amount": {
                "total": "500.00",
                "currency": "USD"},
            "description": "This is the payment transaction description."}]})

    if payment.create():
        print('Payment success!')
    else:
        print(payment.error)

    return jsonify({'paymentID' : payment.id})

@app.route('/execute', methods=['POST'])
def execute():
    success = False

    payment = paypalrestsdk.Payment.find(request.form['paymentID'])

    if payment.execute({'payer_id' : request.form['payerID']}):
        print('Execute success!')
        success = True
    else:
        print(payment.error)

    return jsonify({'success' : success})




if __name__ == '__main__':
    app.run(debug=True)
