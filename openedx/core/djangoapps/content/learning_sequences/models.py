"""

{
  "sections": [
    "": {

    }
  ]
}

"""
from django.db import models
from model_utils.models import TimeStampedModel

from opaque_keys.edx.django.models import CourseKeyField, LearningContextKeyField, UsageKeyField


class LearningContext(TimeStampedModel):
    """

    """
    context_key = LearningContextKeyField(max_length=255)
    published_at = models.DateTimeField()
    version = models.CharField(max_length=255)

class CourseOutline(TimeStampedModel):
    """
    This model represents every sequence that _could_ be in a course. This is
    just the skeleton of the course, and does not include metadata that could
    be user specific (e.g. schedules, progress, etc.). The expectation would be
    that all sequence level metadata would be read from separate models. This
    only has data that is extremely specific to a course: namely the Sections
    (a.k.a. Chapters) and what sequences they contain. Other metadata is better
    associated with the sequences themselves in different models.
    """
    learning_context = models.ForeignKey(LearningContext)

    # Should be a JSONField, but the only implementations of those are database
    # specific at the moment. And we don't need deep querying capability today.
    #
    # Format for the outline is:
    #
    # {
    #   "sections": [
    #     {
    #       "title": "Introduction",
    #       "usage_key": "",
    #       "sequences": [
    #         "block-v1:edX+DemoX+1T2020+type@sequential+block@welcome",
    #         "block-v1:edX+DemoX+1T2020+type@sequential+block@intro"
    #       ]
    #     }
    #   ]
    # }
    outline = models.TextField()


class LearningSequence(TimeStampedModel):
    learning_context = models.ForeignKey(LearningContext)
    usage_key = UsageKeyField(max_length=255)
    title = models.CharField(max_length=255)

