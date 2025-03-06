"""
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
"""
# pylint: disable=import-error, line-too-long, too-many-branches
import logging
import os
import sys
import errno
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


def get_resource_path(file_path: str) -> str:
    """
    Получение пути к файлу или директории внутри проекта, если используется PyInstaller или Nuitka.
    :param file_path: Изначальный путь к файлу или директории.
    :return: Изменённый путь к файлу или директории.
    """
    if "NUITKA_ONEFILE_PARENT" in os.environ:
        base_path = os.path.dirname(sys.executable)
    elif hasattr(sys, "_MEIPASS"):
        base_path = getattr(sys, "_MEIPASS")
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, file_path)


def init_app(icon_path: str):
    """
    Инициализация приложения (логирование, локализация, модуль Tkinter).
    :param icon_path: Путь к иконке для диалоговых окон Tkinter.
    """
    sys.tracebacklimit = 0
    init_logging()
    init_localization()
    init_tkinter(icon_path)


def init_logging():
    """
    Инициализация логирования.
    """
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)
    filterwarnings("ignore", category=DeprecationWarning)


def init_localization():
    """
    Инициализация локализации.
    """
    # noinspection PyDeprecation
    i18n.set("locale", getdefaultlocale()[0])  # pylint: disable=deprecated-method
    i18n.set("fallback", "en_US")
    i18n.load_path.append(get_resource_path("localization"))
    i18n.set("file_format", "yml")
    i18n.set("filename_format", "{namespace}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.set("use_locale_dirs", True)


def init_tkinter(icon_path: str):
    """
    Подготовка модуля Tkinter.
    :param icon_path: Путь к иконке для диалоговых окон Tkinter.
    """
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
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.executable_not_found") % "flatc")
    if sys.platform == "win32":
        filetypes = [(i18n.t("main.exe_filetype"), "*.exe")]
    else:
        filetypes = []
    flatc_path = askopenfilename(title=i18n.t("main.tkinter_flatc_select"), filetypes=filetypes)
    if flatc_path == "":
        if suppress_error:
            return ""
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.executable_not_found") % "flatc")
    flatc_path = which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0])
    if flatc_path is None:
        if suppress_error:
            return ""
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.executable_not_found"), "flatc")
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
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.file_not_found") % flatc_path)
    if which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0]) is None:
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.file_not_executable") % flatc_path)
    if schema_path == "":
        schema_path = askopenfilename(title=i18n.t("main.tkinter_fbs_select"),
                                      filetypes=[(i18n.t("main.fbs_filetype"), "*.fbs")])
        if schema_path == "":
            raise IOError(errno.EIO, i18n.t("main.no_file_selected"))
    if not os.path.isfile(schema_path):
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.file_not_found") % schema_path)
    schema_name = os.path.splitext(os.path.basename(schema_path))[0]
    if len(binary_paths) < 1:
        binary_paths = askopenfilenames(title=i18n.t("main.tkinter_binaries_select"), filetypes=[
            (i18n.t("main.flatc_binary_filetype"), "*." + schema_name)])
        if len(binary_paths) < 1:
            raise IOError(errno.EIO, i18n.t("main.no_files_selected"))
    else:
        binary_paths = [binary_path for binary_path in binary_paths if os.path.isfile(binary_path)]
    if output_path == "":
        output_path = askdirectory(title=i18n.t("main.tkinter_output_select"))
        if output_path == "":
            raise IOError(errno.EIO, i18n.t("main.no_directory_selected"))
    elif not os.path.isdir(output_path):
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.directory_not_found") % output_path)
    with logging_redirect_tqdm():
        pbar = tqdm(total=len(binary_paths), desc=i18n.t("main.files"))
        with ThreadPoolExecutor() as executor:
            future_deserialize_binaries = {
                executor.submit(deserialize, flatc_path, schema_path, binary_path,
                                output_path): binary_path for binary_path in binary_paths}
            for future in as_completed(future_deserialize_binaries):
                binary_path = future_deserialize_binaries[future]
                pbar.set_postfix_str(binary_path)
                future.result()
                pbar.update(1)
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


