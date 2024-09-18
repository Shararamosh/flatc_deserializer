"""
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
"""
# pylint: disable=import-error, line-too-long, too-many-branches
import logging
import os
import sys
from locale import getdefaultlocale
from shutil import which
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames, askdirectory
from concurrent.futures import ThreadPoolExecutor, as_completed
from warnings import filterwarnings

import i18n
from PIL.ImageTk import PhotoImage
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from flatc_download_funcs import download_flatc
from flatc_funcs import deserialize


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
    # noinspection PyDeprecation
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


def get_flatc_path(root_path: str, allow_ask: bool, suppress_error: bool) -> str:
    """
    Получение пути к файлу компилятора Flatbuffers.
    :param root_path: Путь к текущей рабочей директории.
    :param allow_ask: Позволить открыть файл через диалоговое окно, если файла нет в рабочей директории.
    :param suppress_error: Игнорировать ошибку FileNotFoundError.
    :return: Путь к файлу.
    """
    flatc_path = which("flatc", path=root_path + os.sep)
    if flatc_path is not None:
        return os.path.abspath(flatc_path)
    if not allow_ask:
        if suppress_error:
            return ""
        raise FileNotFoundError(i18n.t("main.executable_not_found") % "flatc")
    if sys.platform == "win32":
        filetypes = [(i18n.t("main.exe_filetype"), "*.exe")]
    else:
        filetypes = []
    flatc_path = askopenfilename(title=i18n.t("main.tkinter_flatc_select"), filetypes=filetypes)
    if flatc_path == "":
        if suppress_error:
            return ""
        raise FileNotFoundError(i18n.t("main.executable_not_found") % "flatc")
    flatc_path = which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0])
    if flatc_path is None:
        if suppress_error:
            return ""
        raise FileNotFoundError(i18n.t("main.executable_not_found") % "flatc")
    return os.path.abspath(flatc_path)


def execute_download(root_path: str) -> int | str:
    """
    Скачивание компилятора схемы при его отсутствии в рабочей директории.
    :param root_path: Путь к текущей рабочей директории.
    :return: Код ошибки или строка об ошибке.
    """
    flatc_path = get_flatc_path(root_path, False, True)
    if flatc_path != "":
        logging.info(i18n.t("main.flatc_already_exists"), flatc_path)
    else:
        download_flatc(root_path)
    return os.EX_OK


def execute_deserialize(flatc_path: str, schema_path: str, binary_paths: list[str], output_path:
str) -> (int | str):
    """
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
    :param flatc_path: Путь к файлу компилятора схемы.
    :param schema_path: Путь к файлу схемы.
    :param binary_paths: Список путей к бинарным файлам.
    :param output_path: Путь к директории вывода для десериализованных файлов.
    :return: Код ошибки или строка об ошибке.
    """
    if not os.path.isfile(flatc_path):
        raise FileNotFoundError(i18n.t("main.file_not_found") % flatc_path)
    if which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0]) is None:
        raise FileNotFoundError(i18n.t("main.file_not_executable") % flatc_path)
    if schema_path == "":
        schema_path = askopenfilename(title=i18n.t("main.tkinter_fbs_select"),
                                      filetypes=[(i18n.t("main.fbs_filetype"), "*.fbs")])
        if schema_path == "":
            return os.EX_OK
    elif not os.path.isfile(schema_path):
        raise FileNotFoundError(i18n.t("main.file_not_found") % schema_path)
    schema_name = os.path.splitext(os.path.basename(schema_path))[0]
    if len(binary_paths) < 1:
        binary_paths = askopenfilenames(title=i18n.t("main.tkinter_binaries_select"), filetypes=[
            (i18n.t("main.flatc_binary_filetype"), "*." + schema_name)])
        if len(binary_paths) < 1:
            return os.EX_OK
    else:
        binary_paths = [binary_path for binary_path in binary_paths if os.path.isfile(binary_path)]
    if output_path == "":
        output_path = askdirectory(title=i18n.t("main.tkinter_output_select"))
    elif not os.path.isdir(output_path):
        raise FileNotFoundError(i18n.t("main.directory_not_found") % output_path)
    full_size = sum(os.stat(binary_path).st_size for binary_path in binary_paths)
    with logging_redirect_tqdm():
        pbar = tqdm(total=full_size, position=0, unit="B", unit_scale=True,
                    desc=i18n.t("main.files"))
        with ThreadPoolExecutor() as executor:
            future_deserialize_binaries = {
                executor.submit(deserialize, flatc_path, schema_path, binary_path,
                                output_path): binary_path for binary_path in binary_paths}
            for future in as_completed(future_deserialize_binaries):
                binary_path = future_deserialize_binaries[future]
                pbar.set_postfix_str(binary_path)
                future.result()
                pbar.update(os.stat(binary_path).st_size)
        pbar.set_postfix_str("")
        pbar.close()
    return os.EX_OK


