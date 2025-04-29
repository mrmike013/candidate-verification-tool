# database.py - SQLAlchemy models for the Candidate Verification Tool

from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime

db = SQLAlchemy()

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100))
    _custom_questions = db.Column(db.Text, default='[]')  # JSON string of custom questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def custom_questions(self):
        return json.loads(self._custom_questions)
    
    @custom_questions.setter
    def custom_questions(self, value):
        self._custom_questions = json.dumps(value)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship('Assessment', backref='candidate', lazy=True)

class Question(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    _options = db.Column(db.Text, nullable=False)  # JSON string of options
    correct_answer = db.Column(db.String(255), nullable=False)
    question_type = db.Column(db.String(50), default='logic')  # 'logic' or 'company'
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    
    @property
    def options(self):
        return json.loads(self._options)
    
    @options.setter
    def options(self, value):
        self._options = json.dumps(value)

class Assessment(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_position = db.Column(db.String(100))
    _questions = db.Column(db.Text, nullable=False)  # JSON array of question IDs
    status = db.Column(db.String(20), default='pending')  # pending, completed, expired
    score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    expiry = db.Column(db.DateTime, nullable=False)
    time_taken = db.Column(db.Float, nullable=True)  # in seconds
    
    @property
    def questions(self):
        return json.loads(self._questions)
    
    @questions.setter
    def questions(self, value):
        self._questions = json.dumps(value)
