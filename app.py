import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from extensions import db
from models import Manager, Employee, Report
from flask_migrate import Migrate

# After initializing your Flask app and SQLAlchemy:



# Load environment variables if needed
load_dotenv()

app = Flask(__name__)

# Use environment variables or fallback defaults
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", 'sqlite:///app.db')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", 'DJODNCWOICNWOIEACJOIEWJ')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from auth.managers import authManagers
from auth.employees import authEmployees

# Register blueprints for managers and employees
app.register_blueprint(authManagers, url_prefix='/')
app.register_blueprint(authEmployees, url_prefix='/')

@app.route('/')
def index():
    return render_template('home.html')

# Example route to list employees (for testing purposes)
@app.route('/employees')
def get_employees():
    employees = Employee.query.all()
    employee_list = []
    for emp in employees:
        employee_data = {
            'employee_id': emp.id,
            'email': emp.email,
            'name': emp.name,
            'manager_id': emp.manager_id
        }
        employee_list.append(employee_data)
    return jsonify({'employees': employee_list})

# Example route to list managers (for testing purposes)
@app.route('/managers')
def get_managers():
    managers = Manager.query.all()
    manager_list = []
    for mgr in managers:
        manager_data = {
            'manager_id': mgr.id,
            'email': mgr.email,
            'name': mgr.name
        }
        manager_list.append(manager_data)
    return jsonify({'managers': manager_list})

if __name__ == '__main__':
    # Create the database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Run the Flask application
    app.run(debug=True)
