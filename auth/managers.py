import io, base64, datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from flask import (Blueprint, render_template, request, flash, redirect,
                   url_for, session, send_file)
from passlib.hash import pbkdf2_sha256
from models import Manager, Employee, Report
from extensions import db
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

authManagers = Blueprint('authManager', __name__)

# Manager landing page
@authManagers.route('/managers/home')
def manager_home():
    return render_template('managers/home.html')

# Manager signup: they enter name, secret code and a password.
# Email is auto-generated as <name in lowercase with spaces replaced by dots>@qvt.fr.
@authManagers.route('/managers/signup', methods=['GET', 'POST'])
def manager_signup():
    if request.method == 'POST':
        name = request.form.get('manager_signup_name')
        code = request.form.get('manager_signup_code')
        password = request.form.get('manager_signup_password')

        # Check the secret code
        if code != "123":
            flash("Invalid signup code.", "error")
            return render_template('managers/signup.html')

        email = f"{name.lower().replace(' ','.')}@qvt.fr"
        hashed_password = pbkdf2_sha256.hash(password)
        new_manager = Manager(name=name, email=email, password=hashed_password)
        try:
            db.session.add(new_manager)
            db.session.commit()
        except Exception as e:
            flash("Error creating account. Please try again.", "error")
            return render_template('managers/signup.html')

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for('authManager.manager_signin'))

    return render_template('managers/signup.html')


# Manager signin route
@authManagers.route('/managers/signin', methods=['GET', 'POST'])
def manager_signin():
    if request.method == 'POST':
        email = request.form.get('manager_signin_email')
        password = request.form.get('manager_signin_password')
        manager = Manager.query.filter_by(email=email).first()
        if manager and pbkdf2_sha256.verify(password, manager.password):
            session['manager_id'] = manager.id
            session['manager_name'] = manager.name
            return redirect(url_for('authManager.manager_dashboard'))
        else:
            flash("Invalid credentials. Please try again.")
            return render_template('managers/signin.html')
    return render_template('managers/signin.html')

# Manager dashboard: lists all employees belonging to this manager.
@authManagers.route('/managers/dashboard')
def manager_dashboard():
    manager_id = session.get('manager_id')
    if not manager_id:
        flash("Please sign in to access your dashboard.")
        return redirect(url_for('authManager.manager_signin'))
    manager = Manager.query.get(manager_id)
    employees = Employee.query.filter_by(manager_id=manager_id).all()
    return render_template('managers/dashboard.html', manager=manager, employees=employees)

# Manager PDF report download for a given employee.
@authManagers.route('/managers/download_report/<int:employee_id>')
def manager_download_report(employee_id):
    manager_id = session.get('manager_id')
    if not manager_id:
        flash("Please sign in to generate a report.")
        return redirect(url_for('authManager.manager_signin'))
    # Ensure the employee belongs to this manager
    employee = Employee.query.filter_by(id=employee_id, manager_id=manager_id).first()
    if not employee:
        flash("Employee not found.")
        return redirect(url_for('authManager.manager_dashboard'))
    reports = Report.query.filter_by(employee_id=employee_id).order_by(Report.report_date).all()
    if not reports:
        flash("No reports available for this employee.")
        return redirect(url_for('authManager.manager_dashboard'))
    latest_report = reports[-1]
    # Helper for summary text
    def get_summary(metric, value):
        if value >= 8:
            return f"Your {metric} was excellent."
        elif value >= 5:
            return f"Your {metric} was good."
        else:
            return f"Your {metric} could be improved."
    summary_text = (
        f"{get_summary('satisfaction', latest_report.satisfaction)}\n"
        f"{get_summary('pressure', latest_report.pressure)}\n"
        f"{get_summary('anxiety', latest_report.anxiety)}\n"
        f"{get_summary('relation with others', latest_report.relation)}\n"
        f"{get_summary('negotiation with superiors', latest_report.negotiation)}\n"
        f"{get_summary('task satisfaction', latest_report.task_satisfaction)}"
    )
    # Compute averages for pie chart from all reports of this employee
    df = pd.DataFrame([{
        'satisfaction': report.satisfaction,
        'pressure': report.pressure,
        'anxiety': report.anxiety,
        'relation': report.relation,
        'negotiation': report.negotiation,
        'task_satisfaction': report.task_satisfaction
    } for report in reports])
    avg_metrics = df.mean().to_dict()
    avg_metrics = {k: (0.0 if pd.isna(v) else float(v)) for k, v in avg_metrics.items()}
    labels = list(avg_metrics.keys())
    total = sum(avg_metrics.values())
    if total == 0:
        sizes = [0.0 for _ in labels]
    else:
        sizes = [(avg_metrics[key] / total) * 100.0 for key in labels]
    plt.figure(figsize=(4,4))
    if total == 0:
        plt.text(0.5, 0.5, 'No Data', horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
    else:
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title("QVT Breakdown")
        plt.axis('equal')
    chart_buf = io.BytesIO()
    plt.savefig(chart_buf, format='png')
    plt.close()
    chart_buf.seek(0)
    
    # Create PDF with ReportLab
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    now = datetime.datetime.now()
    header_text = now.strftime("%A, %d %B %Y")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, header_text)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 80, f"Employee Report for {employee.name}")
    c.line(50, height - 90, width - 50, height - 90)
    c.setFont("Helvetica", 12)
    text_object = c.beginText(50, height - 120)
    for line in summary_text.split("\n"):
        text_object.textLine(line)
    c.drawText(text_object)
    chart_image_reader = ImageReader(chart_buf)
    c.drawImage(chart_image_reader, width - 250, height - 300, width=200, height=200)
    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, as_attachment=True, download_name=f"{employee.name}_report.pdf", mimetype="application/pdf")
