"""
    Скачивание компилятора схемы Flatbuffers при его отсутствии в рабочей директории.
"""
# pylint: disable=import-error, wrong-import-position
import os
import sys
import argparse
from i18n import t

sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from general_funcs import init_app, execute_download


def main() -> int | str:
    """
    Запуск скрипта.
    :return: Код ошибки или строка с ошибкой.
    """
    init_app(os.path.join("images", "flatbuffers-downloader-logo-clean.png"))
    parser = argparse.ArgumentParser(prog=t("main.flatc_downloader_name"),
                                     description=t("main.flatc_downloader_desc"))
    parser.add_argument("downloads_directory", nargs="?", type=str, default=os.getcwd(),
                        help=t("main.download_directory_arg"))
    args = parser.parse_args()
    return execute_download(args.downloads_directory)


if __name__ == "__main__":
    sys.exit(main())
