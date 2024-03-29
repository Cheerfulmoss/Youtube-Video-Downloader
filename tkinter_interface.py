"""
Interface for the video downloader.
Alexander Burow - 2 September 2023

License: GPL3

Basic error checking.
"""

from video_downloader_class import VideoDownloader
from video_downloader_class import PlaylistDownloader
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
from tkinter import filedialog as fd
from threading import Thread
from pytube import exceptions
import json

DEBUG = True


class UserInterface:
    def __init__(self, master: tk.Tk) -> None:
        self._master = master
        self.download_folder = None
        self._startup_url = None
        self._thread_count = 5
        self._settings = "preferences.json"
        self._setup_interface()
        self._apply_settings()
        self.change_bg_colour()

    def _setup_interface(self) -> None:
        self._master.geometry("400x160")
        self._master.minsize(width=400, height=160)
        self._master.resizable(width=False, height=False)
        self._master.title("Downloader")

        self._interact_frame = tk.Frame(self._master, padx=10, pady=10)
        self._interact_frame.pack(fill=tk.BOTH, anchor=tk.CENTER)

        self._selector_frame = tk.Frame(self._interact_frame)
        self._selector_frame.pack(side=tk.LEFT)

        self._selector_frame_2 = tk.Frame(self._interact_frame)
        self._selector_frame_2.pack(side=tk.RIGHT)

        entry_boxes = tk.Frame(self._selector_frame_2)
        entry_boxes.pack(side=tk.TOP, fill=tk.X)

        thread_container = tk.Frame(self._selector_frame_2)
        thread_container.pack(side=tk.TOP, fill=tk.X)

        download_button = ttk.Button(self._selector_frame, text="Download",
                                     command=lambda:
                                     Thread(
                                         target=self._button_download).start())
        download_button.pack(side=tk.TOP, anchor=tk.W, pady=5)
        quit_button = ttk.Button(self._selector_frame, text="Quit",
                                 command=self._quit_root)
        quit_button.pack(side=tk.TOP, anchor=tk.W, pady=5)

        self._threaded_state = tk.BooleanVar()
        ttk.Checkbutton(self._selector_frame, text="Threaded",
                        variable=self._threaded_state).pack(
            side=tk.TOP, anchor=tk.W)

        self._audio_ffmpeg_var = tk.StringVar()
        audio_ffmpeg_options = ["Audio Only", "Video Only",
                                "Progressive", "Adaptive"]

        # Create a Combobox for selecting Audio/FFMPEG/None
        audio_ffmpeg_combobox = ttk.Combobox(
            self._selector_frame,
            textvariable=self._audio_ffmpeg_var,
            values=audio_ffmpeg_options
        )
        audio_ffmpeg_combobox.set("Adaptive")
        audio_ffmpeg_combobox.pack(side=tk.TOP, anchor=tk.W, pady=5)

        url_frame = tk.Frame(entry_boxes)
        url_frame.pack(side=tk.TOP, fill=tk.X)
        dir_frame = tk.Frame(entry_boxes)
        dir_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        tk.Label(dir_frame, text="DIR: ").pack(side=tk.LEFT)
        self._url_entry = ttk.Entry(url_frame)
        self._url_entry.pack(side=tk.LEFT, fill=tk.X, expand=tk.TRUE)
        self._directory_entry = ttk.Entry(dir_frame, state="readonly")
        self._directory_entry.bind("<Button-1>",
                                   lambda _: self._open_file_dialog())
        self._directory_entry.pack(side=tk.LEFT, fill=tk.X, expand=tk.TRUE)

        self._thread_count_label = tk.Label(thread_container,
                                            text="Threads: ")
        self._decrease = ttk.Button(
            thread_container,
            text="-",
            command=lambda: self._change_thread_count(False))
        self._increase = ttk.Button(
            thread_container,
            text="+",
            command=lambda: self._change_thread_count(True))

        self._decrease.pack(side=tk.LEFT)
        self._thread_count_label.pack(side=tk.LEFT)
        self._increase.pack(side=tk.LEFT)

    def _change_thread_count(self, increase: bool) -> None:
        if increase and self._thread_count < 50:
            self._thread_count += 1
        elif self._thread_count > 5:
            self._thread_count -= 1
        self._thread_count_label.config(
            text=f"Threads: {self._thread_count}"
        )

    def _open_file_dialog(self) -> None:
        self._directory_entry.config(state="normal")
        with open(self._settings, "r") as settings_raw:
            settings = json.load(settings_raw)
            download_folder = settings.get("download_folder", "No Preset")
        file_path = fd.askdirectory(mustexist=True, initialdir=download_folder)
        self._directory_entry.delete(0, "end")
        self._directory_entry.insert(0, file_path)
        self._save_settings()
        self._directory_entry.config(state="readonly")

    def change_bg_colour(self, colour: str = "blue") -> None:
        self._master.config(bg=colour)

    def _apply_settings(self) -> None:
        with open(self._settings, "r") as settings_raw:
            settings = json.load(settings_raw)
            self.download_folder = settings.get("download_folder", "No Preset")
            self._threaded_state.set(settings.get("threaded_state", False))
            self._thread_count = settings.get("thread_count", 5)
            if self._thread_count > 50:
                self._thread_count = 50
            elif self._thread_count < 5:
                self._thread_count = 5
            self._thread_count_label.config(
                text=f"Threads: {self._thread_count}"
            )
            self._directory_entry.config(state="normal")
            self._directory_entry.insert(0, self.download_folder)
            self._directory_entry.config(state="readonly")

    def _save_settings(self) -> None:
        self.change_bg_colour("green")
        with open(self._settings, "w") as settings_raw:

            if self._thread_count > 50:
                self._thread_count = 50
            elif self._thread_count < 5:
                self._thread_count = 5

            settings = {
                "download_folder": self._directory_entry.get(),
                "threaded_state": self._threaded_state.get(),
                "thread_count": self._thread_count,
            }
            settings_json = json.dumps(settings, indent=4)
            settings_raw.write(settings_json)
        self.change_bg_colour()

    def _quit_root(self) -> None:
        self._save_settings()
        response = mb.askyesno(title="Confirmation",
                               message="Are you sure?")
        if response:
            self._master.destroy()

    def _button_download(self) -> None:
        self._save_settings()
        self._master.title("DO NO CLOSE")
        self.change_bg_colour("red")

        video_url = self._url_entry.get()
        download_dir = self._directory_entry.get()
        self._url_entry.delete(0, "end")

        threaded_state = self._threaded_state.get()
        if "list=" in video_url:
            self._call_downloaders(video_url, download_dir,
                                   self._audio_ffmpeg_var, True,
                                   threaded_state, self._thread_count + 1)
        else:
            self._call_downloaders(video_url, download_dir,
                                   self._audio_ffmpeg_var, False,
                                   threaded_state,
                                   self._thread_count + 1)
        self._master.title("Downloader")
        self.change_bg_colour()

    @staticmethod
    def _call_downloaders(video_url: str, download_dir: str, download_type,
                          playlist: bool, threaded: bool, thread_count: int
                          ) -> None:
        option_map = {
            "Audio Only": "audio",
            "Video Only": "video",
            "Progressive": "progressive",
            "Adaptive": "adaptive",
        }

        try:
            if playlist:
                PlaylistDownloader(
                    url=video_url, download_dir=download_dir,
                    download_type=option_map[download_type.get()],
                    threads=thread_count, debug=DEBUG
                ).download_range()
            else:
                VideoDownloader(
                    url=video_url,
                    download_dir=download_dir,
                    download_type=option_map[download_type.get()], ide=0,
                    debug=DEBUG).download_auto()

        except exceptions.RegexMatchError:
            mb.showerror(title="Error: Invalid URL",
                         message="Given URL is invalid")
        except FileNotFoundError:
            mb.showerror(title="Error: Video File not Found",
                         message="For some reason the video file was not made"
                                 " and no error was thrown, somehow")
        except NotADirectoryError:
            mb.showerror(title="Error: Directory not found",
                         message="The directory given was not found. Can mean "
                                 "that the directory does not already exist")


if __name__ == "__main__":
    root = tk.Tk()
    app = UserInterface(master=root)
    root.mainloop()
