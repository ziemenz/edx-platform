# pylint: disable=wrong-import-order,missing-module-docstring,wildcard-import

from import_shim.utils import alert_deprecated_import

alert_deprecated_import(__name__)

from lms.djangoapps.verify_student import *

