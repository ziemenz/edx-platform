"""
A major issue here is how easy it is to add supplemental information (in models)
to Sequences, Courses, and Learning Contexts in general such that we can support
efficient querying.
"""
from django.db import models
from model_utils.models import TimeStampedModel

from opaque_keys.edx.django.models import CourseKeyField, LearningContextKeyField, UsageKeyField


class LearningContext(TimeStampedModel):
    """
    These are used to group Learning Sequences so that many of them can be
    pulled at once. We use this instead of a foreign key to CourseOverview
    because this table can contain things that are not courses.
    """
    id = models.BigAutoField(primary_key=True)
    context_key = LearningContextKeyField(
        max_length=255, db_index=True, unique=True, null=False
    )
    title = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=False)
    published_version = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['-published_at'])
        ]


class LearningSequence(TimeStampedModel):
    """
    In a sort of abstract way, we can think of this as a join between the pure
    piece of content represented by "usage_key", and how it's used in this
    particular context. (Folks who are aware of the origin of "usage_key" may
    find this bitterly ironic.)

    The reason why this model doesn't have a direct foreign key to CourseSection
    is because we eventually want to have LearningSequences that exist outside
    of courses. All Course-specific data lives in the CourseSection and
    CourseSectionSequence models.
    """
    id = models.BigAutoField(primary_key=True)
    learning_context = models.ForeignKey(
        LearningContext, on_delete=models.CASCADE, related_name='sequences'
    )
    # Do we really want "usage_key" terminology? Too abstract/awkward to use
    # something more generic?
    usage_key = UsageKeyField(max_length=255)
    title = models.CharField(max_length=255)

    # Separate field for when this Sequence's content was last changed?
    class Meta:
        unique_together = (
            ('learning_context', 'usage_key'),
        )


class CourseSection(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    learning_context = models.ForeignKey(
        LearningContext, on_delete=models.CASCADE, related_name='sections'
    )
    usage_key = UsageKeyField(max_length=255)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(null=False)

    class Meta:
        unique_together = (
            ('learning_context', 'usage_key'),
        )
        index_together = (
            ('learning_context', 'order'),
        )

class CourseSectionSequence(TimeStampedModel):
    """
    This is a join+ordering table, with entries that could get wiped out and
    recreated with every course publish. Do NOT make a ForeignKey against this
    table before implementing smarter replacement logic when publishing happens,
    or you'll see deletes all the time.
    """
    id = models.BigAutoField(primary_key=True)
    learning_context = models.ForeignKey(
        LearningContext, on_delete=models.CASCADE, related_name='section_sequences'
    )
    section = models.ForeignKey(CourseSection)
    sequence = models.ForeignKey(LearningSequence)
    order = models.PositiveIntegerField(null=False)

    class Meta:
        index_together = (
            ('learning_context', 'order'),
        )


# Would we want one that stores the last unit you looked at in a sequence?
