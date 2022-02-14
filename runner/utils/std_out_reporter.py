import logging
import sys
from typing import Optional

from tudelft_utilities_logging.Reporter import Reporter


class StdOutReporter(Reporter):
    def log(self, level: int, msg: str, exc: Optional[BaseException] = None):
        if level >= logging.WARNING:
            print(logging.getLevelName(level) + ":" + msg, file=sys.stderr)
        else:
            print(logging.getLevelName(level) + ":" + msg)
