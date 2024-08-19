"""
    Модуль, включающий в себя функции для скачивания и распаковки последней версии компилятора
    Flatbuffers.
"""
import os
import platform
import sys
from shutil import which
from zipfile import ZipFile
from logging import info
from urllib import request

from i18n import t


def is_linux() -> bool:
    """
    Проверка, является ли данная платформа Linux.
    :return: Является ли данная платформа Linux.
    """
    return sys.platform == "cygwin" or sys.platform == "msys" or sys.platform.startswith("linux")


def get_flatc_url() -> str:
    """
    Получение URL-адреса для последней версии компилятора Flatbuffers для данной платформы.
    :return: URL-адрес.
    """
    root_url = "https://github.com/google/flatbuffers/releases/latest/download"
    if sys.platform == "win32":  # Windows.
        return root_url + "/Windows.flatc.binary.zip"
    if is_linux():  # Linux.
        return root_url + "/Linux.flatc.binary.clang++-15.zip"
    if sys.platform == "darwin":  # macOS.
        if platform.processor() == "i386":  # Intel macOS.
            return root_url + "/MacIntel.flatc.binary.zip"
        return root_url + "/Mac.flatc.binary.zip"
    raise OSError(t("main.unsupported_platform").format(platform.platform(True)))


def download_flatc(root_path: str) -> str:
    """
    Скачивание компилятора Flatbuffers в заданную папку.
    :param root_path: Путь для скачивания компилятора.
    :return: Путь к файлу компилятора.
    """
    if not os.path.isdir(root_path):
        raise FileNotFoundError(t("main.directory_not_found"), root_path)
    info(t("flatc_download_funcs.download_start"))
    zip_path, _ = request.urlretrieve(get_flatc_url())
    info(t("flatc_download_funcs.download_finish"), zip_path)
    with ZipFile(zip_path, "r") as f:
        f.extractall(root_path)
    info(t("flatc_download_funcs.unpack_path"), zip_path, root_path)
    os.remove(zip_path)
    info(t("main.file_removed"), zip_path)
    flatc_path = which("flatc", path=root_path + os.sep)
    if flatc_path is None:
        raise FileNotFoundError(t("main.executable_not_found") % "flatc")
    return os.path.abspath(flatc_path)
