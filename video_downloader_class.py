from pytube import Playlist
from pytube import YouTube
from subprocess import call
from os import getcwd, remove, rename, replace, path
import os
from threading import Thread
from pytube.exceptions import VideoUnavailable


class VideoDownloader:
    def __init__(self, music_folder):
        self.current_folder = getcwd()
        self.music_folder = music_folder

    def audio_only_download(self, video_object, download_path, for_merger=False):
        audio = video_object.streams.filter(file_extension="mp4", type="audio", only_audio=True).order_by("abr")[-1]
        if for_merger:
            audio.download(output_path=download_path, filename="audio_input.mp4")
        else:
            audio.download(output_path=download_path)
        return audio

    def video_only_download(self, video_object):
        video = video_object.streams.filter(file_extension="mp4", type="video", only_video=True).order_by("resolution")[-1]
        video.download(output_path=self.current_folder, filename="video_input.mp4")
        return video

    def download_video(self, video_object, audio_only, high_quality):
        if audio_only:
            self.audio_only_download(video_object, download_path=self.music_folder)
            print(f"{video_object.title} downloaded: audio only")
        else:
            if high_quality:
                video_name = str(video_object.title)
                video_author = str(video_object.author)
                video_year = str(video_object.publish_date)
                # Video names sometimes have characters that aren't allowed in filenames
                filename = ""
                disallowed_character_set = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
                for letter in video_name:
                    if letter not in disallowed_character_set:
                        filename = filename + letter
                threads = list()
                threads.append(Thread(target=self.audio_only_download, args=(video_object, self.current_folder, True)))
                threads.append(Thread(target=self.video_only_download, args=(video_object,)))
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                if path.exists("output.mp4"):
                    remove("output.mp4")
                cmd = f'ffmpeg -i video_input.mp4 -i audio_input.mp4 -c:v copy -c:a aac -metadata author="{video_author}" -metadata year="{video_year}" -metadata title="{filename}" output.mp4'
                call(cmd, shell=False, creationflags=0x00000008)
                remove("video_input.mp4")
                remove("audio_input.mp4")
                n = 0
                while os.path.exists(f"{self.music_folder}\\output-{n}.mp4"):
                    n += 1
                replace(self.current_folder + "\\output.mp4", self.music_folder + f"\\output-{n}.mp4")
                n = 0
                if os.path.exists(self.music_folder + f"\\{filename}.mp4"):
                    while os.path.exists(self.music_folder + f"\\{filename}_({n}).mp4"):
                        n += 1
                    rename(self.music_folder + f"\\output-{n}.mp4", self.music_folder + f"\\{filename}_({n}).mp4")
                else:
                    rename(self.music_folder + f"\\output-{n}.mp4", self.music_folder + f"\\{filename}.mp4")
                print(f"{filename} downloaded: ffmpeg")
            else:
                video_object.streams.filter(file_extension="mp4", progressive=True).order_by("resolution")[-1].download(output_path=self.music_folder)
                print(f"{video_object.title} downloaded: progressive")

    def download_playlist(self, url, audio_only, high_quality):
        for video_url in Playlist(url):
            try:
                video_object = YouTube(video_url)
            except VideoUnavailable:
                print(f"Playlist {video_url} unavailable")
                continue
            self.download_video(video_object, audio_only=audio_only, high_quality=high_quality)

    def auto_download(self, video_url, audio_set, high_quality_set):
        if "list=" in video_url:
            self.download_playlist(video_url, audio_only=audio_set, high_quality=high_quality_set)
            print(f"Finished downloading playlist: {Playlist(video_url).title}")
        else:
            try:
                video_object = YouTube(video_url)
            except VideoUnavailable:
                print(f"Video {video_url} unavailable")
                return
            self.download_video(video_object, audio_only=audio_set, high_quality=high_quality_set)

    def list_input(self, video_list, audio_only):
        for video_url in video_list:
            try:
                video_object = YouTube(video_url)
            except VideoUnavailable:
                print(f"Video {video_url} unavailable")
                continue
            self.download_video(video_object, audio_only=audio_only, high_quality=False)

    def threaded_download(self, video_url, audio_set, num_threads=5):
        if "list=" in video_url:
            playlist_object = Playlist(video_url)
            playlist_list = list(playlist_object)
            split_list = [playlist_list[i::num_threads] for i in range(num_threads)]
            threads = list()
            for index in range(num_threads):
                t = Thread(target=self.list_input, args=(split_list[index], audio_set))
                threads.append(t)
            for thread in threads:
                thread.start()
        else:
            self.auto_download(video_url=video_url, audio_set=audio_set, high_quality_set=False)
