"""
    Скачивание компилятора схемы Flatbuffers при его отсутствии в рабочей директории.
"""
# pylint: disable=import-error
import os
import sys
import argparse
from i18n import t

from main import init_app, execute_download

if __name__ == "__main__":
    sys.tracebacklimit = 0
    init_app("images/flatbuffers-downloader-logo-clean.png")
    parser = argparse.ArgumentParser(prog=t("main.flatc_downloader_name"),
                                     description=t("main.flatc_downloader_desc"))
    parser.add_argument("downloads_directory", nargs="?", type=str, default=os.getcwd(),
                        help=t("main.download_directory_arg"))
    args = parser.parse_args()
    sys.exit(execute_download(args.downloads_directory))
