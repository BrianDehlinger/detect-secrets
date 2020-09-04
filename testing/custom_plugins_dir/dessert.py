import re

from detect_secrets.plugins.base import classproperty
from detect_secrets.plugins.base import RegexBasedDetector


class DessertDetector(RegexBasedDetector):
    """Scans for tasty desserts."""
    secret_type = 'Tasty Dessert'

    @classproperty
    def disable_flag_text(cls):
        return 'no-dessert-scan'

    denylist = (
        re.compile(
            r"(sweet potato)",
            re.IGNORECASE,
        ),
    )
