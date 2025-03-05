"""
    GUI app for deserializing flatbuffers files.
"""
# pylint: disable=import-error, too-many-instance-attributes, too-many-statements
import os
import tkinter.filedialog
from collections.abc import Callable
from importlib import import_module
from tkinter import ttk

from PIL.ImageTk import PhotoImage
from PIL import Image
from i18n import t
import customtkinter as CTk
from CTkMenuBar import CTkMenuBar
from CTkMessagebox import CTkMessagebox

from main import init_localization, get_resource_path, execute_download, get_flatc_path, \
    get_binary_tuples
from flatc_funcs import deserialize


class Deserializer(CTk.CTk):
    """
    GUI for batch deserialization of flatbuffers files.
    """

    def __init__(self):
        super().__init__()
        width = int(self.winfo_screenwidth() / 2)
        height = int(self.winfo_screenheight() / 2)
        self.geometry(f"{width}x{height}")
        self.title(t("main.flatc_deserializer_name"))
        self.wm_iconbitmap()
        img = Image.open(get_resource_path("images/flatbuffers-logo-clean.png"))
        self.iconphoto(True, PhotoImage(img))
        self.top_menu = CTkMenuBar(self, bg_color=None)
        img = Image.open(get_resource_path("images/flatbuffers-downloader-logo-clean.png"))
        self.flatc_button = self.top_menu.add_cascade(image=CTk.CTkImage(img))
        self.flatc_button.configure(text=t("frontend.download_flatc"))
        self.flatc_button.configure(command=self.flatc_button_pressed)
        self.main_frame = CTk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.files_frame = CTk.CTkFrame(self.main_frame)
        self.files_frame.grid_rowconfigure(0, weight=1)
        self.files_frame.grid_columnconfigure(0, weight=1)
        self.files_frame.grid_columnconfigure(1, weight=1)
        self.files_frame.grid(row=0, sticky=CTk.NSEW)
        self.src_files_frame = ttk.LabelFrame(self.files_frame, text=t("frontend.source_files"))
        self.src_files_frame.grid_rowconfigure(0, weight=1)
        self.src_files_frame.grid_rowconfigure(1, weight=1)
        self.src_files_frame.grid_columnconfigure(0, weight=1)
        self.src_files_frame.grid(row=0, column=0, sticky=CTk.NSEW)
        self.src_binaries_frame = ttk.LabelFrame(self.src_files_frame,
                                                 text=t("frontend.source_binaries"))
        self.src_binaries_frame.grid(row=0, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.src_binaries_table = ttk.Treeview(self.src_binaries_frame,
                                               columns=("file", "file_size"), show="headings")
        self.src_binaries_table.heading("file", text=t("frontend.source_file_loc"))
        self.src_binaries_table.heading("file_size", text=t("frontend.file_size"))
        self.src_binaries_frame.grid_rowconfigure(0, weight=1)
        self.src_binaries_frame.grid_rowconfigure(1, weight=1)
        self.src_binaries_frame.grid_columnconfigure(0, weight=1)
        self.src_binaries_frame.grid_columnconfigure(1, weight=1)
        self.src_binaries_frame.grid_columnconfigure(2, weight=1)
        self.src_binaries_frame.grid_propagate(False)
        self.src_binaries_table.grid(row=0, column=0, columnspan=3, padx=10, pady=10,
                                     sticky=CTk.NSEW)
        self.attempt_apply_dnd(self.src_binaries_table.winfo_id(), self.on_binary_dropped)
        self.src_binaries_add_btn = CTk.CTkButton(self.src_binaries_frame,
                                                  text=t("frontend.button_add"))
        self.src_binaries_add_btn.configure(command=self.on_binary_add_click)
        self.src_binaries_add_btn.grid(row=1, column=0, padx=10, pady=10, sticky=CTk.EW)
        self.src_binaries_remove_selected_btn = CTk.CTkButton(self.src_binaries_frame, text=t(
            "frontend.button_remove_selected"))
        self.src_binaries_remove_selected_btn.grid(row=1, column=1, padx=10, pady=10, sticky=CTk.EW)
        self.src_binaries_remove_selected_btn.configure(
            command=self.on_binary_remove_selected_click)
        self.src_binaries_remove_all = CTk.CTkButton(self.src_binaries_frame,
                                                     text=t("frontend.button_remove_all"))
        self.src_binaries_remove_all.grid(row=1, column=2, padx=10, pady=10, sticky=CTk.EW)
        self.src_binaries_remove_all.configure(command=self.on_binary_remove_all_click)
        self.src_schemas_frame = ttk.LabelFrame(self.src_files_frame,
                                                text=t("frontend.source_schemas"))
        self.src_schemas_frame.grid(row=1, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.src_schemas_table = ttk.Treeview(self.src_schemas_frame, columns="file", show="")
        self.src_schemas_frame.grid_rowconfigure(0, weight=1)
        self.src_schemas_frame.grid_columnconfigure(0, weight=1)
        self.src_schemas_frame.grid_propagate(False)
        self.src_schemas_table.grid(row=0, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.attempt_apply_dnd(self.src_schemas_table.winfo_id(), self.on_schema_dropped)
        self.dest_files_frame = ttk.LabelFrame(self.files_frame,
                                               text=t("frontend.destination_files"))
        self.dest_files_frame.grid_rowconfigure(0, weight=1)
        self.dest_files_frame.grid_rowconfigure(1, weight=1)
        self.dest_files_frame.grid_columnconfigure(0, weight=1)
        self.dest_files_frame.grid(row=0, column=1, sticky=CTk.NSEW)
        self.dest_binaries_frame = ttk.LabelFrame(self.dest_files_frame,
                                                  text=t("frontend.destination_binaries"))
        self.dest_binaries_frame.grid(row=0, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.dest_binaries_table = ttk.Treeview(self.dest_binaries_frame,
                                                columns=("file", "result", "file_size"),
                                                show="headings", selectmode="browse")
        self.dest_binaries_table.heading("file", text=t("frontend.destination_file_loc"))
        self.dest_binaries_table.heading("result", text=t("frontend.result"))
        self.dest_binaries_table.heading("file_size", text=t("frontend.file_size"))
        self.dest_binaries_frame.grid_rowconfigure(0, weight=1)
        self.dest_binaries_frame.grid_rowconfigure(1, weight=1)
        self.dest_binaries_frame.grid_columnconfigure(0, weight=1)
        self.dest_binaries_frame.grid_columnconfigure(1, weight=1)
        self.dest_binaries_frame.grid_propagate(False)
        self.dest_binaries_table.grid(row=0, column=0, columnspan=2, padx=10, pady=10,
                                      sticky=CTk.NSEW)
        self.attempt_apply_dnd(self.dest_binaries_table.winfo_id(), self.on_binary_dropped)
        self.dest_binaries_change_dest_btn = CTk.CTkButton(self.dest_binaries_frame,
                                                           text=t("frontend.button_change_dest"))
        self.dest_binaries_change_dest_btn.grid(row=1, column=0, padx=10, pady=10, sticky=CTk.EW)
        self.dest_binaries_change_dest_btn.configure(command=self.on_change_dest_click)
        self.dest_binaries_rename_btn = CTk.CTkButton(self.dest_binaries_frame,
                                                      text=t("frontend.button_rename_file"))
        self.dest_binaries_rename_btn.grid(row=1, column=1, padx=10, pady=10, sticky=CTk.EW)
        self.dest_options_frame = ttk.LabelFrame(self.dest_files_frame,
                                                 text=t("frontend.destination_options"))
        self.dest_options_frame.grid_propagate(False)
        self.dest_options_frame.grid(row=1, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.bottom_menu = CTkMenuBar(self, bg_color=None)
        img = Image.open(get_resource_path("images/flatbuffers-batch-logo-clean.png"))
        self.deserialize_button = self.bottom_menu.add_cascade(image=CTk.CTkImage(img))
        self.deserialize_button.configure(text=t("frontend.deserialize"))
        self.deserialize_button.configure(command=self.deserialize_button_pressed)
        self.bottom_menu.pack(side=CTk.RIGHT)

    @staticmethod
    def attempt_apply_dnd(widget_id: int, dnd_event: Callable):
        """
        Adding files drag-and-drop functionality to widget if it's supported.
        :param widget_id: Widget ID.
        :param dnd_event: Callable object for drag-and-drop event.
        """
        if os.name != "nt":
            return
        try:
            mod = import_module("pywinstyles")
        except ModuleNotFoundError:
            return
        fun = getattr(mod, "apply_dnd", None)
        if fun is not None:
            fun(widget_id, dnd_event)

    @staticmethod
    def flatc_button_pressed():
        """
        Triggered to download flatc.
        """
        execute_download(os.getcwd())

    def on_binary_add_click(self):
        """
        Triggered when "Add..." button is clicked.
        """
        binary_paths = tkinter.filedialog.askopenfilenames(title=t("main.tkinter_binaries_select"))
        if binary_paths is not None:
            self.on_binary_dropped(binary_paths)

    def on_binary_remove_selected_click(self):
        """
        Triggered when "Remove selected" button is clicked.
        """
        selected_items = self.src_binaries_table.selection()
        for selected_item in selected_items:
            self.src_binaries_table.delete(selected_item)
            self.src_binaries_table.update()
            self.dest_binaries_table.delete(selected_item)
            self.dest_binaries_table.update()

    def on_binary_remove_all_click(self):
        """
        Triggered when "Remove all" button is clicked.
        :return:
        """
        for item in self.dest_binaries_table.get_children():
            self.src_binaries_table.delete(item)
            self.src_binaries_table.update()
            self.dest_binaries_table.delete(item)
            self.dest_binaries_table.update()

    def on_change_dest_click(self):
        """
        Triggered when "Change destination directory..." button is clicked.
        :return:
        """
        selected_items = self.dest_binaries_table.selection()
        for selected_item in selected_items:
            file_path = self.dest_binaries_table.set(selected_item, 0)
            file_dir, file_name = os.path.split(file_path)
            dest_dir = tkinter.filedialog.askdirectory(title=t("main.tkinter_output_select"),
                                                       initialdir=file_dir)
            if os.path.isdir(dest_dir):
                new_file_path = os.path.abspath(os.path.join(dest_dir, file_name))
                self.dest_binaries_table.set(selected_item, 0, new_file_path)
                if os.path.isfile(new_file_path):
                    self.dest_binaries_table.set(selected_item, 1,
                                                 t("frontend.file_already_exists"))
                    self.dest_binaries_table.set(selected_item, 2,
                                                 t("frontend.size_kb") % (
                                                             os.path.getsize(new_file_path) / 1024))
                else:
                    self.dest_binaries_table.set(selected_item, 1, "")
                self.dest_binaries_table.update()

    def on_binary_dropped(self, paths: list[str]):
        """
        Triggered when binary files or directories are added to table.
        :param paths: List of paths to added files or directories
        """
        for path in paths:
            if os.path.isdir(path):
                for subdir, _, files in os.walk(path):
                    for file in files:
                        self.add_src_binary(os.path.abspath(os.path.join(subdir, file)))
            elif os.path.isfile(path):
                self.add_src_binary(path)

    def add_src_binary(self, file: str):
        """
        Adds file to binary source table.
        :param file: Path to file.
        """
        binary_path = os.path.abspath(file)
        if os.path.splitext(binary_path)[1].lower() == ".json":
            return
        binary_exists = self.src_binaries_table.exists(binary_path.casefold())
        src_values = (binary_path, t("frontend.size_kb") % (os.path.getsize(binary_path) / 1024))
        output_path = os.path.splitext(binary_path)[0] + ".json"
        if os.path.isfile(output_path):
            dest_values = (output_path, t("frontend.file_already_exists"),
                           t("frontend.size_kb") % (os.path.getsize(output_path) / 1024))
        else:
            dest_values = (output_path, "", "")
        if binary_exists:
            for j in range(2):
                self.src_binaries_table.set(binary_path.casefold(), j, src_values[j])
            self.src_binaries_table.update()
            for j in range(3):
                self.dest_binaries_table.set(binary_path.casefold(), j, dest_values[j])
            self.dest_binaries_table.update()
        else:
            self.src_binaries_table.insert("", "end", binary_path.casefold(), values=src_values)
            self.src_binaries_table.update()
            self.dest_binaries_table.insert("", "end", binary_path.casefold(), values=dest_values)
            self.dest_binaries_table.update()

    def on_schema_dropped(self, paths: list[str]):
        """
        Triggered when schema files or directories are added to table.
        :param paths: List of paths to added files or directories
        """
        for path in paths:
            if os.path.isdir(path):
                for subdir, _, files in os.walk(path):
                    for file in files:
                        self.add_src_schema(os.path.abspath(os.path.join(subdir, file)))
            elif os.path.isfile(path):
                self.add_src_schema(path)

    def add_src_schema(self, file: str):
        """
        Adds file to schema source table.
        :param file: Path to file.
        """
        schema_path = os.path.abspath(file)
        if os.path.splitext(schema_path)[1].lower() != ".fbs":
            return
        if self.src_schemas_table.exists(schema_path.casefold()):
            return
        self.src_schemas_table.insert("", "end", schema_path.casefold(), values=[schema_path])
        self.src_schemas_table.update()

    def deserialize_button_pressed(self):
        """
        Triggered to deserialize source binary files.
        :return:
        """
        flatc_path = get_flatc_path(os.getcwd(), False, True)
        if flatc_path == "":
            CTkMessagebox(title=t("frontend.error"), message=t("frontend.flatc_not_found"),
                          icon="cancel")
            return
        binary_paths = [self.src_binaries_table.set(i, 0) for i in
                        self.src_binaries_table.get_children("")]
        output_paths = [os.path.dirname(self.dest_binaries_table.set(i, 0)) for i in
                        self.dest_binaries_table.get_children("")]
        schema_paths = [self.src_schemas_table.set(i, 0) for i in
                        self.src_schemas_table.get_children("")]
        binary_tuples = get_binary_tuples(binary_paths, schema_paths, True)
        for i, binary_tuple in enumerate(binary_tuples):
            self.deserialize_and_update_table(flatc_path, binary_tuple[1], binary_tuple[0],
                                              output_paths[i])

    def deserialize_and_update_table(self, flatc_path: str, schema_path: str, binary_path: str,
                                     output_path: str):
        """
        Deserializes flatbuffers binary and updates destination table.
        :param flatc_path: Schema compiler path.
        :param schema_path: Schema file path.
        :param binary_path: Binary file path.
        :param output_path: Output directory path.
        """
        json_path = deserialize(flatc_path, schema_path, binary_path, output_path, False)
        for i in self.dest_binaries_table.get_children(""):
            if not os.path.samefile(i, binary_path):
                continue
            if json_path != "":
                self.dest_binaries_table.set(i, 1, t("frontend.result_done"))
                self.dest_binaries_table.set(i, 2, t("frontend.size_kb") % (
                        os.path.getsize(json_path) / 1024))
            elif not os.path.isfile(binary_path):
                self.dest_binaries_table.set(i, 1, t("frontend.binary_not_found"))
                self.dest_binaries_table.set(i, 2, "")
            elif not os.path.isfile(schema_path):
                self.dest_binaries_table.set(i, 1, t("frontend.schema_not_found"))
                self.dest_binaries_table.set(i, 2, "")
            else:
                self.dest_binaries_table.set(i, 1, t("frontend.result_error"))
                self.dest_binaries_table.set(i, 2, "")
            self.dest_binaries_table.update()


if __name__ == "__main__":
    init_localization()
    CTk.set_appearance_mode("System")
    CTk.set_default_color_theme("blue")
    Deserializer().mainloop()
