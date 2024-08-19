"""
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
"""
import logging
import os
import sys
from locale import getdefaultlocale
from shutil import which
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames, askdirectory
from warnings import filterwarnings

import i18n
from PIL.ImageTk import PhotoImage
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from flatc_download_funcs import download_flatc  # pylint: disable=import-error
from flatc_funcs import deserialize  # pylint: disable=import-error


def get_resource_path(filename: str) -> str:
    """
    Получение пути к файлу или директории, если используется PyInstaller.
    :param filename: Изначальный путь к файлу или директории.
    :return: Изменённый путь к файлу или директории.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(getattr(sys, "_MEIPASS"), filename)
    return filename


def prepare_app(icon_path: str):
    """
    Подготовка приложения к выполнению.
    :param icon_path: Путь к иконке для диалоговых окон Tkinter.
    """
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)
    filterwarnings("ignore", category=DeprecationWarning)
    i18n.set("locale", getdefaultlocale()[0])  # pylint: disable=deprecated-method
    i18n.set("fallback", "en_US")
    i18n.load_path.append(get_resource_path("localization"))
    i18n.set("file_format", "yml")
    i18n.set("filename_format", "{namespace}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.set("use_locale_dirs", True)
    root = Tk()
    root.withdraw()
    root.iconphoto(True, PhotoImage(file=get_resource_path(icon_path)))


def get_flatc_path(allow_system_path: bool, root_path: str, allow_ask: bool,
                   suppress_ask_error: bool = True) -> str:
    """
    Получение пути к файлу компилятора Flatbuffers.
    :param allow_system_path: Позволить искать файл в системных директориях Python.
    :param root_path: Путь к текущей рабочей директории.
    :param allow_ask: Позволить открыть файл через диалоговое окно, если файла нет в рабочей директории.
    :param suppress_ask_error: Игнорировать ошибку FileNotFoundError, если не выводится диалоговое окно для файла.
    :return: Путь к файлу.
    """
    if allow_system_path:
        flatc_path = which("flatc")
        if flatc_path is not None:
            return os.path.abspath(flatc_path)
    flatc_path = which("flatc", path=root_path + os.sep)
    if flatc_path is not None:
        return os.path.abspath(flatc_path)
    if not allow_ask:
        if suppress_ask_error:
            return ""
        raise FileNotFoundError(i18n.t("main.executable_not_found") % "flatc")
    if sys.platform == "win32":
        filetypes = [(i18n.t("main.exe_filetype"), "*.exe")]
    else:
        filetypes = []
    flatc_path = askopenfilename(title=i18n.t("main.tkinter_flatc_select"), filetypes=filetypes)
    if flatc_path == "":
        raise FileNotFoundError(i18n.t("main.executable_not_found") % "flatc")
    flatc_path = which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0])
    if flatc_path is None:
        raise FileNotFoundError(i18n.t("main.executable_not_found") % "flatc")
    return os.path.abspath(flatc_path)


def execute_download(root_path: str) -> int | str:
    """
    Скачивание компилятора схемы при его отсутствии в рабочей директории.
    :param root_path: Путь к текущей рабочей директории.
    :return: Код ошибки или строка об ошибке.
    """
    flatc_path = get_flatc_path(False, root_path, False, True)
    if flatc_path != "":
        logging.info(i18n.t("main.flatc_already_exists"), flatc_path)
    else:
        download_flatc(os.getcwd())
    return os.EX_OK


def execute_deserialize(flatc_path: str) -> int | str:
    """
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
    :param flatc_path: Путь к файлу компилятора схемы.
    :return: Код ошибки или строка об ошибке.
    """
    if not os.path.isfile(flatc_path):
        raise FileNotFoundError(i18n.t("main.file_not_found") % flatc_path)
    if which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0]) is None:
        raise FileNotFoundError(i18n.t("main.file_not_executable") % flatc_path)
    schema_path = askopenfilename(title=i18n.t("main.tkinter_fbs_select"),
                                  filetypes=[(i18n.t("main.fbs_filetype"), "*.fbs")])
    if schema_path == "":
        return os.EX_OK
    schema_name = os.path.splitext(os.path.basename(schema_path))[0]
    binary_paths = askopenfilenames(title=i18n.t("main.tkinter_binaries_select"),
                                    filetypes=[
                                        (i18n.t("main.flatc_binary_filetype"), "*." + schema_name)])
    output_path = askdirectory(title=i18n.t("main.tkinter_output_select"))
    full_size = sum(os.stat(binary_path).st_size for binary_path in binary_paths)
    with logging_redirect_tqdm():
        pbar = tqdm(total=full_size, position=0, unit="B", unit_scale=True,
                    desc=i18n.t("main.files"))
        for binary_path in binary_paths:
            pbar.set_postfix_str(binary_path)
            pbar.clear()
            deserialize(flatc_path, schema_path, binary_path, output_path)
            pbar.update(os.stat(binary_path).st_size)
        pbar.set_postfix_str("")
        pbar.close()
    return os.EX_OK
