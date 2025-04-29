# app.py - Flask Backend for Candidate Verification Tool

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import datetime
import random
from database import db, Assessment, Candidate, Question, Company

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///candidate_verification.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db.init_app(app)

# Sample logic questions bank
LOGIC_QUESTIONS = [
    {
        "id": "q1",
        "question": "What comes next in this sequence: 2, 4, 8, 16, ___?",
        "options": ["24", "32", "64", "20"],
        "correct_answer": "32"
    },
    {
        "id": "q2",
        "question": "If A is larger than B, and B is smaller than C, which statement must be true?",
        "options": [
            "A is larger than C", 
            "A is smaller than C", 
            "A and C are equal", 
            "The relationship between A and C cannot be determined"
        ],
        "correct_answer": "The relationship between A and C cannot be determined"
    },
    {
        "id": "q3",
        "question": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        "options": ["1 minute", "5 minutes", "20 minutes", "100 minutes"],
        "correct_answer": "5 minutes"
    },
    {
        "id": "q4",
        "question": "If all roses are flowers and some flowers fade quickly, then:",
        "options": [
            "All roses fade quickly",
            "Some roses fade quickly",
            "No roses fade quickly",
            "Cannot be determined"
        ],
        "correct_answer": "Cannot be determined"
    },
    {
        "id": "q5",
        "question": "A clock shows 3:15. What is the angle between the hour and minute hands?",
        "options": ["7.5 degrees", "22.5 degrees", "37.5 degrees", "45 degrees"],
        "correct_answer": "7.5 degrees"
    }
]

@app.route('/api/companies', methods=['GET'])
def get_companies():
    companies = Company.query.all()
    return jsonify([{
        'id': company.id,
        'name': company.name,
        'industry': company.industry
    } for company in companies])

@app.route('/api/companies', methods=['POST'])
def create_company():
    data = request.json
    company = Company(
        name=data['name'],
        industry=data['industry'],
        custom_questions=data.get('custom_questions', [])
    )
    db.session.add(company)
    db.session.commit()
    return jsonify({'id': company.id, 'message': 'Company created successfully'})

@app.route('/api/assessments', methods=['POST'])
def create_assessment():
    data = request.json
    
    # Create or get candidate
    candidate = Candidate.query.filter_by(email=data['email']).first()
    if not candidate:
        candidate = Candidate(
            email=data['email'],
            name=data['name']
        )
        db.session.add(candidate)
    
    # Get company
    company = Company.query.get(data['company_id'])
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    # Create a new assessment
    assessment_id = str(uuid.uuid4())
    
    # Select questions: 3 random logic questions + up to 2 company-specific questions
    selected_questions = random.sample(LOGIC_QUESTIONS, 3)
    company_questions = []
    
    if company.custom_questions:
        num_company_questions = min(2, len(company.custom_questions))
        company_questions = random.sample(company.custom_questions, num_company_questions)
    
    all_questions = selected_questions + company_questions
    
    # Create assessment
    assessment = Assessment(
        id=assessment_id,
        candidate_id=candidate.id,
        company_id=company.id,
        job_position=data.get('job_position', ''),
        questions=[q['id'] for q in all_questions],
        status='pending',
        created_at=datetime.datetime.utcnow(),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    # Return assessment details with questions
    return jsonify({
        'assessment_id': assessment_id,
        'questions': all_questions,
        'expiry': assessment.expiry.isoformat()
    })

@app.route('/api/assessments/<assessment_id>/submit', methods=['POST'])
def submit_assessment():
    data = request.json
    assessment = Assessment.query.get(data['assessment_id'])
    
    if not assessment:
        return jsonify({'error': 'Assessment not found'}), 404
    
    if assessment.status != 'pending':
        return jsonify({'error': 'Assessment already completed'}), 400
    
    if datetime.datetime.utcnow() > assessment.expiry:
        assessment.status = 'expired'
        db.session.commit()
        return jsonify({'error': 'Assessment has expired'}), 400
    
    # Calculate score
    correct_answers = 0
    total_questions = len(assessment.questions)
    
    for answer in data['answers']:
        question_id = answer['question_id']
        
        # Check if it's a standard logic question
        logic_question = next((q for q in LOGIC_QUESTIONS if q['id'] == question_id), None)
        
        if logic_question and answer['answer'] == logic_question['correct_answer']:
            correct_answers += 1
        elif not logic_question:
            # It's a company-specific question
            company = Company.query.get(assessment.company_id)
            company_question = next((q for q in company.custom_questions if q['id'] == question_id), None)
            if company_question and answer['answer'] == company_question['correct_answer']:
                correct_answers += 1
    
    score = (correct_answers / total_questions) * 100
    
    # Update assessment
    assessment.score = score
    assessment.completed_at = datetime.datetime.utcnow()
    assessment.status = 'completed'
    assessment.time_taken = (assessment.completed_at - assessment.created_at).total_seconds()
    
    db.session.commit()
    
    return jsonify({
        'assessment_id': assessment.id,
        'score': score,
        'status': 'completed'
    })

@app.route('/api/companies/<company_id>/assessments', methods=['GET'])
def get_company_assessments(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    assessments = Assessment.query.filter_by(company_id=company_id).all()
    results = []
    
    for assessment in assessments:
        candidate = Candidate.query.get(assessment.candidate_id)
        results.append({
            'assessment_id': assessment.id,
            'candidate_name': candidate.name,
            'candidate_email': candidate.email,
            'job_position': assessment.job_position,
            'status': assessment.status,
            'score': assessment.score,
            'created_at': assessment.created_at.isoformat(),
            'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None,
            'time_taken': assessment.time_taken
        })
    
    return jsonify(results)

@app.route('/api/assessments/<assessment_id>', methods=['GET'])
def get_assessment(assessment_id):
    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        return jsonify({'error': 'Assessment not found'}), 404
    
    candidate = Candidate.query.get(assessment.candidate_id)
    company = Company.query.get(assessment.company_id)
    
    # Get questions
    questions = []
    for q_id in assessment.questions:
        # Check if it's a standard logic question
        logic_question = next((q for q in LOGIC_QUESTIONS if q['id'] == q_id), None)
        
        if logic_question:
            questions.append(logic_question)
        else:
            # It's a company-specific question
            company_question = next((q for q in company.custom_questions if q['id'] == q_id), None)
            if company_question:
                questions.append(company_question)
    
    return jsonify({
        'assessment_id': assessment.id,
        'candidate': {
            'name': candidate.name,
            'email': candidate.email
        },
        'company': {
            'name': company.name
        },
        'job_position': assessment.job_position,
        'status': assessment.status,
        'score': assessment.score,
        'created_at': assessment.created_at.isoformat(),
        'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None,
        'questions': questions
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
