from functools import wraps

from memonto.utils.exceptions import ConfigException
from memonto.utils.logger import logger


def require_config(*config_names):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if getattr(self, "ephemeral", False):
                return func(self, *args, **kwargs)

            for config_name in config_names:
                store = getattr(self, config_name, None)

                if store is None:
                    logger.warning(f"{config_name} is not configured.")
                    raise ConfigException(f"{config_name} is not configured.")

            return func(self, *args, **kwargs)

        return wrapper

    return decorator
