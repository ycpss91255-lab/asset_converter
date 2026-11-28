"""IR validation error."""


class IRError(ValueError):
    """Invalid IR value; ``field`` names the offending field."""

    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
