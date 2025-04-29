import click, json, datetime as dt, uuid
from . import db
from .models import Company

@click.command("seed")
def seed_cmd():
    """Load a dummy company with two custom questions"""
    if Company.query.first():
        click.echo("Data already seeded; skipping")
        return

    comp = Company(
        name="DemoCo",
        industry="Software",
        custom_questions=[
            {"id": "c1", "question": "Why do you want to join DemoCo?", "options": [], "correct_answer": "any"},
            {"id": "c2", "question": "2 + 2 = ?", "options": ["3", "4"], "correct_answer": "4"},
        ],
    )
    db.session.add(comp)
    db.session.commit()
    click.echo("Seeded DemoCo (#%s)" % comp.id)
