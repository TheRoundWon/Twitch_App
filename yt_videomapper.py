"""
The following script is designed to access the Youtube Data API and confirm which Youtube videos
have already been uploaded and whether all the videos are accounted for and correctly mapped to the right playlists. The script also accounts for accidental deletions and removes deleted
youtube files from the sql database as well as updating the TwitchVideos table (or tries)

"""

## Developer notes - the playlist 


#Import necessary documents
import argparse
import http.client
# import httplib2
import os
import random
import time
import datetime
from datetime import datetime, timedelta
from Google import *
import os
from dotenv import load_dotenv
from sqlalchemy import *
import datetime
import re
from StreamMaster import *
from _utils import *
# Connecting to a rasberry pi sql data base, mysql was in this instance

clips_folder = os.environ['CLIPS_FOLDER']
mobile_folder = os.environ['MOBILE_FOLDER']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']

CLIENT_SECRET_FILE = 'client_secrets.json'
API_NAME = 'youtube'
API_VERSION = 'v3'
# recommend pulling as much access as possible since the Create_Service function will create a pickle token of your authentication allow single authentication for extended period.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", 'https://www.googleapis.com/auth/youtube']

# Code that initiates connection to the Google API - pulled from Google.py. Difference from using Google's built-in service is the following script creates convenience of storing pickle with necessary authentication
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

def completeThumbnails(playlist, default_mode = 'default'):
    default = playlist['snippet']['thumbnails'][default_mode]
    checks = ['default', 'medium', 'high', 'standard']
    for chck in checks:
        if not bool(playlist['snippet']['thumbnails'].get(chck)):
            playlist['snippet']['thumbnails'][chck] = default
    return playlist



