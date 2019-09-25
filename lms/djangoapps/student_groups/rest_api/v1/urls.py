"""
Student Groups API v1 URLs.
"""
from __future__ import absolute_import

from django.conf.urls import url

from .views import InitView

app_name = 'v1'

urlpatterns = [
    url(
        r'^init/$',
        InitView.as_view(),
        name='init_view'
    ),
]
