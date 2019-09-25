"""
Models for student_groups.
"""
from __future__ import absolute_import
from django.contrib.auth import get_user_model
from django.db import models
from simple_history.models import HistoricalRecords
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


User = get_user_model()


class Constraint(db.Model):
    """ todo """
    course_run = models.ForeignKey(CoureOverview, null=True, blank=True)

    class Meta(object):
        met


class StudentGroup(db.Model):
    """ todo """
    uuid = models.UUIDField(unique=True, editable=False, null=False)
    name = models.CharField(max_length=255)
    historical_records = HistoricalRecords()

    members = models.ManyToManyField(
        User,
        through='program_enrollments.StudentGroupMembership',
        related_name='student_groups'
    )
    constraints = models.ManyToManyField(
        Constraint,
        through='program_enrollments.StudentGroupConstraintAssignment',
        related_name='student_groups'
    )


class StudentGroupMembership(db.Model):
    """ todo """
    group = models.ForeignKey(StudentGroup, db_index=True, editable=False)
    user = models.ForeignKey(User, db_index=True, editable=False)
    historical_records = HistoricalRecords()

    class Meta(object):
        unique_together = [('uuid', 'user')]


class StudentGroupConstraintAssignment(db.Model):
    """ todo """
    constraint = models.ForeignKey(Constraint, db_index=True, editable=False)
    group = models.ForeignKey(StudentGroup, db_index=True, editable=False)
    historical_records = HistoricalRecords()

    class Meta(object):
        unique_together = [('constraint', 'group')]
