"""
Expectation for all OutlineProcessors are:

* something to do a one-time load of data for an entire course
* a method to call to emit a list of usage_keys to hide
* a method to call to add any data that is relevant to this system.

"""
from collections import defaultdict

from edx_when.api import get_dates_for_course


class ScheduleOutlineProcessor:

    def load_data_for_course(self, course_key, user):
        # (BlockUsageLocator(CourseLocator('DaveX', 'CTL.SC0x', '3T2019', None, None), 'sequential', '93efff307c9d4135865e25077eff57c0'), 'due'): datetime.datetime(2019, 12, 11, 15, 0, tzinfo=<UTC>)
        self.dates = get_dates_for_course(course_key, user)

    def sequence_keys_to_hide(self, course_outline):
        # Return a set/frozenset of usage keys to hide
        pass

    def data_to_add(self, course_outline):
        """
        This should have assignment types as well?

        Does it really need the whole course_outline, or just a set of remaining sequence usage_keys?
        """
        schedule = defaultdict(dict)
        for (usage_key, field_name), date in self.dates.items():
            if (usage_key.block_type == 'sequential') and (usage_key in course_outline.sequences):
                schedule[usage_key][field_name] = date

    #def disable_set(self, course_outline):
    #    # ???
    #   pass
