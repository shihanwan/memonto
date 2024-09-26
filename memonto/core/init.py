from memonto.utils.logger import setup_logger


def init(debug: bool) -> None:
    setup_logger(debug=debug)
