import sys
from loguru import logger


def setup_logger(debug: bool) -> None:
    logger.remove()

    if debug:
        logger.add("memonto.log", level="DEBUG")
        logger.add(sys.stdout, level="DEBUG")
        logger.debug("Debug mode enabled.")
    else:
        logger.add("memonto.log", level="INFO")
        logger.info("Debug mode disabled.")


__all__ = ["logger"]
