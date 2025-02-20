import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, send_file
from passlib.hash import pbkdf2_sha256
from models import Employee, Report
from extensions import db

authEmployees = Blueprint('authEmployee', __name__)

@authEmployees.route('/employees/home')
def employee_home():
    return render_template('employees/home.html')

@authEmployees.route('/employees/signin', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        email = request.form.get('employee_log_mail')
        password = request.form.get('employee_log_password')
        employee = Employee.query.filter_by(email=email).first()
        if employee and pbkdf2_sha256.verify(password, employee.password):
            # Set session variables after successful login
            session['employee_id'] = employee.id
            session['employee_name'] = employee.name
            return redirect(url_for('authEmployee.employee_dashboard'))
        else:
            flash("Invalid credentials. Please try again.")
            return render_template('employees/signin.html')
    return render_template('employees/signin.html')

@authEmployees.route('/employees/signup', methods=['GET', 'POST'])
def employee_signup():
    if request.method == 'POST':
        name = request.form.get('employee_signup_name')
        email = request.form.get('employee_signup_email')
        password = request.form.get('employee_signup_password')
        # Hash the password before storing it
        hashed_password = pbkdf2_sha256.hash(password)
        # Assign a default manager (adjust logic as needed)
        new_employee = Employee(name=name, email=email, password=hashed_password, manager_id=1)
        try:
            db.session.add(new_employee)
            db.session.commit()
        except Exception as e:
            flash("Error creating account. Please try again.")
            return render_template('employees/signup.html')
        flash("Account created successfully! Please sign in.")
        return redirect(url_for('authEmployee.employee_login'))
    return render_template('employees/signup.html')
@authEmployees.route('/employees/dashboard')
def employee_dashboard():
    employee_id = session.get('employee_id')
    if not employee_id:
        flash("Please sign in to access your dashboard.")
        return redirect(url_for('authEmployee.employee_login'))
    
    employee = Employee.query.get(employee_id)
    reports = Report.query.filter_by(employee_id=employee_id).order_by(Report.report_date).all()
    
    # Compute average metrics if there are reports
    if reports:
        df = pd.DataFrame([{
            'satisfaction': report.satisfaction,
            'pressure': report.pressure,
            'anxiety': report.anxiety,
            'relation': report.relation,
            'negotiation': report.negotiation,
            'task_satisfaction': report.task_satisfaction
        } for report in reports])
        avg_metrics = df.mean().to_dict()
        # Replace any NaN values with 0.0
        avg_metrics = {k: (0.0 if pd.isna(v) else float(v)) for k, v in avg_metrics.items()}
    else:
        avg_metrics = {
            'satisfaction': 0.0,
            'pressure': 0.0,
            'anxiety': 0.0,
            'relation': 0.0,
            'negotiation': 0.0,
            'task_satisfaction': 0.0
        }
    
    labels = list(avg_metrics.keys())
    total = sum(avg_metrics.values())
    if pd.isna(total):
        total = 0.0

    # Create the pie chart
    plt.figure(figsize=(6, 6))
    if total == 0.0:
        # No valid data available – display a placeholder chart
        plt.text(0.5, 0.5, 'No Data Available', horizontalalignment='center', 
                 verticalalignment='center', fontsize=16)
        plt.axis('off')
    else:
        sizes = [(avg_metrics[key] / total) * 100.0 for key in labels]
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title("Quality of Work Life (QVT) Breakdown")
        plt.axis('equal')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_image = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    
    return render_template('employees/dashboard.html', employee=employee, reports=reports, chart_image=chart_image)

@authEmployees.route('/employees/submit_report', methods=['POST'])
def submit_report():
    employee_id = session.get('employee_id')
    if not employee_id:
        flash("Please sign in to submit a report.")
        return redirect(url_for('authEmployee.employee_login'))
    
    try:
        # Retrieve all new metrics from form
        satisfaction = int(request.form.get('satisfaction'))
        pressure = int(request.form.get('pressure'))
        anxiety = int(request.form.get('anxiety'))
        relation = int(request.form.get('relation'))
        negotiation = int(request.form.get('negotiation'))
        task_satisfaction = int(request.form.get('task_satisfaction'))
    except (TypeError, ValueError):
        flash("Please enter valid numbers for all fields.")
        return redirect(url_for('authEmployee.employee_dashboard'))
    
    comment = request.form.get('comment')
    
    new_report = Report(
        employee_id=employee_id,
        satisfaction=satisfaction,
        pressure=pressure,
        anxiety=anxiety,
        relation=relation,
        negotiation=negotiation,
        task_satisfaction=task_satisfaction,
        comment=comment
    )
    try:
        db.session.add(new_report)
        db.session.commit()
        flash("Report submitted successfully!")
    except Exception as e:
        flash("Error submitting report. Please try again.")
    return redirect(url_for('authEmployee.employee_dashboard'))

@authEmployees.route('/employees/download_report')
def download_report():
    employee_id = session.get('employee_id')
    if not employee_id:
        flash("Please sign in to generate a report.")
        return redirect(url_for('authEmployee.employee_login'))
    
    employee = Employee.query.get(employee_id)
    reports = Report.query.filter_by(employee_id=employee_id).order_by(Report.report_date).all()
    
    if not reports:
        flash("No reports available to generate a PDF.")
        return redirect(url_for('authEmployee.employee_dashboard'))
    
    # For summary, we'll use the latest report
    latest_report = reports[-1]
    
    # Helper to create a summary based on score thresholds
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
    
    # Re-calculate average metrics across all reports for the pie chart
    import pandas as pd
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
    
    # Generate the pie chart using matplotlib
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
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
    
    # Generate the PDF using ReportLab
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    import datetime
    now = datetime.datetime.now()
    header_text = now.strftime("%A, %d %B %Y")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, header_text)
    
    # Employee name in the header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 80, f"Employee Report for {employee.name}")
    
    # Draw a separator line
    c.line(50, height - 90, width - 50, height - 90)
    
    # Write the summary text
    c.setFont("Helvetica", 12)
    text_object = c.beginText(50, height - 120)
    for line in summary_text.split("\n"):
        text_object.textLine(line)
    c.drawText(text_object)
    
    # Embed the pie chart image in the PDF
    chart_image_reader = ImageReader(chart_buf)
    # Place the chart image on the lower right of the page
    c.drawImage(chart_image_reader, width - 250, height - 300, width=200, height=200)
    
    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    
    return send_file(pdf_buffer, as_attachment=True, download_name="employee_report.pdf", mimetype="application/pdf")
