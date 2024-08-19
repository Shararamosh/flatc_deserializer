"""
    Скачивание компилятора схемы Flatbuffers при его отсутствии в рабочей директории.
"""
import os
import sys

from main import prepare_app, execute_download  # pylint: disable=import-error

if __name__ == "__main__":
    prepare_app("images/flatbuffers-downloader-logo-clean.png")
    sys.exit(execute_download(os.getcwd()))
