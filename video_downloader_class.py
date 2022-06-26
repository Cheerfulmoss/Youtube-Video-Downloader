from pytube import Playlist
from pytube import YouTube
import subprocess
import os
import threading

from pytube.exceptions import VideoUnavailable


class VideoDownloader():
    def __init__(self, music_folder):
        self.current_folder = os.getcwd()
        self.music_folder = music_folder

    def audio_only_download(self, video_url, download_path, for_merger=False):
        # 140 is 128kbps, 130 is 48kbps
        audio_bitrates_mp4 = [140, 139]

        audio = YouTube(video_url).streams
        for bitrate in audio_bitrates_mp4:
            if bitrate in audio.itag_index.keys():
                if for_merger:
                    audio.get_by_itag(bitrate). \
                        download(output_path=download_path, filename="audio_input.mp4")
                else:
                    audio.get_by_itag(bitrate).download(output_path=download_path)
                return f"Audio bitrate preset: {bitrate}"

    def video_only_download(self, video_url):
        # Ordered from highest quality (2160p) to lowest quality (144p).
        # When two values are used for a resolution it means they are using a different codex.
        # values: (401, 2160p), (400, 1440p), (299/399, 1080p), (298/398, 720p),
        # (135/397, 480p), (134/396, 360p), (133/395, 240p), (160/394, 144p).
        video_resolutions = [401, 400, 299, 399, 298, 398, 135, 397, 134, 396, 133, 395, 160, 394]

        video = YouTube(video_url).streams
        for resolution in video_resolutions:
            if resolution in video.itag_index.keys():
                video.get_by_itag(resolution).\
                    download(output_path=self.current_folder, filename="video_input.mp4")
                return f"Video resolution preset: {resolution}"

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
                video_name = str(YouTube(video_url).title)
                # Video names sometimes have characters that aren't allowed in filenames
                filename = ""
                disallowed_character_set = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
                for letter in video_name:
                    if letter not in disallowed_character_set:
                        filename = filename + letter
                bitrate = self.audio_only_download(video_url, download_path=self.current_folder, for_merger=True)
                resolution = self.video_only_download(video_url)
                print(f"{bitrate}\n{resolution}")
                cmd = f"ffmpeg -i video_input.mp4 -i audio_input.mp4 -c:v copy -c:a aac output.mp4"
                subprocess.call(cmd, shell=False)
                os.remove("video_input.mp4")
                os.remove("audio_input.mp4")
                os.replace(self.current_folder + "\\output.mp4", self.music_folder + f"\\output.mp4")
                os.rename(self.music_folder + f"\\output.mp4", self.music_folder + f"\\{filename}.mp4")
            else:
                # This is generally of lower quality or sometimes non-existent.
                # (22, 720p), (18, 360p).
                combined_audio_video = [22, 18]
                video = YouTube(video_url).streams
                for identifier in combined_audio_video:
                    if identifier in video.itag_index.keys():
                        video.get_by_itag(identifier). \
                            download(output_path=self.music_folder)
                        print(f"Combined audio and video tag: {identifier}")
                        return

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
            threads = []
            for index in range(num_threads):
                t = threading.Thread(target=self.list_input, args=(split_list[index], audio_set))
                t.start()
                threads.append(t)
        else:
            self.download(video_url=video_url, audio_set=audio_set, high_quality_set=False)
