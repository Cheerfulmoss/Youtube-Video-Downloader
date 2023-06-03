from video_downloader import VideoDownloader
from video_downloader import PlaylistDownloader
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
import json


# TODO(Cheerful) Use tkinter filedialog (from tkinter import filedialog) and
#  askdirectory(**options), can use this to get save directory

class UserInterface:
    def __init__(self, master: tk.Tk) -> None:
        self._master = master
        self.download_folder = None
        self._startup_url = None
        self._settings = "preferences.json"
        self._setup_interface()
        self._apply_settings()

    def _setup_interface(self) -> None:
        self._master.geometry("280x140")
        self._master.minsize(width=280, height=140)
        self._master.resizable(width=False, height=False)
        self._master.title("Downloader")

        interact_frame = tk.Frame(self._master, padx=10, pady=10)
        interact_frame.pack(fill=tk.BOTH, anchor=tk.CENTER)

        selector_frame = tk.Frame(interact_frame)
        selector_frame.pack(side=tk.LEFT)

        selector_frame_2 = tk.Frame(interact_frame)
        selector_frame_2.pack(side=tk.LEFT)

        entry_boxes = tk.Frame(selector_frame_2)
        entry_boxes.pack(side=tk.TOP)

        download_button = tk.Button(selector_frame, text="Download",
                                    command=self._button_download)
        download_button.pack(side=tk.TOP, anchor=tk.W, pady=5)
        quit_button = tk.Button(selector_frame, text="Quit",
                                command=self._quit_root)
        quit_button.pack(side=tk.TOP, anchor=tk.W, pady=5)

        self._audio_state = tk.BooleanVar()
        self._ffmpeg_state = tk.BooleanVar()

        audio_only_tb = tk.Checkbutton(selector_frame, text="Audio Only",
                                       variable=self._audio_state)
        audio_only_tb.pack(side=tk.TOP, anchor=tk.W)
        ffmpeg_tb = tk.Checkbutton(selector_frame, text="FFMPEG",
                                   variable=self._ffmpeg_state)
        ffmpeg_tb.pack(side=tk.TOP, anchor=tk.W)

        url_frame = tk.Frame(entry_boxes)
        url_frame.pack(side=tk.TOP)
        dir_frame = tk.Frame(entry_boxes)
        dir_frame.pack(side=tk.TOP)

        tk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        tk.Label(dir_frame, text="DIR: ").pack(side=tk.LEFT)
        self._url_entry = tk.Entry(url_frame)
        self._url_entry.pack(side=tk.LEFT)
        self._directory_entry = tk.Entry(dir_frame)
        self._directory_entry.pack(side=tk.LEFT)

    def _apply_settings(self):
        with open(self._settings, "r") as settings_raw:
            settings = json.load(settings_raw)
            self.download_folder = settings.get("download_folder", "No Preset")
            self._audio_state.set(settings.get("audio_state", False))
            self._ffmpeg_state.set(settings.get("ffmpeg_state", False))
            self._directory_entry.insert(0, self.download_folder)

    def _save_settings(self) -> None:
        with open(self._settings, "w") as settings_raw:
            settings = {
                "download_folder": self._directory_entry.get(),
                "audio_state": self._audio_state.get(),
                "ffmpeg_state": self._ffmpeg_state.get(),
            }
            settings_json = json.dumps(settings, indent=4)
            settings_raw.write(settings_json)

    def _quit_root(self) -> None:
        self._save_settings()
        response = mb.askyesno(title="Confirmation",
                               message="Are you sure?")
        if response:
            self._master.destroy()

    def _button_download(self) -> None:
        self._master.title("DO NO CLOSE")
        self._master.configure(bg="red")

        video_url = self._url_entry.get()
        download_dir = self._directory_entry.get()
        audio_state = self._audio_state.get()
        self._url_entry.delete(0, "end")

        ffmpeg_state = self._ffmpeg_state.get()
        if "list=" in video_url:
            PlaylistDownloader(url=video_url, download_dir=download_dir,
                               audio_only=audio_state,
                               progressive=(not ffmpeg_state)
                               ).download_all()
        else:
            VideoDownloader(
                url=video_url,
                download_dir=download_dir,
                audio_only=audio_state,
                progressive=(not ffmpeg_state)).download_auto()
        self._master.title("Downloader")
        self._master.configure(bg="white")


if __name__ == "__main__":
    root = tk.Tk()
    app = UserInterface(master=root)
    root.mainloop()
