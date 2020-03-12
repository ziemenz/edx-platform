import logging
from typing import Dict, List #, OrderedDict

import attr
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey, UsageKey


User = get_user_model()
log = logging.getLogger(__name__)


@attr.s(frozen=True)
class LearningSequenceData:
    usage_key = attr.ib(type=UsageKey)
    title = attr.ib(type=str)


@attr.s(frozen=True)
class CourseSectionData:
    usage_key = attr.ib(type=UsageKey)
    title = attr.ib(type=str)
    sequences = attr.ib(type=List[LearningSequenceData])


@attr.s(frozen=True)
class CourseOutlineData:
    course_key = attr.ib(type=CourseKey)
    title = attr.ib(type=str)
    published_at = attr.ib()
    published_version = attr.ib()
    sections = attr.ib(type=List[CourseSectionData])
    sequences = attr.ib() # (type=OrderedDict[UsageKey, LearningSequenceData])

    class DoesNotExist(Exception):
        pass

@attr.s(frozen=True)
class UserCourseOutlineData:
    outline = attr.ib(type=CourseOutlineData)
    user = attr.ib(type=User)
    schedule = attr.ib()  # Make a real type later?
    # how to handle per-system metadata?