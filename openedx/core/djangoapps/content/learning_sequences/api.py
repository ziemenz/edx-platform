"""

"""
import attr
import json
from typing import List

from django.contrib.auth import get_user_model
from opaque_keys import OpaqueKey
from opaque_keys.edx.keys import CourseKey, UsageKey

from .models import LearningContext

User = get_user_model()


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
    sequence_set = attr.ib(type=frozenset)

    class DoesNotExist(Exception):
        pass

@attr.s(frozen=True)
class UserCourseOutlineData:
    outline = attr.ib(type=CourseOutlineData)
    user = attr.ib(type=User)


    schedule = attr.ib()  # Make a real type later?
    # how to handle per-system metadata?


def get_course_outline_for_user(course_key, user):

    s = ScheduleOutlineProcessor()
    s.load_data_for_course(course_key, user)

    full_course_outline = get_course_outline_data(course_key)
    user_course_outline = UserCourseOutlineData(
        outline=full_course_outline,  # hasn't been transformed yet, should.
        user=user,
        schedule=s.data_to_add(full_course_outline),
    )
    return user_course_outline



def get_course_outline_data(course_key):
    try:
        lc = LearningContext.objects \
                .select_related('course_outline') \
                .prefetch_related('sequences') \
                .get(context_key=course_key)
    except LearningContext.NotFound:
        raise CourseOutlineData.DoesNotExist(
            "No outline for course {}".format(course_key)
        )

    course_outline_data = _create_course_outline_data(lc)

    return course_outline_data



def _create_course_outline_data(learning_context):
    """
    All this mucking in JSON is actually pretty cumbersome.
    """
    outline_skeleton = json.loads(learning_context.course_outline.outline_data)
    sequence_set = set(seq.usage_key for seq in learning_context.sequences.all())

    return CourseOutlineData(
        course_key=learning_context.context_key,
        title=learning_context.title,
        published_at=learning_context.published_at,
        published_version=learning_context.published_version,
        sections=[
            CourseSectionData(
                usage_key=UsageKey.from_string(section['usage_key']),
                title=section['title'],
                sequences=[
                    LearningSequenceData(
                        usage_key=UsageKey.from_string(sequence['usage_key']),
                        title=sequence['title'],
                    )
                    for sequence in section['sequences']
                ]
            )
            for section in outline_skeleton['sections']
        ],
        sequence_set=frozenset(sequence_set)
    )


def create_course_outline(outline):
    pass


from edx_when.api import get_dates_for_course

class ScheduleOutlineProcessor:

    def load_data_for_course(self, course_key, user):
        self.dates = get_dates_for_course(course_key, user)

    def sequence_keys_to_hide(self, course_outline):
        # Return a set/frozenset of usage keys to hide
        pass

    def data_to_add(self, course_outline):
        """"
        (BlockUsageLocator(CourseLocator('DaveX', 'CTL.SC0x', '3T2019', None, None), 'sequential', '93efff307c9d4135865e25077eff57c0'), 'due'): datetime.datetime(2019, 12, 11, 15, 0, tzinfo=<UTC>)
        """
        return {
            str(usage_key): {'due': date}
            for (usage_key, field_name), date in self.dates.items()
            if (usage_key.block_type == 'sequential') # and (usage_key in course_outline.sequence_set)
        }


    #def disable_set(self, course_outline):
    #    # ???
    #   pass


def process():

    # Phase 1:
    sequence_keys_to_hide = set()
    for processor in processors:
        sequence_keys_to_hide.update(processor.sequence_keys_to_hide())

    # What is the desired behavior if you have a Chapter with no sequences?
    # I guess we keep it?
    outline_with_hidden_stuff = hide_sequences

    for processor in processors:
        pass