def get_schema_paths(root_path: str) -> list[str]:
    """
    Получение списка путей к файлам схем Flatbuffers внутри заданной корневой директории.
    :param root_path: Путь к корневой директории.
    :return: Список путей к файлам схем.
    """
    schema_paths = []
    if not os.path.isdir(root_path):
        return schema_paths
    for subdir, _, files in os.walk(root_path):
        for file in files:
            file_path = os.path.abspath(os.path.join(subdir, file))
            if os.path.splitext(file_path)[1].lower() == ".fbs":
                schema_paths.append(file_path)
    return schema_paths


def get_binary_tuples(binaries_path: str, schema_paths: list[str]) -> tuple[
    list[tuple[str, str]], int]:
    """
    Получение списка кортежей из двух элементов: (путь к бинарному файлу, путь к соответствующему ему файлу схемы)
    :param binaries_path: Список путей к бинарным файлам.
    :param schema_paths: Список путей к файлам схем.
    :return: Кортеж из двух строковых элементов.
    """
    binary_tuples = []
    full_size = 0
    for subdir, _, files in os.walk(binaries_path):
        for file in files:
            file_path = os.path.abspath(os.path.join(subdir, file))
            for schema_path in schema_paths:
                if os.path.splitext(os.path.basename(schema_path))[0].casefold() == \
                        os.path.splitext(file)[1][1:].casefold():
                    binary_tuples.append((file_path, schema_path))
                    full_size += os.stat(file_path).st_size
                    break
    return binary_tuples, full_size


def execute_deserialize_batch(flatc_path: str, schemas_path: str, binaries_path: str,
                              output_path: str) -> (int | str):
    """
    Десериализация всех файлов Flatbuffers в директории по всем схемам из другой директории.
    :param flatc_path: Путь к файлу компилятора схемы.
    :param schemas_path: Путь к директории с файлами схем.
    :param binaries_path: Путь к директории с бинарными файлами.
    :param output_path: Путь к директории вывода.
    :return: Код ошибки или строка об ошибке.
    """
    if not os.path.isfile(flatc_path):
        raise FileNotFoundError(i18n.t("main.file_not_found") % flatc_path)
    if which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0]) is None:
        raise FileNotFoundError(i18n.t("main.file_not_executable") % flatc_path)
    if schemas_path == "":
        schemas_path = askdirectory(title=i18n.t("main.tkinter_fbs_directory_select"))
        if schemas_path == "":
            return os.EX_OK
    elif not os.path.isdir(schemas_path):
        raise FileNotFoundError(i18n.t("main.directory_not_found") % schemas_path)
    if binaries_path == "":
        binaries_path = askdirectory(title=i18n.t("main.tkinter_binary_directory_select"))
        if binaries_path == "":
            return os.EX_OK
    elif not os.path.isdir(binaries_path):
        raise FileNotFoundError(i18n.t("main.directory_not_found") % binaries_path)
    if output_path == "":
        output_path = askdirectory(title=i18n.t("main.tkinter_output_select"))
        if output_path == "":
            output_path = os.path.split(flatc_path)[0]
    elif not os.path.isdir(output_path):
        raise FileNotFoundError(i18n.t("main.directory_not_found") % output_path)
    schema_paths = get_schema_paths(schemas_path)
    if len(schema_paths) < 1:
        logging.info(i18n.t("main.no_schema_files_found"), binaries_path)
        return os.EX_OK
    binary_tuples, full_size = get_binary_tuples(binaries_path, schema_paths)
    with logging_redirect_tqdm():
        pbar = tqdm(total=full_size, position=0, unit="B", unit_scale=True,
                    desc=i18n.t("main.files"))
        with ThreadPoolExecutor() as executor:
            future_deserialize_binaries = {
                executor.submit(deserialize, flatc_path, schema_path, binary_path,
                                output_path + os.sep +
                                os.path.split(os.path.relpath(binary_path, binaries_path))[
                                    0]): binary_path for binary_path, schema_path in binary_tuples}
            for future in as_completed(future_deserialize_binaries):
                binary_path = future_deserialize_binaries[future]
                pbar.set_postfix_str(binary_path)
                future.result()
                pbar.update(os.stat(binary_path).st_size)
        pbar.set_postfix_str("")
        pbar.close()
    return os.EX_OK
