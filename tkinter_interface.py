from tkinter import ttk, Tk, BooleanVar
from video_downloader_class import VideoDownloader
from json import load, dump
from threading import Thread
import ctypes

startup_directory = 0
startup_url = 0
settings = "preferences.json"
threads = 5


def check_preferences():
    download_folder = folder_directory.get()
    with open(settings, "r") as file:
        preferences = load(file)
        preferences["download_folder"] = download_folder
        file = open(settings, "w")
        dump(preferences, file)
        file.close()
    return download_folder


def fast_download():
    warning = ctypes.windll.user32.MessageBoxW(0, "Fast Download is at maximum 720p, unlike Download which can"
                                                  " go up to 4K. "
                                                  "Fast download does not use FFMPEG.\n"
                                                  "Are you sure you want to start the download?", "WARNING", 1)
    if warning == 2:
        return

    if thread_count_state.get():
        num_threads = threads
    else:
        num_threads = 5
    download_folder = check_preferences()
    video_url = video_url_box.get()
    video_url_box.delete(0, "end")
    root.title("DO NOT CLOSE")
    VideoDownloader(download_folder).\
        threaded_download(video_url=video_url, audio_set=audio_state.get(), num_threads=num_threads)
    video_url_box.delete(0, "end")
    root.title("Downloader")


def thread_start():
    warning = ctypes.windll.user32.MessageBoxW(0, "Are you sure you want to start the download", "WARNING", 1)
    if warning == 2:
        return
    t1 = Thread(target=button_download)
    t1.start()


def button_download():
    download_folder = check_preferences()
    video_url = video_url_box.get()
    video_url_box.delete(0, "end")
    root.title("DO NOT CLOSE")
    VideoDownloader(download_folder).download(video_url=video_url, audio_set=audio_state.get(),
                                              high_quality_set=ffmpeg_state.get())
    video_url_box.delete(0, "end")
    root.title("Downloader")


def increment_threads():
    global threads
    threads += 1
    thread_label.configure(text=f"Thread count: {threads}")


def decrement_threads():
    global threads
    if threads == 1:
        threads += 0
    else:
        threads -= 1
    thread_label.configure(text=f"Thread count: {threads}")


def close_program():
    root.destroy()


def temporary_text_directory(e):
    global startup_directory
    startup_directory += 1
    if startup_directory == 1:
        folder_directory.delete(0, "end")


def temporary_text_url(e):
    global startup_url
    startup_url += 1
    if startup_url == 1:
        video_url_box.delete(0, "end")


root = Tk()
root.geometry("290x150")
root.resizable(False, False)
root.title("Downloader")
frm = ttk.Frame(root, padding=10)
frm.pack(fill="both", expand=True)
download_button = ttk.Button(frm, text="Download", command=thread_start)
download_button.place(y=0, x=0)
fast_download_button = ttk.Button(frm, text="Fast Download", command=fast_download)
fast_download_button.place(y=30, x=0)

increase_thread_count = ttk.Button(frm, text="-", command=decrement_threads)
increase_thread_count.place(y=30, x=100)
thread_label = ttk.Label(frm, text=f"Thread count: {threads}")
thread_label.place(y=0, x=150)
decrease_thread_count = ttk.Button(frm, text="+", command=increment_threads)
decrease_thread_count.place(y=30, x=200)

with open(settings, "r") as file:
    preferences = load(file)
    directory = preferences["download_folder"]

folder_directory = ttk.Entry(root)
folder_directory.insert(0, directory)
folder_directory.place(y=90, x=135)
if directory == "Download Directory":
    folder_directory.bind("<FocusIn>", temporary_text_directory)

video_url_box = ttk.Entry(root)
video_url_box.insert(0, "Video URL")
video_url_box.place(y=70, x=135)
video_url_box.bind("<FocusIn>", temporary_text_url)

audio_state = BooleanVar()
audio_only_button = ttk.Checkbutton(frm, text="Audio only", variable=audio_state)
audio_only_button.place(y=90, x=0)
ffmpeg_state = BooleanVar()
ffmpeg_button = ttk.Checkbutton(frm, text="FFMPEG", variable=ffmpeg_state)
ffmpeg_button.place(y=110, x=0)
thread_count_state = BooleanVar()
change_thread_count = ttk.Checkbutton(frm, text="Change thread count", variable=thread_count_state)
change_thread_count.place(y=110, x=80)

quit_button = ttk.Button(frm, text="Quit", command=close_program)
quit_button.place(y=60, x=0)

root.mainloop()