def yt_playlist_map(session_engine, service):
    # First pull all created playlists - videos should be mapped to playlists or a search will be required which is a more complicated operation
    playlists = service.playlists().list(part='id,snippet,status', channelId=os.environ['YT_CHANNEL_ID']).execute()
    nextPage = playlists['nextPageToken']
    while nextPage != None:
        seedPlaylist = service.playlists().list(part='id,snippet,status', channelId=os.environ['YT_CHANNEL_ID'], pageToken = nextPage).execute()
        playlists['items'] = playlists['items'] + seedPlaylist['items']
        if bool(seedPlaylist.get('nextPageToken')):
            nextPage = seedPlaylist['nextPageToken']
        else:
            nextPage = None
    status_mapper = {PublishingStatus.d: VideoStyle.f, PublishingStatus.m: VideoStyle.m}
    invers_mapper = {value: key for key, value in status_mapper.items()}
      
    shorts_pattern = f"[sS]hort" # check for YT short videos
    with Session(session_engine) as session: # initialize session to sql using context manager
        for playlist in playlists['items']: # loop through the differen playlists
            playlist = completeThumbnails(playlist)
            for key, thumbnail in playlist['snippet']['thumbnails'].items(): # first ensure that thumbnails are mapped in thumbnail table
                if not bool(session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()):
                    session.add(Thumbnails(asset=thumbnail['url'], width = thumbnail['width'], height=thumbnail['height']))
                    session.commit()
                # map the thumbnail table ids to the playlist dictionary
                playlist['snippet']['thumbnails'][key]['id'] = session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()[0]

            # if the playlist id is not in the table, add it
            if not bool(session.query(PlayList_yt).where(PlayList_yt.id == playlist['id']).first()):
                session.add(PlayList_yt(id=playlist['id'], title=playlist['snippet']['title'], 
                tb_default = playlist['snippet']['thumbnails']['default']['id'], 
                tb_medium = playlist['snippet']['thumbnails']['medium']['id'],
                tb_high = playlist['snippet']['thumbnails']['high']['id'], 
                tb_standard = playlist['snippet']['thumbnails']['standard']['id']
                ))
                session.commit()

            # else, update the table with the current values if it's already in the table - this is to capture if thumbnails or titles have changed
            else:
                session.execute(
                    update(PlayList_yt).where(PlayList_yt.id == playlist['id']).values(dict(title=playlist['snippet']['title'], 
                tb_default = playlist['snippet']['thumbnails']['default']['id'], 
                tb_medium = playlist['snippet']['thumbnails']['medium']['id'],
                tb_high = playlist['snippet']['thumbnails']['high']['id'], 
                tb_standard = playlist['snippet']['thumbnails']['standard']['id']))
                )
                session.commit()
            if "Shorts" in playlist['snippet']['title']:
                style = VideoStyle.m
            else:
                style = VideoStyle.f
            # next find all the videos in each playlist
            playlist_Items = service.playlistItems().list(part="id,snippet", playlistId=playlist['id']).execute()
            if bool(playlist_Items.get('nextPageToken')):
                nextPage = playlist_Items['nextPageToken']
            else:
                nextPage = None
            # Make sure you get all the pages...
            while nextPage != None:
                seed_list = service.playlistItems().list(part="id,snippet", playlistId=playlist['id'], pageToken = nextPage).execute()
                if bool(seed_list.get('nextPageToken')):
                    nextPage = seed_list['nextPageToken']
                else:
                    nextPage = None
                playlist_Items['items'] = playlist_Items['items'] + seed_list['items']

            # Remove any videos that are in playlist mapper and YT_Video that are no longer in youtube
            video = session.query(yt_vid_pl_mapper).where(yt_vid_pl_mapper.c.yt_playlist_id == playlist['id']).filter(~yt_vid_pl_mapper.c.yt_video_id.in_([video['snippet']['resourceId']['videoId'] for video in playlist_Items['items']])).all()
         
            for video in playlist_Items['items']:
                try:
                    video = completeThumbnails(video)
                    title = video['snippet']['title']
                    description = video['snippet']['description']
                     # check whether the title or description have the word "short" in it
                    # combine the tags into a  single string due to datatype limitations in database - leave as array if your database can store arrays
                    tags = " | ".join(service.videos().list(part='snippet,contentDetails', id=video['snippet']['resourceId']['videoId']).execute()['items'][0]['snippet']['tags'])
                   

                    # to capture titles with title conventon used in yt_videoupload.py
                    title_components = title.split("|")
                    if len(title_components) > 1:
                        titleName = title_components[-1].strip()
                    
                    else: # incase title does not follow current convention
                        titleName = title
                    
                 
                
                    # find clip and original filename in clips database
                    for clip_id, filename in session.query(TwitchVideos.id, TwitchVideos.video_name).where(TwitchVideos.title == titleName).all():

                        if not bool(clip_id):
                            print(title)
                        else:
                            # loop through the thumbnail images to ensure they are in the thumbnail database
                            for key, thumbnail in video['snippet']['thumbnails'].items():
                                if not bool(session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()):
                                    session.add(Thumbnails(asset=thumbnail['url'], width = thumbnail['width'], height=thumbnail['height']))
                                    session.commit()
                                video['snippet']['thumbnails'][key]['id'] = session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()[0]
                            # VideoID is not in the YT_Video table - add it!    
                            if not bool(session.query(YT_Video).where(YT_Video.id == video['snippet']['resourceId']['videoId']).first()):
                                session.add( YT_Video(id = video['snippet']['resourceId']['videoId'], 
                                clip_id=clip_id, 
                                title = title,
                                filename = filename,
                                style = style,
                                description = description,
                                tb_default = video['snippet']['thumbnails']['default']['id'], 
                                tb_medium = video['snippet']['thumbnails']['medium']['id'],
                                tb_high = video['snippet']['thumbnails']['high']['id'], 
                                tb_standard = video['snippet']['thumbnails']['standard']['id'],
                                tags = tags
                                
                                )
                                )
                                session.commit()
                            # If it's already in there, update our record of current descriptiption / thumbnails.
                            else:
                                session.execute(
                                    update(YT_Video).where(YT_Video.id == video['snippet']['resourceId']['videoId']).values(
                                        dict(
                                            clip_id=clip_id, 
                                            title = title,
                                            filename = filename,
                                            style = style,
                                            description = description,
                                            tb_default = video['snippet']['thumbnails']['default']['id'], 
                                            tb_medium = video['snippet']['thumbnails']['medium']['id'],
                                            tb_high = video['snippet']['thumbnails']['high']['id'], 
                                            tb_standard = video['snippet']['thumbnails']['standard']['id'],
                                            tags = tags
                                        )
                                    )
                                    )
                                session.commit()
                            if not bool(session.query(yt_vid_pl_mapper).where(yt_vid_pl_mapper.c.yt_video_id == video['snippet']['resourceId']['videoId']).where(yt_vid_pl_mapper.c.yt_playlist_id ==playlist['id']).first()):
                                session.execute(insert(yt_vid_pl_mapper).values({"yt_playlist_id": playlist['id'], 'yt_video_id': video['snippet']['resourceId']['videoId']}))
                except Exception as e:
                    if video.get('snippet')['title'] != 'Deleted video':
                        print(video, e)
            # End loop


        # Next, check whether clips have been published by checking them vs the YT table

        # for clip_id in session.query(TwitchVideos.id).all():
        #     # query where we count number of videos with each clip_id
        #     for title, style in session.query(YT_Video.title, YT_Video.style).where(YT_Video.clip_id == clip_id[0]).group_by(YT_Video.title).having(func.count(YT_Video.style) == 2).all():
        #         if bool(title): # If there is a title for a query with 2 counts, then we update the video as f
        #             session.query(TwitchVideos).where(TwitchVideos.id == clip_id[0]).update({'published': PublishingStatus.f})
        #             session.commit()
        #     # queries with 1 count, determine if mobile or short has been uploaded - design script to catch up videos with only one type of publishing complete.
        #     for title, style in session.query(YT_Video.title, YT_Video.style).where(YT_Video.clip_id == clip_id[0]).group_by(YT_Video.title).having(func.count(YT_Video.style) == 1).all():
        #         if bool(title) and style.name == "f":
        #             session.query(TwitchVideos).where(TwitchVideos.id == clip_id[0]).update({'published': PublishingStatus.d})
        #             session.commit()
        #         else:
        #             session.query(TwitchVideos).where(TwitchVideos.id == clip_id[0]).update({'published': PublishingStatus.m})
        #             session.commit()

                
if __name__ == "__main__":
    yt_playlist_map(mysql_engine, service)
    print('All Done!')


