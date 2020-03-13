"""

"""
import attr
import json
import logging
from collections import defaultdict, OrderedDict

from django.db import transaction
from opaque_keys import OpaqueKey
from opaque_keys.edx.keys import CourseKey, UsageKey

from .data import (
    CourseOutlineData, CourseSectionData, LearningSequenceData, UserCourseOutlineData,
)
from .models import (
    CourseSection, CourseSectionSequence, LearningContext, LearningSequence,
)
from .processors import ScheduleOutlineProcessor

log = logging.getLogger(__name__)


def get_course_outline_for_user(course_key, user) -> UserCourseOutlineData:

    s = ScheduleOutlineProcessor()
    s.load_data_for_course(course_key, user)

    full_course_outline = get_course_outline(course_key)
    user_course_outline = UserCourseOutlineData(
        outline=full_course_outline,  # hasn't been transformed yet, should.
        user=user,
        schedule=s.data_to_add(full_course_outline),
    )
    return user_course_outline


def get_course_outline(course_key) -> CourseOutlineData:
    # Need better error handling
    if course_key.deprecated:
        raise ValueError(
            "Learning Sequence API does not support Old Mongo courses: %s",
            course_key
        )

    learning_context = LearningContext.objects.get(context_key=course_key)
    section_models = CourseSection.objects \
                         .filter(learning_context=learning_context) \
                         .order_by('order')
    section_sequence_models = CourseSectionSequence.objects \
                                  .filter(learning_context=learning_context) \
                                  .order_by('order') \
                                  .select_related('sequence')

    # Build mapping of section.id keys to sequence lists. We do it this way and
    # pull the sections separately to accurately represent empty sections.
    sec_ids_to_sequence_list = defaultdict(list)
    seq_keys_to_sequence = {}
    for sec_seq_model in section_sequence_models:
        sequence_model = sec_seq_model.sequence
        sequence_data = LearningSequenceData(
            usage_key=sequence_model.usage_key,
            title=sequence_model.title,
        )
        seq_keys_to_sequence[sequence_data.usage_key] = sequence_data
        sec_ids_to_sequence_list[sec_seq_model.section_id].append(sequence_data)

    return CourseOutlineData(
        course_key=learning_context.context_key,
        title=learning_context.title,
        published_at=learning_context.published_at,
        published_version=learning_context.published_version,
        sections=[
            CourseSectionData(
                usage_key=section_model.usage_key,
                title=section_model.title,
                sequences=sec_ids_to_sequence_list[section_model.id]
            )
            for section_model in section_models
        ],
        sequences=seq_keys_to_sequence,
    )


def replace_course_outline(course_outline):
    """
    Replace the model data stored for the Course Outline with the contents of
    course_outline (a CourseOutlineData).

    This isn't particularly optimized at the moment.
    """
    course_key = course_outline.course_key
    log.info("Generating CourseOutline for %s", course_key)
    if course_key.deprecated:
        raise ValueError("CourseOutline generation not supported for Old Mongo courses")

    with transaction.atomic():
        # Update or create the basic LearningContext...
        learning_context = _update_learning_context(course_outline)

        # Wipe out the CourseSectionSequences join+ordering table so we can
        # delete CourseSection and LearningSequence objects more easily.
        learning_context.section_sequences.all().delete()

        _update_sections(course_outline, learning_context)
        _update_sequences(course_outline, learning_context)
        _update_course_section_sequences(course_outline, learning_context)


def _update_learning_context(course_outline):
    learning_context, created = LearningContext.objects.update_or_create(
        context_key=course_outline.course_key,
        defaults={
            'title': course_outline.title,
            'published_at': course_outline.published_at,
            'published_version': course_outline.published_version
        }
    )
    if created:
        log.info("Created new LearningContext for %s", course_outline.course_key)
    else:
        log.info("Found LearningContext for %s, updating...", course_outline.course_key)

    return learning_context


def _update_sections(course_outline, learning_context):
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


def _update_sequences(course_outline, learning_context):
    for section_data in course_outline.sections:
        for sequence_data in section_data.sequences:
            LearningSequence.objects.update_or_create(
                learning_context=learning_context,
                usage_key=sequence_data.usage_key,
                defaults={'title': sequence_data.title}
            )
    LearningSequence.objects \
        .filter(learning_context=learning_context) \
        .exclude(usage_key__in=course_outline.sequences) \
        .delete()


def _update_course_section_sequences(course_outline, learning_context):
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

########## Scratch Notes...

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