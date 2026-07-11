from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=200
    )

    github_url = models.URLField(
        blank=True,
        null=True
    )

    zip_file = models.FileField(
        upload_to='projects/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Analysis(models.Model):

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE
    )

    health_score = models.IntegerField(
        default=0
    )

    risks_found = models.IntegerField(
        default=0
    )

    recommendations = models.IntegerField(
        default=0
    )

    total_files = models.IntegerField(
        default=0
    )

    lines_of_code = models.IntegerField(
        default=0
    )

    complexity = models.FloatField(
        default=0
    )

    maintainability = models.FloatField(
        default=0
    )

    technologies = models.TextField(
        blank=True,
        default=""
    )

    total_classes = models.IntegerField(default=0)
    total_functions = models.IntegerField(default=0)
    large_files = models.IntegerField(default=0)
    test_files = models.IntegerField(default=0)

    # AI AGENT REPORTS

    architecture_report = models.TextField(
        blank=True,
        default=""
    )

    technical_debt_report = models.TextField(
        blank=True,
        default=""
    )

    risk_report = models.TextField(
        blank=True,
        default=""
    )

    recommendation_report = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.project.name