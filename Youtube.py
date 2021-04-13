from tkinter import *
from pytube import *
import socket
import os

# -- Initialise the window entity
window = Tk()

# --- Change the icon
window.iconbitmap("YoutubeDownloader.ico")

# --- Window size
window.geometry("500x300")
window.resizable(0, 0)

# --- Window title
window.title("Youtube Downloader")

# --- Label, positioned at the top of the window. Since this label is initialised and packed first it is at the top
Label(window, text="Youtube Video Downloader", font="arial 20 bold").pack()

# --- Initialise variables. Link is used to make a entry field that can be typed in and an output can be retrieved
link = StringVar()
video_playlist = 0

# --- More Labels, and the entry field is initialised and placed
link_descriptor = Label(window, text="Paste Video Link Here", font="arial 15 bold")
link_descriptor.place(x=160, y=60)
link_enter = Entry(window, width=70, textvariable=link)
link_enter.place(x=32, y=90)
downloaded = Label(window, text=f"", font="arial 15")
quality = Label(window, text=f"", font="arial 15")
# --- qTag, Quality Tag is used later to tell the program whether the download is high or low quality
qTag = 0


# --- Gets the author of the video
def get_youtuber(video_url):
    url = video_url
    youtuber = url.author

    return youtuber


# --- Checks to see if the user has an internet connection
def check_connection():
    try:
        socket.create_connection(("google.com", 80))
        return True
    except OSError:
        return False


# --- annihilate is used to get rid of most if not all Labels and buttons
def annihilate():
    try:
        link_descriptor.destroy()
    except:
        pass
    try:
        link_enter.destroy()
    except:
        pass
    try:
        download.destroy()
    except:
        pass
    try:
        downloaded.destroy()
    except:
        pass
    try:
        quality.destroy()
    except:
        pass
    try:
        switch.destroy()
    except:
        pass


# --- Calls the annihilate function and is a contingency when the user does not have a connection
def offline():
    annihilate()
    # --- fg is text colour
    ERROR = Label(window, text=f"No internet connection,\n"
                               f" restart the program", font=f"arial 20", fg="red")
    ERROR.pack(side="top")

    return


# --- The function that downloads the single video link
def downloadFunc(video_url):
    url = video_url
    # --- Grabs the Quality Tag
    global qTag

    try:

        # --- Checks to see if there is an internet connection
        connection = check_connection()
        if not connection:
            # --- If there is no connection, offline is called. Informing the user that they do not have an internet
            # --- connection
            offline()

        else:

            # --- Gets the youtuber
            youtuber = get_youtuber(url)

            # --- Gets the path/directory
            direc = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Videos', youtuber)

            # --- Checks to see if the directory already exists
            exists = os.path.exists(direc)

            # --- Checks to see if exists = False
            if not exists:
                # --- Makes the directory
                os.mkdir(path=direc)

                # --- calls the HD download option, and assigns it to the title variable
                title = ResPopDown(direc, url)

            # --- If the directory already exists
            else:
                # --- calls the HD download option, and assigns it to the title variable
                title = ResPopDown(direc, url)

            return title, qTag

    # --- If the HD download didn't work
    except:

        # --- Checks to see if there is an internet connection
        connection = check_connection()
        if not connection:
            # --- If there is no connection, offline is called. Informing the user that they do not have an internet
            # --- connection
            offline()

        else:

            # --- Gets the youtuber
            youtuber = get_youtuber(url)

            # --- Grabs the title
            title = url.title

            # --- Gets the path/directory
            direc = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Videos', youtuber)

            # --- Checks to see if the directory already exists
            exists = os.path.exists(direc)

            # --- Checks to see if exists = False
            if not exists:
                # --- Makes the directory
                os.mkdir(path=direc)

                # --- downloads the first quality option to the path
                url.streams.first().download(output_path=direc)

                # --- Sets the quality tag to the 0, meaning the lowest quality
                qTag = 0
            else:
                # --- downloads the first quality option to the path
                url.streams.first().download(output_path=direc)

                # --- Sets the quality tag to the 0, meaning the lowest quality
                qTag = 0

            return title, qTag


# --- ResPopDown: resolution pop download. Grabs all the resolutions, pops the highest,
# --- and downloads the highest to the path
def ResPopDown(direc, url):
    # --- Grabs the Quality Tag
    global qTag

    # --- Grabs all the progressive (one file) qualities and appends them to a list
    resL = [url.resolution for url in url.streams.filter(progressive=True)]

    # --- Isolates the last option
    resL = resL[1:]

    # --- Pops the option from the list
    res = resL.pop(0)

    # --- Gets the title of the video
    title = url.title

    # --- Downloads the video, using the res variable
    url.streams.filter(resolution=res).first().download(output_path=direc)

    # --- Sets qTag to 1, meaning highest quality
    qTag = 1
    return title


