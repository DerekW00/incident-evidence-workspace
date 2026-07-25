from django.db import models
from django.contrib.auth.models import User


class Organization(models.Model):
    name = models.CharField(max_length=120)


class Membership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)


class Service(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)


class Incident(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)


class Evidence(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20)
    text = models.TextField()
    at = models.DateTimeField()
    skew_seconds = models.IntegerField(default=0)


class RunbookSection(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    text = models.TextField()


class Investigation(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    start = models.DateTimeField()
    end = models.DateTimeField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, default="queued")
    revision = models.PositiveIntegerField(default=0)
    steps = models.PositiveIntegerField(default=0)
    tools = models.PositiveIntegerField(default=0)
    guard_units = models.PositiveIntegerField(default=0)
    measured_usage = models.JSONField(null=True)
    failure = models.TextField(blank=True)


class Job(models.Model):
    run = models.OneToOneField(Investigation, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, blank=True)
    lease_until = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)


class Event(models.Model):
    run = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="events"
    )
    sequence = models.PositiveIntegerField()
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "sequence"], name="ordered_run_events"
            )
        ]
        ordering = ["sequence"]


class Observation(models.Model):
    run = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="observations"
    )
    text = models.TextField()
    citations = models.JSONField(default=list)


class Hypothesis(models.Model):
    run = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="hypotheses"
    )
    text = models.TextField()
    confidence = models.CharField(max_length=30)
    citations = models.JSONField(default=list)
    contradictions = models.JSONField(default=list)


class Review(models.Model):
    run = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="reviews"
    )
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["run", "revision"], name="review_revision")
        ]


class Brief(models.Model):
    run = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="briefs"
    )
    review = models.OneToOneField(Review, on_delete=models.PROTECT)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
