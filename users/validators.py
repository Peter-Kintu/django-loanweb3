import re
from django.core.validators import RegexValidator

class SpaceUsernameValidator(RegexValidator):
    regex = r'^[\w.@+\- ]+$'  # Added space to the regex
    message = (
        "Enter a valid username. This value may contain only letters, numbers, "
        "and @/./+/-/_/ (space) characters."
    )
    flags = 0