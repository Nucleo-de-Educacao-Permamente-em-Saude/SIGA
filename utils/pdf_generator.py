from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

class PDFGenerator:
    @staticmethod
    def generate_student_report(student, enrollments):
        filename = f"student_report_{student.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(f"static/reports/{filename}", pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph(f"Relatório do Aluno - {student.username}", styles['Heading1'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Informações do aluno
        story.append(Paragraph(f"Email: {student.email}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Tabela de notas
        data = [['Curso', 'Professor', 'Nota', 'Frequência']]
        for enrollment in enrollments:
            data.append([
                enrollment.course.name,
                enrollment.course.teacher.username,
                str(enrollment.grade or 'N/A'),
                f"{enrollment.attendance}%"
            ])
        
        table = Table(data, colWidths=[2.5*inch, 2*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        # Data de geração
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            styles['Normal']
        ))
        
        doc.build(story)
        return filename

    @staticmethod
    def generate_course_report(course, enrollments):
        filename = f"course_report_{course.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(f"static/reports/{filename}", pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph(f"Relatório do Curso - {course.name}", styles['Heading1'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Informações do curso
        story.append(Paragraph(f"Professor: {course.teacher.username}", styles['Normal']))
        story.append(Paragraph(f"Total de Alunos: {len(enrollments)}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Tabela de alunos e notas
        data = [['Aluno', 'Nota', 'Frequência']]
        for enrollment in enrollments:
            data.append([
                enrollment.student.username,
                str(enrollment.grade or 'N/A'),
                f"{enrollment.attendance}%"
            ])
        
        # Adicionar linha com médias
        grades = [e.grade for e in enrollments if e.grade is not None]
        attendance = [e.attendance for e in enrollments if e.attendance is not None]
        avg_grade = sum(grades) / len(grades) if grades else 'N/A'
        avg_attendance = sum(attendance) / len(attendance) if attendance else 'N/A'
        
        data.append(['Média', 
                    str(round(avg_grade, 2)) if avg_grade != 'N/A' else 'N/A',
                    f"{round(avg_attendance, 2)}%" if avg_attendance != 'N/A' else 'N/A'])
        
        table = Table(data, colWidths=[2.5*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        # Data de geração
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            styles['Normal']
        ))
        
        doc.build(story)
        return filename
