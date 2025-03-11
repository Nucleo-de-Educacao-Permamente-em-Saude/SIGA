from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, SubmitField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=3)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')])
    submit = SubmitField('Submit')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    teacher_id = SelectField('Teacher', coerce=int)
    submit = SubmitField('Submit')

class GradeForm(FlaskForm):
    grade = FloatField('Grade', validators=[DataRequired()])
    attendance = FloatField('Attendance %', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_date = DateTimeField('Start Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_date = DateTimeField('End Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    type = SelectField('Event Type', choices=[
        ('aula', 'Aula'),
        ('prova', 'Prova'),
        ('feriado', 'Feriado'),
        ('evento', 'Evento Geral')
    ])
    course_id = SelectField('Course', coerce=int)
    submit = SubmitField('Submit')

class EnrollmentForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Enroll Student')