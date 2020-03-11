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

    You'd think that title belongs with the usage and not in "usage in a certain
    context", but we have a suprising number of use cases that want to override
    all sorts of things. The only things safely out of bounds are the raw
    content of things HTMLBlocks. Almost everything else (grading policy,
    due dates, etc.) already exists within the context of the course.
    """
    id = models.BigAutoField(primary_key=True)
    learning_context = models.ForeignKey(
        LearningContext, on_delete=models.CASCADE, related_name='sequences'
    )
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


class CourseOutline: #(TimeStampedModel):
    """
    This model represents the hierarchical relationship for every sequence that
    _could_ be in a course. This is just the skeleton of the course, and does
    not include metadata that could be user specific (e.g. schedules, progress,
    etc.). The expectation would be that all sequence level metadata would be
    read from separate models. This only has data that is extremely specific to
    a course: namely the Sections (a.k.a. Chapters) and what sequences they
    contain. Other metadata is better associated with the sequences themselves
    in different models.
    """
    id = models.BigAutoField(primary_key=True)
    learning_context = models.OneToOneField(
        LearningContext, on_delete=models.CASCADE, related_name='course_outline'
    )
    schema_version = models.IntegerField(null=False)

    # `outline` could be a JSONField, but those are implemented in database-
    # specific ways at the moment. And we don't need deep querying capability
    # today.
    #
    # Format for the outline is:
    #
    # {
    #   "version": 1,
    #   "sections": [
    #     {
    #       "title": "Introduction",
    #       "usage_key": "block-v1:edX+DemoX+1T2020+type@chapter+block@Introduction",
    #       "sequences": [
    #         "block-v1:edX+DemoX+1T2020+type@sequential+block@welcome",
    #         "block-v1:edX+DemoX+1T2020+type@sequential+block@intro"
    #       ]
    #     }
    #   ]
    # }
    #
    # OEP-38 discourages JSON blobs like this, but we do it because:
    #
    # 1. For course navigation we almost always want to grab the entire course's
    #    outline at once.
    # 2. Sections are rarely analyzed on their own and are mostly navigational
    #    conveniences of the Course. Sequences (subsections) are first class
    #    entities with their own data models.
    # 3. Modeling nested, ordered parent-child relationships is more cumbersome
    #    in the database, and retrieving it efficiently is more awkward in the
    #    Django ORM.
    # 4. Updates happen infrequently (during course publish), and we want to
    #    rewrite the whole structure at once.
    #
    # If we need to put more metadata in Sections, it might spin out to its own
    # model, though we'll probably still want to keep all the parent/child
    # relationships in one place. We DON'T want to put that knowledge in the
    # LearningSequence model directly, because in the long run, we want to allow
    # Sequences that live outside of Courses as they exist today.
    #
    # Sigh, maybe I should just give up and make a CourseSection model instead
    # of explaining this. Yeah, that makes more sense...
    outline_data = models.TextField()
