# -*- coding: utf-8 -*-
"""
student_groups Application Configuration
"""
from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from openedx.core.djangoapps.plugins.constants import PluginURLs, ProjectType


class StudentGroupsConfig(AppConfig):
    """
    Application configuration for student_groups.
    """
    name = 'lms.djangoapps.student_groups'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: 'student_groups',
                PluginURLs.REGEX: 'api/student_groups/',
                PluginURLs.RELATIVE_PATH: 'rest_api.urls',
            }
        },
    }
