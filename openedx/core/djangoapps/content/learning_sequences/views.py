"""
Views that we need:

# Metadata API?
/sequence/{}/slug  # Usage Key based? Learning Context + Slug, fallback to usage
                   # key?


    slug = models.SlugField(
        max_length=255, allow_unicode=True, db_index=True, null=True, blank=False
    )

                               ('learning_context', 'slug'),


/course_outline/{}  # CourseOutline



{
  "course_key": {},
  "title": {},
  "published_at": {},
  "published_version": {},

  # The outline is central data in the learning_sequence data
  "outline": {
    "sections": [
      {
        "title": "Introduction",
        "usage_key": "block-v1:edX+DemoX+1T2020+type@chapter+block@Introduction",
        "sequences": [
          "block-v1:edX+DemoX+1T2020+type@sequential+block@welcome",
          "block-v1:edX+DemoX+1T2020+type@sequential+block@intro"
        ]
      }
    ]
  }
  "metadata": {
    # These often only apply to a small subset of sequences...
    "scheduling": {
      "assignments": {
        "block-v1:edX+DemoX+1T2020+type@sequential+block@intro": {
          "type": "Homework",
          "due": <ISO date>
        }
      }
    },
    "prereqs": {

    },
    "opencraft-estimate": {

    }
  }
}

"""
import json

import attr
from opaque_keys.edx.keys import CourseKey

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import CourseOutline, LearningContext, LearningSequence
from .api import get_course_outline_for_user


class CourseOutlineView(APIView):
    """
    Display all CourseOutline information for a given user.
    """

    class UserCourseOutlineDataSerializer(BaseSerializer):
        """Read-only serializer for CourseOutlineData for this endpoint."""
        def to_representation(self, user_course_outline_data):
            course_outline_data = user_course_outline_data.outline
            schedule = user_course_outline_data.schedule
            return {
                "course_key": str(course_outline_data.course_key),
                "title": course_outline_data.title,
                "published_at": course_outline_data.published_at,
                "published_version": course_outline_data.published_version,
                "sections": [
                    {
                        "usage_key": str(section.usage_key),
                        "title": section.title,
                        "sequences": [
                            {
                                "usage_key": str(sequence.usage_key),
                                "title": sequence.title
                            }
                            for sequence in section.sequences
                        ]
                    }
                    for section in course_outline_data.sections
                ],
                "schedule": schedule,
            }

    def get(self, request, course_key_str, format=None):
        course_key = CourseKey.from_string(course_key_str)
        course_outline_data = get_course_outline_for_user(course_key, request.user)
        serializer = self.UserCourseOutlineDataSerializer(course_outline_data)
        return Response(serializer.data)
