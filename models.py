from extensions import db
from datetime import datetime

class Manager(db.Model):
    __tablename__ = 'managers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Store hashed passwords
    # One manager can have many employees
    employees = db.relationship('Employee', backref='manager', lazy=True)

    def __repr__(self):
        return f"<Manager {self.name}>"

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # Each employee is assigned to one manager
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=False)
    # One employee can have multiple reports
    reports = db.relationship('Report', backref='employee', lazy=True)

    def __repr__(self):
        return f"<Employee {self.name}>"

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    report_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    # New metrics for the QVT questionnaire:
    satisfaction = db.Column(db.Integer, nullable=False)
    pressure = db.Column(db.Integer, nullable=False)
    anxiety = db.Column(db.Integer, nullable=False)
    relation = db.Column(db.Integer, nullable=False)
    negotiation = db.Column(db.Integer, nullable=False)
    task_satisfaction = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Report {self.id} for Employee {self.employee_id}>"
