from functools import wraps

from memonto.utils.exceptions import ConfigException
from memonto.utils.logger import logger


def require_config(config_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            store = kwargs.get(config_name, None)

            if store is None and len(args) > 1:
                store = getattr(args[1], config_name, None)

            if store is None:
                logger.error(f"{config_name} is not configured.")
                raise ConfigException(f"{config_name} is not configured.")

            return func(*args, **kwargs)

        return wrapper

    return decorator
