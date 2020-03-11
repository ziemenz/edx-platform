import json
import logging
import pprint

from celery.task import task
from django.db import transaction
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, SignalHandler

from .api import (
    create_course_outline,
    replace_course_outline,
    CourseOutlineData,
    CourseSectionData,
    LearningSequenceData,
)
from .models import CourseOutline, LearningContext, LearningSequence

@receiver(SignalHandler.course_published)
def ls_listen_for_course_publish(sender, course_key, **kwargs):
    # update_from_modulestore.delay(course_key)
    return

    if not isinstance(course_key, CourseKey):
        return
    if course_key.deprecated:
        return
    update_from_modulestore(course_key)


log = logging.getLogger(__name__)


def update_from_modulestore(course_key):
    """
    All of this logic should be moved to api.py
    """
    def _make_section_data(section):
        return CourseSectionData(
            usage_key=section.location,
            title=section.display_name,
            sequences=[
                LearningSequenceData(
                    usage_key=sequence.location,
                    title=sequence.display_name,
                )
                for sequence in section.get_children()
            ]
        )

    # Do the expensive modulestore access before starting a transaction...
    store = modulestore()
    sections = []
    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key, depth=2)
        sections_data = [_make_section_data(section) for section in course.get_children()]
        all_seq_keys = []
        for section_data in sections_data:
            all_seq_keys.extend([seq.usage_key for seq in section_data.sequences])

        course_outline_data = CourseOutlineData(
            course_key=course_key,
            title=course.display_name,
            published_at=course.subtree_edited_on,
            published_version=str(course.course_version),  # .course_version is a BSON obj
            sections=sections_data,
            sequence_set=frozenset(all_seq_keys),
        )

    replace_course_outline(course_outline_data)



