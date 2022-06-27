from pytube import Playlist
from pytube import YouTube
from subprocess import call
from os import getcwd, remove, rename, replace, path
from threading import Thread
from pytube.exceptions import VideoUnavailable


class VideoDownloader():
    def __init__(self, music_folder):
        self.current_folder = getcwd()
        self.music_folder = music_folder

    def audio_only_download(self, video_url, download_path, for_merger=False):
        audio = YouTube(video_url).streams.filter(file_extension="mp4", type="audio", only_audio=True).order_by("abr")[-1]
        if for_merger:
            audio.download(output_path=download_path, filename="audio_input.mp4")
        else:
            audio.download(output_path=download_path)
        return audio

    def video_only_download(self, video_url):
        video = YouTube(video_url).streams.filter(file_extension="mp4", type="video", only_video=True).order_by("resolution")[-1]
        video.download(output_path=self.current_folder, filename="video_input.mp4")
        return video

    def download_video(self, video_url, audio_only, high_quality):
        try:
            YouTube(video_url)
        except VideoUnavailable:
            print(f"Video {video_url} is unavailable, skipping")
            return
        if audio_only:
            self.audio_only_download(video_url, download_path=self.music_folder)
        else:
            if high_quality:
                video_object = YouTube(video_url)
                video_name = str(video_object.title)
                video_author = str(video_object.author)
                video_year = str(video_object.publish_date)
                # Video names sometimes have characters that aren't allowed in filenames
                filename = ""
                disallowed_character_set = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
                for letter in video_name:
                    if letter not in disallowed_character_set:
                        filename = filename + letter
                bitrate = self.audio_only_download(video_url, download_path=self.current_folder, for_merger=True)
                resolution = self.video_only_download(video_url)
                print(f"{bitrate}\n{resolution}")
                if path.exists("output.mp4"):
                    remove("output.mp4")
                cmd = f'ffmpeg -i video_input.mp4 -i audio_input.mp4 -c:v copy -c:a aac -metadata author="{video_author}" -metadata year="{video_year}" output.mp4'
                call(cmd, shell=False, creationflags=0x00000008)
                remove("video_input.mp4")
                remove("audio_input.mp4")
                replace(self.current_folder + "\\output.mp4", self.music_folder + f"\\output.mp4")
                rename(self.music_folder + f"\\output.mp4", self.music_folder + f"\\{filename}.mp4")
            else:
                YouTube(video_url).streams.filter(file_extension="mp4", progressive=True).order_by("resolution")[-1].download(output_path=self.music_folder)

    def download_playlist(self, video_url, audio_only, high_quality):
        for video_url in Playlist(video_url):
            self.download_video(video_url, audio_only=audio_only, high_quality=high_quality)

    def download(self, video_url, audio_set, high_quality_set):
        if "list=" in video_url:
            self.download_playlist(video_url, audio_only=audio_set, high_quality=high_quality_set)
        else:
            self.download_video(video_url, audio_only=audio_set, high_quality=high_quality_set)

    def list_input(self, video_list, audio_only):
        for video_url in video_list:
            self.download_video(video_url, audio_only=audio_only, high_quality=False)

    def threaded_download(self, video_url, audio_set, num_threads=5):
        if "list=" in video_url:
            playlist_object = Playlist(video_url)
            playlist_list = list(playlist_object)
            split_list = [playlist_list[i::num_threads] for i in range(num_threads)]
            threads = list()
            for index in range(num_threads):
                t = Thread(target=self.list_input, args=(split_list[index], audio_set))
                t.start()
                threads.append(t)
        else:
            self.download(video_url=video_url, audio_set=audio_set, high_quality_set=False)
