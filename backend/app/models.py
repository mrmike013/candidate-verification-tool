import json, uuid, datetime as dt
from . import db

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100))
    _custom_questions = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    @property
    def custom_questions(self):
        return json.loads(self._custom_questions)

    @custom_questions.setter
    def custom_questions(self, value):
        self._custom_questions = json.dumps(value)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

class Assessment(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    job_position = db.Column(db.String(100))
    _questions = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")
    score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    expiry = db.Column(db.DateTime, nullable=False)
    time_taken = db.Column(db.Float)

    @property
    def questions(self):
        return json.loads(self._questions)

    @questions.setter
    def questions(self, value):
        self._questions = json.dumps(value)
