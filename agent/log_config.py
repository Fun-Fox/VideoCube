import sys

from loguru import logger

logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("file_{time}.log",rotation="500 MB")
