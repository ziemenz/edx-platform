"""
Testes for V1 student groups REST API.
"""

from django.urls import reverse
from rest_framework.test import APITestCase


class InitTest(APITestCase):
    """ todo """

    def test_get_init_view(self):
        path = reverse("student_groups:v1:init_view")
        assert path == "/api/student_groups/v1/init/"
        response = self.client.get(path)
        assert response.status_code == 501
