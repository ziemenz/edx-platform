import json
import logging
import pprint

from celery.task import task
from django.db import transaction
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, SignalHandler

from .api import create_course_outline
from .models import CourseOutline, LearningContext, LearningSequence

@receiver(SignalHandler.course_published)
def ls_listen_for_course_publish(sender, course_key, **kwargs):
    # update_from_modulestore.delay(course_key)
    if not isinstance(course_key, CourseKey):
        return
    if course_key.deprecated:
        return
    update_from_modulestore(course_key)


log = logging.getLogger(__name__)


# @task() # temporarily running this inline for easier debugging.
def update_from_modulestore(course_key):
    """
    All of this logic should be moved to api.py
    """
    # Do the expensive modulestore access before starting a transaction...
    store = modulestore()
    sections = []
    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key, depth=2)
        course_title = course.display_name
        published_at = course.subtree_edited_on
        published_version = str(course.course_version)
        for section in course.get_children():
            sections.append(
                {
                    "title": section.display_name,
                    "usage_key": section.location,
                    "sequences": [
                        {"title": seq.display_name, "usage_key": seq.location}
                        for seq in section.get_children()
                    ]
                }
            )

    # Do all our actual updates in the transaction...
    # this should be put into api.py at some point when our data structures are
    # clearer...
    with transaction.atomic():
        # Update or create the basic LearninContext...
        log.info("Creating LearningContext %s", course_key)
        lc, _created = LearningContext.objects.update_or_create(
            context_key=course_key,
            defaults={
                'title': course_title,
                'published_at': published_at,
                'published_version': published_version
            }
        )

        # In case any sequences were deleted in the last publish, we just wipe
        # them all out and rebuild with the ones we see with this publish.
        #
        # todo: We could replace this with something that turns it inactive?
        # Mostly relevant if we start storing user state related to this...
        log.info("Removing old Sequences from %s", course_key)
        LearningSequence.objects.filter(learning_context=lc).delete()

        log.info("Creating new Sequences for %s", course_key)
        for section in sections:
            sequences = [
                LearningSequence(usage_key=seq["usage_key"], title=seq["title"])
                for seq in section["sequences"]
            ]
            lc.sequences.add(*sequences, bulk=False) # bulk=True doesn't for new (unsaved) models.

        outline_data = {
            "sections": [
                {
                    "title": section["title"],
                    "usage_key": str(section["usage_key"]),
                    "sequences": [
                        {
                            "title": seq["title"],
                            "usage_key": str(seq["usage_key"]),
                        }
                        for seq in section["sequences"]
                    ]
                }
                for section in sections
            ]
        }

        log.info("Updating the outline for %s", course_key)
        CourseOutline.objects.update_or_create(
            learning_context=lc,
            defaults={
                'schema_version': 1,
                'outline_data': json.dumps(outline_data)
            }
        )

