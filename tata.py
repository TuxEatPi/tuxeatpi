import logging
from tuxeatpi.libs.settings import Settings

logger = logging.getLogger(name="TuxEatPi")   
settings = Settings('tuxeatpi-conf.yml',  logger)
settings.save()
