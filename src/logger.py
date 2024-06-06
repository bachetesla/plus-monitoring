import logging
import json
import sys

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs log records as JSON strings.

    Attributes:
    - fmt_dict (dict): Mapping of log record attributes to JSON keys. Defaults to {"message": "message"}.
    - time_format (str): Time format string for log timestamps. Defaults to "%Y-%m-%dT%H:%M:%S".
    - msec_format (str): Microsecond format string appended to the time format. Defaults to "%s.%03dZ".
    """

    def __init__(self, fmt_dict: dict = None, time_format: str = "%Y-%m-%dT%H:%M:%S", msec_format: str = "%s.%03dZ"):
        """
        Initialize the JSON formatter with the given format dictionary and time formats.

        Parameters:
        - fmt_dict (dict): Format dictionary mapping log record attributes to JSON keys.
        - time_format (str): Time format string for log timestamps.
        - msec_format (str): Microsecond format string appended to the time format.
        """
        super().__init__()
        self.fmt_dict = fmt_dict if fmt_dict is not None else {"message": "message"}
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:
        """
        Determine if the log records should include a timestamp.

        Returns:
        - bool: True if "asctime" is in the format dictionary values, otherwise False.
        """
        return "asctime" in self.fmt_dict.values()

    def formatMessage(self, record) -> dict:
        """
        Create a dictionary of the log record attributes based on the format dictionary.

        Parameters:
        - record (LogRecord): The log record to format.

        Returns:
        - dict: A dictionary of formatted log record attributes.

        Raises:
        - KeyError: If an unknown attribute is provided in the format dictionary.
        """
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record) -> str:
        """
        Format the log record as a JSON string.

        Parameters:
        - record (LogRecord): The log record to format.

        Returns:
        - str: The JSON-formatted log record.
        """
        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        message_dict = self.formatMessage(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(message_dict, default=str)

# Initialize the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create and configure the handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Set the formatter for the handler
json_formatter = JsonFormatter({
    "level": "levelname",
    "message": "message",
    "timestamp": "asctime"
})
handler.setFormatter(json_formatter)
