"""
Views for V1 student groups REST API.
"""
from __future__ import absolute_import, unicode_literals

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class InitView(APIView):
    """ todo """

    def get(self, request, *args, **kwargs):
        """ todo """
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
