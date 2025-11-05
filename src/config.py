import os
import sys
import logging

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))

VERSION_FILE_PATH = os.path.realpath(os.path.join(ROOT_DIR, "version", "version.txt"))
version_file = open(VERSION_FILE_PATH, "r")
MODEL_VERSION = version_file.readline().strip()
version_file.close()

logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level (INFO, WARNING, ERROR, etc.)
    stream=sys.stdout,  # Direct log output to stdout
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
