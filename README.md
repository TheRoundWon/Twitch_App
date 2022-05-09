# Twitch_App

The following repository is a collection of py applications which can be run from the CLI that help with the video processing and uploads required for maintaining my Twitch and YouTube channels. 



Included is a .env.sample file on how I structure a .env file that works with this application.

The .env file will be required to configure the connection necessary for the orm
The repository is called "Twitch_App" but covers projects that interact with both YouTube and Twitch.

<i>I run  the following scripts daily using crontab </i>

## Structure of Repository
- twitch-video-puller.py - Usually the first script run daily. Will download any un-downloaded clips and will update the viewcount on existing clips
```
python3 twitch-video-puller.py 
```
- twitch-video-processor.py - handles the post-processing required for youtube uploads. The video processing script can incorporate a logo into your twitch clip as well as resize the clip to be YT shorts friendly. Since we are using a pyscript - very slow and not optimal render quality. This process wil likely be migraited to a script which can ensure better video fidelity and processing time. 

```
python3 twitch-video-puller.py <int: default 5> 
```

- yt_daily_upload.py - selects an unpublished clip with the highest twitch views (that has a video processed ready for upload) and uploads a full screen video and a short.
```
python3 yt_daily_upload.py <int: default 1>
```


- Google.py - script of boilerplate code to initiate a service and store your google authentication as a pickle file.
