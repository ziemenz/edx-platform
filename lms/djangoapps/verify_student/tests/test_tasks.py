# Lots of patching to stub in our own settings, and HTTP posting
import ddt
import mock
from django.conf import settings
from mock import patch

from common.test.utils import MockS3BotoMixin
from student.tests.factories import UserFactory
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from verify_student.tests.test_models import (
    FAKE_SETTINGS,
    TestVerification,

    mock_software_secure_post_unavailable
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

LOGGER_NAME = 'lms.djangoapps.verify_student.tasks'


@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@ddt.ddt
class TestPhotoVerificationTasks(TestVerification, MockS3BotoMixin, ModuleStoreTestCase):
    def create_and_submit(self):
        """Helper method to create a generic submission and send it."""

        attempt = SoftwareSecurePhotoVerification(user=self.user)
        attempt.upload_face_image("Just pretend this is image data")
        attempt.upload_photo_id_image("Hey, we're a photo ID")
        attempt.mark_ready()
        attempt.submit()

        return attempt

    @mock.patch('lms.djangoapps.verify_student.tasks.log')
    def test_logs_for_retry_until_failure(self, mock_log):
        retry_max_attempts = settings.SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS
        with patch('lms.djangoapps.verify_student.tasks.requests.post', new=mock_software_secure_post_unavailable):
            attempt = self.create_and_submit()
            username = attempt.user.username
            self.assertEqual(mock_log.error.call_count, 8)
            mock_log.error.assert_called_with(
                'Software Secure submission failed for user %r, setting status to must_retry',
                username,
                exc_info=True
            )
            for current_attempt in range(retry_max_attempts):
                mock_log.error.assert_any_call(
                    ('Retrying sending request to Software Secure for user: %r, Receipt ID: %r '
                     'attempt#: %s of %s'),
                    username,
                    attempt.receipt_id,
                    current_attempt,
                    settings.SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS,
                )
