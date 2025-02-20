from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from passlib.hash import pbkdf2_sha256
from models import Manager
from extensions import db

authManagers = Blueprint('authManager', __name__)

@authManagers.route('/managers/home', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        email = request.form['manager_log_mail']
        password = request.form['manager_log_password']

        try:
            manager = Manager.query.filter_by(email=email).first()
        except Exception as e:
            print(f"Error querying manager email: {str(e)}")
            flash("An error occurred. Please try again.")
            return render_template('managers/home.html')

        if manager:
            if pbkdf2_sha256.verify(password, manager.password):
                return render_template('home.html')
            else:
                flash("Incorrect password!")
                return render_template('managers/home.html')
        else:
            flash("This email doesn't exist!")
            return render_template('managers/home.html')
    
    return render_template('managers/home.html')
