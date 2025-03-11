from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Course, Enrollment, Event, Notification
from forms import LoginForm, UserForm, CourseForm, GradeForm, EventForm, EnrollmentForm
from utils.pdf_generator import PDFGenerator
from functools import wraps
from datetime import datetime
import os

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.context_processor
def inject_unread_notifications():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, 
            read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_users():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('manage_users'))

    users = User.query.all()
    return render_template('admin/users.html', users=users, form=form)

@app.route('/admin/courses', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_courses():
    form = CourseForm()
    teachers = User.query.filter_by(role='teacher').all()
    form.teacher_id.choices = [(t.id, t.username) for t in teachers]

    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            teacher_id=form.teacher_id.data
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully', 'success')
        return redirect(url_for('manage_courses'))

    courses = Course.query.all()
    return render_template('admin/classes.html', courses=courses, form=form)

@app.route('/admin/courses/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def enroll_student(course_id):
    course = Course.query.get_or_404(course_id)
    form = EnrollmentForm()

    # Obter lista de alunos que ainda não estão matriculados no curso
    enrolled_student_ids = [e.student_id for e in Enrollment.query.filter_by(course_id=course_id).all()]
    available_students = User.query.filter_by(role='student').filter(User.id.notin_(enrolled_student_ids)).all()

    form.student_id.choices = [(s.id, s.username) for s in available_students]

    if form.validate_on_submit():
        enrollment = Enrollment(
            student_id=form.student_id.data,
            course_id=course_id,
            attendance=100.0  # Iniciar com 100% de frequência
        )
        db.session.add(enrollment)
        db.session.commit()
        flash('Student enrolled successfully', 'success')
        return redirect(url_for('manage_course_enrollments', course_id=course_id))

    return render_template('admin/enroll_student.html', course=course, form=form)

@app.route('/admin/courses/<int:course_id>/enrollments')
@login_required
@role_required('admin')
def manage_course_enrollments(course_id):
    course = Course.query.get_or_404(course_id)
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    return render_template('admin/course_enrollments.html', course=course, enrollments=enrollments)

@app.route('/admin/courses/<int:course_id>/enrollments/<int:enrollment_id>/remove', methods=['POST'])
@login_required
@role_required('admin')
def remove_enrollment(course_id, enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    if enrollment.course_id != course_id:
        flash('Invalid enrollment', 'danger')
        return redirect(url_for('manage_courses'))

    db.session.delete(enrollment)
    db.session.commit()
    flash('Student removed from course', 'success')
    return redirect(url_for('manage_course_enrollments', course_id=course_id))

@app.route('/teacher/grades/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def manage_grades(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('dashboard'))

    form = GradeForm()
    if form.validate_on_submit():
        student_id = request.form.get('student_id')
        app.logger.debug(f"Updating grades - Student ID: {student_id}, Course ID: {course_id}")
        app.logger.debug(f"Form data - Grade: {form.grade.data}, Attendance: {form.attendance.data}")

        enrollment = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id
        ).first()

        if enrollment:
            app.logger.debug(f"Found enrollment: {enrollment.id}")
            old_grade = enrollment.grade
            enrollment.grade = form.grade.data
            enrollment.attendance = form.attendance.data
            db.session.commit()
            flash('Grades updated successfully', 'success')

            # Criar notificação para o aluno
            create_notification(
                student_id,
                f'Nota atualizada em {course.name}',
                f'Sua nota foi atualizada para {form.grade.data}',
                'info'
            )
        else:
            app.logger.error(f"Enrollment not found for student {student_id} in course {course_id}")
            flash('Error: Student enrollment not found', 'danger')

    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    app.logger.debug(f"Found {len(enrollments)} enrollments for course {course_id}")
    return render_template('teacher/grades.html', course=course, enrollments=enrollments, form=form)

@app.route('/student/grades')
@login_required
@role_required('student')
def view_grades():
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    return render_template('student/view_grades.html', enrollments=enrollments)

@app.route('/calendar')
@login_required
def view_calendar():
    return render_template('calendar/view.html')

@app.route('/calendar/events')
@login_required
def get_events():
    events = Event.query.all()
    event_list = []
    for event in events:
        # Verificar permissões baseadas no papel do usuário
        if current_user.role == 'student':
            # Estudantes só veem eventos dos seus cursos
            enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
            course_ids = [e.course_id for e in enrollments]
            if event.course_id and event.course_id not in course_ids:
                continue
        elif current_user.role == 'teacher':
            # Professores veem eventos dos seus cursos
            if event.course_id and event.course_id not in [c.id for c in Course.query.filter_by(teacher_id=current_user.id).all()]:
                continue

        event_list.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat(),
            'description': event.description,
            'type': event.type,
            'className': f'event-type-{event.type}'
        })
    return jsonify(event_list)

@app.route('/calendar/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if current_user.role == 'student':
        flash('Você não tem permissão para adicionar eventos.', 'danger')
        return redirect(url_for('view_calendar'))

    form = EventForm()
    # Configurar choices do course_id baseado no papel do usuário
    if current_user.role == 'teacher':
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
    else:  # admin
        courses = Course.query.all()
    form.course_id.choices = [(c.id, c.name) for c in courses]
    form.course_id.choices.insert(0, (0, 'Evento Geral'))

    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            type=form.type.data,
            course_id=form.course_id.data if form.course_id.data != 0 else None,
            created_by=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Evento adicionado com sucesso!', 'success')
        return redirect(url_for('view_calendar'))

    return render_template('calendar/add_event.html', form=form)

@app.route('/calendar/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    # Verificar permissões
    if current_user.role == 'student' or \
       (current_user.role == 'teacher' and event.created_by != current_user.id):
        flash('Você não tem permissão para editar este evento.', 'danger')
        return redirect(url_for('view_calendar'))

    form = EventForm(obj=event)
    if current_user.role == 'teacher':
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
    else:  # admin
        courses = Course.query.all()
    form.course_id.choices = [(c.id, c.name) for c in courses]
    form.course_id.choices.insert(0, (0, 'Evento Geral'))

    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.type = form.type.data
        event.course_id = form.course_id.data if form.course_id.data != 0 else None
        db.session.commit()
        flash('Evento atualizado com sucesso!', 'success')
        return redirect(url_for('view_calendar'))

    return render_template('calendar/edit_event.html', form=form, event=event)


@app.route('/notifications')
@login_required
def view_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    # Marcar todas as notificações como lidas
    for notification in notifications:
        if not notification.read:
            notification.read = True
    db.session.commit()

    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/mark_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('Você não tem permissão para acessar esta notificação.', 'danger')
        return redirect(url_for('view_notifications'))

    notification.read = True
    db.session.commit()
    return redirect(url_for('view_notifications'))

def create_notification(user_id, title, message, type='info'):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type
    )
    db.session.add(notification)
    db.session.commit()

# Ensure reports directory exists
os.makedirs('static/reports', exist_ok=True)

@app.route('/student/report/pdf')
@login_required
@role_required('student')
def generate_student_pdf():
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    filename = PDFGenerator.generate_student_report(current_user, enrollments)
    return send_from_directory('static/reports', filename, as_attachment=True)

@app.route('/teacher/course/<int:course_id>/report/pdf')
@login_required
@role_required('teacher')
def generate_course_pdf(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        flash('Você não tem permissão para gerar relatórios deste curso.', 'danger')
        return redirect(url_for('dashboard'))

    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    filename = PDFGenerator.generate_course_report(course, enrollments)
    return send_from_directory('static/reports', filename, as_attachment=True)