# --- Individual video downloader
def videodownloader():
    global downloaded
    global quality
    global qTag
    global link_descriptor
    global link_enter
    global download

    # --- Initialise the Youtube API
    url = YouTube(str(link.get()))

    # --- Checks to see if downloaded label exists
    if downloaded.winfo_exists() == 1:
        # --- If yes, it deletes it
        downloaded.destroy()
    else:
        # --- Else, and it does nothing
        pass

    # --- Checks to see if quality label exists
    if quality.winfo_exists() == 1:
        # --- If yes, it deletes it
        quality.destroy()
    else:
        # --- Else, and it does nothing
        pass

    try:

        # --- Calls the download function and grabs the title
        title = downloadFunc(url)

        # --- Informs the user that the video was downloaded
        downloaded = Label(window, text=f"{title[0]}: DOWNLOADED", font="arial 15")
        downloaded.pack(side="bottom")

        # --- Checks if qTag is 0, meaning lower quality
        if title[1] == 0:
            quality = Label(window, text=f"Highest Quality was Unable to Download", font="arial 15")
            quality.pack(side="top")

        # --- Checks if qTag is 1, meaning higher quality
        elif title[1] == 1:
            quality = Label(window, text=f"Highest Quality was Downloaded", font="arial 15")
            quality.pack(side="top")

        # --- empties the entry field
        link_enter.delete(0, "end")
        return title

    except:

        # --- Checks to see if the user has an internet connection
        connection = check_connection()

        # --- If connection returns false, it does nothing
        if not connection:
            pass

        # --- If connection returns true
        if connection:
            # --- Calls annihilate to delete nearly everything
            annihilate()

            # --- Displays Label below
            ERROR = Label(window, text=f"Unknown error has occurred\n"
                                       f" restart the program", font=f"arial 20", fg="red")
            ERROR.pack(side="top")

            return


# --- Playlist downloader
def playlistdownloader():
    global downloaded
    global quality

    # --- Initialise the Youtube API
    url = Playlist(str(link.get()))

    # --- Checks to see if downloaded label exists
    if downloaded.winfo_exists() == 1:
        # --- If yes, it deletes it
        downloaded.destroy()
    else:
        # --- Else, and it does nothing
        pass

    # --- Checks to see if quality label exists
    if quality.winfo_exists() == 1:
        # --- If yes, it deletes it
        quality.destroy()
    else:
        # --- Else, and it does nothing
        pass

    try:

        title = url.title
        # --- For each video in the playlist
        for video in url.videos:
            path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Videos', title)
            # --- Download highest quality
            ResPopDown(path, video)

        # --- Inform user that the playlist was downloader
        downloaded = Label(window, text=f"{title}: DOWNLOADED", font="arial 15")
        downloaded.pack(side="bottom")
        link_enter.delete(0, "end")

    except:
        title = url.title
        # --- For each video in playlist
        for video in url.videos:
            path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Videos', title)
            # --- Download first listed quality
            video.streams.first().download(output_path=path)

        # --- Inform user that the playlist was downloader
        downloaded = Label(window, text=f"{title}: DOWNLOADED", font="arial 15")
        downloaded.pack(side="bottom")
        link_enter.delete(0, "end")


def swap(switch_text, switch_command, link_text, download_command):
    global switch, link_descriptor, download
    # --- Checks to see if downloaded label exists
    if downloaded.winfo_exists() == 1:
        # --- If yes, it deletes it
        downloaded.destroy()
    else:
        # --- Else it does nothing
        pass
    # --- Checks to see if quality label exists
    if quality.winfo_exists() == 1:
        # --- If yes, it deletes it
        quality.destroy()
    else:
        # --- Else it does nothing
        pass
    # --- Checks to see if the change button exists
    if switch.winfo_exists() == 1:
        # --- If it does it deletes it
        switch.destroy()

        # --- Re-creates the object with desired settings
        switch = Button(window, text=f"{switch_text} DOWNLOADER", font="arial 15 bold", bg="red", padx=2
                        , command=switch_command)
        switch.pack(side="bottom")
    else:
        pass
    # --- Checks to see if the link_descriptor label exists
    if link_descriptor.winfo_exists() == 1:
        # --- If it does it deletes it
        link_descriptor.destroy()

        # --- Re-creates the object with desired settings
        link_descriptor = Label(window, text=f"Paste {link_text} Link Here", font="arial 15 bold")
        link_descriptor.place(x=160, y=60)
    else:
        pass
    # --- Checks to see if the download button exists
    if download.winfo_exists() == 1:
        # --- If it does it deletes it
        download.destroy()

        # --- Re-creates the object with desired settings
        download = Button(window, text="DOWNLOAD", font="arial 15 bold", bg="red", padx=2,
                          command=download_command)
        download.place(x=180, y=150)


# --- Switch between vid and playlist downloader
def vid_to_playlist():
    # --- Grab necessary globals
    global video_playlist
    global switch
    global link_descriptor
    global download

    # --- If video playlist = 1, it means it's in playlist downloader
    if video_playlist == 0:

        # -- Change to video downloader
        video_playlist = 1

        # --- Calls the swap function
        swap("VIDEO", vid_to_playlist, "Playlist", playlistdownloader)


    # --- If video playlist = 0, it means it's in playlist downloader
    elif video_playlist == 1:

        # -- Change to playlist downloader
        video_playlist = 0

        # --- Calls the swap function
        swap("PLAYLIST", vid_to_playlist, "Video", videodownloader)


download = Button(window, text="DOWNLOAD", font="arial 15 bold", bg="red", padx=2, command=videodownloader)
download.place(x=180, y=150)

switch = Button(window, text="PLAYLIST DOWNLOADER", font="arial 15 bold", bg="red", padx=2
                , command=vid_to_playlist)
switch.pack(side="bottom")

window.mainloop()
