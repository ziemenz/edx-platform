"""

"""
import attr
import json
import logging
from typing import List

from django.contrib.auth import get_user_model
from django.db import transaction
from opaque_keys import OpaqueKey
from opaque_keys.edx.keys import CourseKey, UsageKey

from .models import (
    CourseSection, CourseSectionSequence, LearningContext, LearningSequence
)

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
    sequence_set = attr.ib(type=frozenset)
    #@property
    #def sequence_set(self):


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

    full_course_outline = get_course_outline(course_key)
    user_course_outline = UserCourseOutlineData(
        outline=full_course_outline,  # hasn't been transformed yet, should.
        user=user,
        schedule=s.data_to_add(full_course_outline),
    )
    return user_course_outline



#def get_course_outline_data(course_key):
#    try:
#        lc = LearningContext.objects \
#                .select_related('course_outline') \
#                .prefetch_related('sequences') \
#                .get(context_key=course_key)
#    except LearningContext.NotFound:
#        raise CourseOutlineData.DoesNotExist(
#            "No outline for course {}".format(course_key)
#        )
#
#    course_outline_data = _create_course_outline_data(lc)
#
#    return course_outline_data







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


from collections import defaultdict
from operator import attrgetter
from itertools import groupby


def get_course_outline(course_key):
    # Need better error handling
    if course_key.deprecated:
        raise ValueError(
            "Learning Sequence API does not support Old Mongo courses: %s",
            course_key
        )

    learning_context = LearningContext.objects.get(context_key=course_key)
    section_sequences = CourseSectionSequence.objects \
                            .filter(learning_context=learning_context) \
                            .order_by('order') \
                            .select_related('sequence')

    # Build mapping of section.id keys to sequence lists. We do it this way and
    # pull the sections separately to accurately represent empty sections.
    section_ids_to_sequences = defaultdict(list)
    for sec_seq in section_sequences:
        section_ids_to_sequences[sec_seq.section_id].append(sec_seq.sequence)

    sections = CourseSection.objects \
                   .filter(learning_context=learning_context) \
                   .order_by('order')

    outline_data = CourseOutlineData(
        course_key=learning_context.context_key,
        title=learning_context.title,
        published_at=learning_context.published_at,
        published_version=learning_context.published_version,
        sections=[
            CourseSectionData(
                usage_key=section.usage_key,
                title=section.title,
                sequences=[
                    LearningSequenceData(
                        usage_key=sequence.usage_key, title=sequence.title,
                    )
                    for sequence in section_ids_to_sequences[section.id]
                ]
            )
            for section in sections
        ],
        sequence_set=set()
    )

    # hack code pending changes in CourseOutlineData data structure
    for section in outline_data.sections:
        for seq in section.sequences:
            outline_data.sequence_set.add(seq.usage_key)
    return outline_data

def create_course_outline(course_outline_data):
    pass

def replace_course_outline(course_outline):
    """
    Replace the model data stored for the Course Outline with the contents of
    course_outline (a CourseOutlineData).

    This isn't particularly optimized at the moment.
    """
    def update_learning_context():
        learning_context, created = LearningContext.objects.update_or_create(
            context_key=course_outline.course_key,
            defaults={
                'title': course_outline.title,
                'published_at': course_outline.published_at,
                'published_version': course_outline.published_version
            }
        )
        if created:
            log.info("Created new LearningContext for %s", course_key)
        else:
            log.info("Found LearningContext for %s, updating...", course_key)

        return learning_context

    def update_sections(learning_context):
        # Add/update relevant sections...
        for order, section_data in enumerate(course_outline.sections):
            CourseSection.objects.update_or_create(
                learning_context=learning_context,
                usage_key=section_data.usage_key,
                defaults={
                    'title': section_data.title,
                    'order': order,
                }
            )
        # Delete sections that we don't want any more
        section_usage_keys_to_keep = [
            section_data.usage_key for section_data in course_outline.sections
        ]
        CourseSection.objects \
            .filter(learning_context=learning_context) \
            .exclude(usage_key__in=section_usage_keys_to_keep) \
            .delete()

    def update_sequences(learning_context):
        for section_data in course_outline.sections:
            for sequence_data in section_data.sequences:
                LearningSequence.objects.update_or_create(
                    learning_context=learning_context,
                    usage_key=sequence_data.usage_key,
                    defaults={'title': sequence_data.title}
                )
        LearningSequence.objects \
            .filter(learning_context=learning_context) \
            .exclude(usage_key__in=course_outline.sequence_set) \
            .delete()

    def update_course_section_sequences(learning_context):
        section_models = {
            section_model.usage_key: section_model
            for section_model
            in CourseSection.objects.filter(learning_context=learning_context).all()
        }
        sequence_models = {
            sequence_model.usage_key: sequence_model
            for sequence_model
            in LearningSequence.objects.filter(learning_context=learning_context).all()
        }

        for order, section_data in enumerate(course_outline.sections):
            for sequence_data in section_data.sequences:
                CourseSectionSequence.objects.update_or_create(
                    learning_context=learning_context,
                    section=section_models[section_data.usage_key],
                    sequence=sequence_models[sequence_data.usage_key],
                    defaults={'order': order},
                )


    course_key = course_outline.course_key
    log.info("Generating CourseOutline for %s", course_key)
    if course_key.deprecated:
        raise ValueError("CourseOutline generation not supported for Old Mongo courses")

    with transaction.atomic():
        # Update or create the basic LearningContext...
        learning_context = update_learning_context()

        # Wipe out the CourseSectionSequences join+ordering table so we can
        # delete CourseSection and LearningSequence objects more easily.
        learning_context.section_sequences.all().delete()

        update_sections(learning_context)
        update_sequences(learning_context)
        update_course_section_sequences(learning_context)



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