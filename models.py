from extensions import db
from datetime import datetime

class Manager(db.Model):
    __bind_key__ = 'managers'
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
    # Note: Although we may conceptually relate managers to employees,
    # cross-database relationships (i.e. between binds) are not automatically enforced.
    # You can store a manager's id in Employee but the foreign key constraint cannot span binds.
    
    def __repr__(self):
        return f"<Manager {self.name}>"

class Employee(db.Model):
    __bind_key__ = 'employees'
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # Storing the manager's id as an integer; a formal foreign key cannot be enforced across binds.
    manager_id = db.Column(db.Integer, nullable=False)
    
    # One employee can have many reports.
    reports = db.relationship('Report', backref='employee', lazy=True)
    
    def __repr__(self):
        return f"<Employee {self.name}>"

class Report(db.Model):
    __bind_key__ = 'employees'
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    # Add the ForeignKey constraint here:
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    report_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    
    # QVT metrics
    satisfaction = db.Column(db.Integer, nullable=False)
    pressure = db.Column(db.Integer, nullable=False)
    anxiety = db.Column(db.Integer, nullable=False)
    relation = db.Column(db.Integer, nullable=False)
    negotiation = db.Column(db.Integer, nullable=False)
    task_satisfaction = db.Column(db.Integer, nullable=False)
    
    comment = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"<Report {self.id} for Employee {self.employee_id}>"
