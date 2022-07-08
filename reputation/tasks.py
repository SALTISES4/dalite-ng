from dalite.celery import app


@app.task
def update_reputation_history():
    from .models import Reputation, ReputationHistory

    for reputation in Reputation.objects.all().iterator():
        ReputationHistory.create(reputation)
