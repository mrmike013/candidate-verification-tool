import datetime as dt, random
from flask import Blueprint, request, jsonify, current_app
from .models import db, Company, Candidate, Assessment

api_bp = Blueprint("api", __name__)

LOGIC_QUESTIONS = [
    {
        "id": "q1",
        "question": "What comes next in this sequence: 2, 4, 8, 16, ___?",
        "options": ["24", "32", "64", "20"],
        "correct_answer": "32",
    },
    {
        "id": "q2",
        "question": "If A > B and B < C, which statement is true?",
        "options": [
            "A > C",
            "A < C",
            "A = C",
            "Cannot be determined",
        ],
        "correct_answer": "Cannot be determined",
    },
    # … add more
]

# ---------- Company endpoints ----------
@api_bp.route("/companies", methods=["POST"])
def create_company():
    data = request.get_json()
    company = Company(
        name=data["name"],
        industry=data.get("industry"),
        custom_questions=data.get("custom_questions", []),
    )
    db.session.add(company)
    db.session.commit()
    return jsonify({"id": company.id}), 201

@api_bp.route("/companies", methods=["GET"])
def list_companies():
    companies = Company.query.all()
    return jsonify([
        {"id": c.id, "name": c.name, "industry": c.industry} for c in companies
    ])

# ---------- Assessment endpoints ----------
@api_bp.route("/assessments", methods=["POST"])
def create_assessment():
    data = request.get_json()

    candidate = Candidate.query.filter_by(email=data["email"]).first()
    if not candidate:
        candidate = Candidate(name=data["name"], email=data["email"])
        db.session.add(candidate)
        db.session.flush()

    company = Company.query.get_or_404(data["company_id"])

    selected_logic = random.sample(LOGIC_QUESTIONS, 3)
    company_qs = random.sample(company.custom_questions, min(2, len(company.custom_questions)))
    questions = selected_logic + company_qs

    assessment = Assessment(
        candidate_id=candidate.id,
        company_id=company.id,
        job_position=data.get("job_position", ""),
        questions=[q["id"] for q in questions],
        expiry=dt.datetime.utcnow() + dt.timedelta(days=7),
    )
    db.session.add(assessment)
    db.session.commit()

    return jsonify({"assessment_id": assessment.id, "questions": questions, "expiry": assessment.expiry.isoformat()})

@api_bp.route("/assessments/<assessment_id>/submit", methods=["POST"])
def submit_assessment(assessment_id):
    data = request.get_json()
    assessment = Assessment.query.get_or_404(assessment_id)

    if assessment.status != "pending":
        return jsonify({"error": "Already completed or expired"}), 400
    if dt.datetime.utcnow() > assessment.expiry:
        assessment.status = "expired"
        db.session.commit()
        return jsonify({"error": "Expired"}), 400

    correct = 0
    for ans in data["answers"]:
        qid, given = ans["question_id"], ans["answer"]
        # logic questions
        logic_match = next((q for q in LOGIC_QUESTIONS if q["id"] == qid), None)
        if logic_match and given == logic_match["correct_answer"]:
            correct += 1
        else:
            company = Company.query.get(assessment.company_id)
            comp_q = next((q for q in company.custom_questions if q["id"] == qid), None)
            if comp_q and given == comp_q["correct_answer"]:
                correct += 1

    total = len(assessment.questions)
    assessment.score = (correct / total) * 100
    assessment.status = "completed"
    assessment.completed_at = dt.datetime.utcnow()
    assessment.time_taken = (assessment.completed_at - assessment.created_at).total_seconds()
    db.session.commit()

    return jsonify({"score": assessment.score, "status": assessment.status})
