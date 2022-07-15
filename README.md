# Twitch_App

The following repository is a collection of py applications which can be run from the CLI that help with the video processing and uploads required for maintaining my Twitch and YouTube channels. 

The scripts utilize a SQLALCHEMY backend to keep track of all the videos being uploaded and their associated view counts. Few iterations of this repository will aim to connect with other repositories related to individiaul game meta data which are yet to be created (for Example - my [Clash Royale Repo](https://github.com/TheRoundWon/Clash_Royale))

Included is a .env.sample file on how I structure a .env file that works with this application.

The .env file will be required to configure the connection necessary for the orm
The repository is called "Twitch_App" but covers projects that interact with both YouTube and Twitch.


## Requirements

The following script utilizes [FFMPEG](https://ffmpeg.org) and requires that it be installed <h2> First </h2> before installing the requirements of this repository. FFMPEG now handles video editting as it's far more performant than movie.py in terms of speed and quality.



## Structure of Repository
<i>I run  the following scripts daily using crontab -e</i>
- twitch-video-puller.py - Usually the first script run daily. Will download any un-downloaded clips and will update the viewcount on existing clips in sql database using sqlalchemy.
```
python3 twitch-video-puller.py 
```
 * Algo Notes - Scales in O(N) where N = # of clips. Typical run time to process 10 clips is around 30 seconds

- twitch-video-processor.py - handles the post-processing required for youtube uploads. The video processing script can incorporate a logo into your twitch clip as well as resize the clip to be YT shorts friendly. Now that we are using ffmpeg to handle our video processing ()

```
python3 twitch-video-puller.py <int: default 5> 
```

- yt_daily_upload.py - selects an unpublished clip with the highest twitch views (that has a video processed ready for upload) and uploads a full screen video and a short.
```
python3 yt_daily_upload.py <int: default 1>
```

<i>

- yt_videomaper.py - maps the videos and playlists which I've created in Youtube but have not mapped to my back end server.

```
python3 yt_videomaperj.py
```


## Reference scripts

- Google.py - script of boilerplate code to initiate a service and store your google authentication as a pickle file.
- StreamMaster.py - Script which holds the the Base object and SQLALCHEMY ORMs which will be used to create and update the underlying MYSQL table