def get_binary_tuples(binary_paths: list[str], schema_paths: list[str], return_empty_pairs: bool = False) -> list[tuple[str, str]]:
    """
    Получение списка кортежей из двух элементов: (путь к бинарному файлу, путь к соответствующему ему файлу схемы)
    :param binary_paths: Список путей к бинарным файлам или директориям с ними.
    :param schema_paths: Список путей к файлам схем.
    :param return_empty_pairs: True, если необходимо добавить в список файлы, к которым нет схем.
    :return: Кортеж из двух строковых элементов.
    """
    binary_tuples = []
    for _, binary_path in enumerate(binary_paths):
        if os.path.isfile(binary_path):
            schema_found = False
            file_path = os.path.abspath(binary_path)
            for schema_path in schema_paths:
                schema_ext = os.path.splitext(os.path.basename(schema_path))[0]
                file_ext = os.path.splitext(file_path)[1][1:]
                if schema_ext.casefold() == file_ext.casefold():
                    schema_found = True
                    binary_tuples.append((file_path, schema_path))
                    break
            if not schema_found and return_empty_pairs:
                binary_tuples.append((file_path, ""))
            continue
        if not os.path.isdir(binary_path):
            if return_empty_pairs:
                binary_tuples.append((binary_path, ""))
            continue
        for subdir, _, files in os.walk(binary_path):
            for file in files:
                schema_found = False
                file_path = os.path.abspath(os.path.join(subdir, file))
                for schema_path in schema_paths:
                    schema_ext = os.path.splitext(os.path.basename(schema_path))[0]
                    file_ext = os.path.splitext(file_path)[1][1:]
                    if schema_ext.casefold() == file_ext.casefold():
                        schema_found = True
                        binary_tuples.append((file_path, schema_path))
                        break
                if not schema_found and return_empty_pairs:
                    binary_tuples.append((file_path, ""))
    return binary_tuples


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
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.file_not_found") % flatc_path)
    if which(os.path.split(flatc_path)[1], path=os.path.split(flatc_path)[0]) is None:
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.file_not_executable") % flatc_path)
    if schemas_path == "":
        schemas_path = askdirectory(title=i18n.t("main.tkinter_fbs_directory_select"))
        if schemas_path == "":
            raise IOError(errno.EIO, i18n.t("main.no_directory_selected"))
    if not os.path.isdir(schemas_path):
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.directory_not_found") % schemas_path)
    if binaries_path == "":
        binaries_path = askdirectory(title=i18n.t("main.tkinter_binary_directory_select"))
        if binaries_path == "":
            raise IOError(errno.EIO, i18n.t("main.no_directory_selected"))
    if not os.path.isdir(binaries_path):
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.directory_not_found") % binaries_path)
    if output_path == "":
        output_path = askdirectory(title=i18n.t("main.tkinter_output_select"))
        if output_path == "":
            output_path = os.path.split(flatc_path)[0]
            if output_path == "":
                raise IOError(errno.EIO, i18n.t("main.no_directory_selected"))
    if not os.path.isdir(output_path):
        raise FileNotFoundError(errno.ENOENT, i18n.t("main.directory_not_found") % output_path)
    schema_paths = get_schema_paths(schemas_path)
    if len(schema_paths) < 1:
        logging.info(i18n.t("main.no_schema_files_found"), binaries_path)
        return os.EX_OK
    binary_tuples = get_binary_tuples([binaries_path], schema_paths)
    with logging_redirect_tqdm():
        pbar = tqdm(total=len(binary_tuples), desc=i18n.t("main.files"))
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
                pbar.update(1)
        pbar.set_postfix_str("")
        pbar.close()
    return os.EX_OK
