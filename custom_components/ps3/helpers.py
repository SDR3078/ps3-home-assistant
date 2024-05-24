from functools import wraps

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .const import DOMAIN
from .API.exceptions import DeviceOffError, LockError


def request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)

        except DeviceOffError:
            raise ServiceValidationError(
                translation_domain = DOMAIN,
                translation_key = "device_off"
            )

        except LockError:
            raise ServiceValidationError(
                translation_domain = DOMAIN,
                translation_key = "lock"
            )

        except Exception as e:
            raise HomeAssistantError(e) 
        
    return wrapper