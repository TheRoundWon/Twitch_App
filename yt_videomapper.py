"""
The following script is designed to access the Youtube Data API and confirm which Youtube videos
have already been uploaded and whether all the videos are accounted for and correctly mapped to the right playlists

"""

## Developer notes - the playlist 


#Import necessary documents
import argparse
import http.client
import httplib2
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
# Connecting to a rasberry pi sql data base, mysql was in this instance

clips_folder = os.environ['CLIPS_FOLDER']
mobile_folder = os.environ['MOBILE_FOLDER']
fullscreen_folder = os.environ['FULLSCREEN_FOLDER']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']

CLIENT_SECRET_FILE = 'client_secrets.json'
API_NAME = 'youtube'
API_VERSION = 'v3'
# recommend pulling as much access as possible since the Create_Service function will create a pickle token of your authentication allow single authentication for extended period.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", 'https://www.googleapis.com/auth/youtube']

# Code that initiates connection to the Google API - pulled from Google.py. Difference from using Google's built-in service is the following script creates convenience of storing pickle with necessary authentication
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

def main(engine, service):
    # First pull all created playlists - videos should be mapped to playlists or a search will be required which is a more complicated operation
    playlists = service.playlists().list(part='id,snippet,status', channelId=os.environ['YT_CHANNEL_ID']).execute()

    shorts_pattern = f"[sS]hort" # check for YT short videos
    with Session(engine) as session: # initialize session to sql using context manager
        for playlist in playlists['items']: # loop through the differen playlists
            for key, thumbnail in playlist['snippet']['thumbnails'].items(): # first ensure that thumbnails are mapped in thumbnail table
                if not bool(session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()):
                    session.add(Thumbnails(asset=thumbnail['url'], width = thumbnail['width'], height=thumbnail['height']))
                    session.commit()
                # map the thumbnail table ids to the playlist dictionary
                playlist['snippet']['thumbnails'][key]['id'] = session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()[0]

            # if the playlist id is not in the table, add it
            if not bool(session.query(PlayList).where(PlayList.id == playlist['id']).first()):
                session.add(PlayList(id=playlist['id'], title=playlist['snippet']['title'], 
                tb_default = playlist['snippet']['thumbnails']['default']['id'], 
                tb_medium = playlist['snippet']['thumbnails']['medium']['id'],
                tb_high = playlist['snippet']['thumbnails']['high']['id'], 
                tb_standard = playlist['snippet']['thumbnails']['standard']['id']
                ))
                session.commit()

            # else, update the table with the current values if it's already in the table - this is to capture if thumbnails or titles have changed
            else:
                session.execute(
                    update(PlayList).where(PlayList.id == playlist['id']).values(dict(title=playlist['snippet']['title'], 
                tb_default = playlist['snippet']['thumbnails']['default']['id'], 
                tb_medium = playlist['snippet']['thumbnails']['medium']['id'],
                tb_high = playlist['snippet']['thumbnails']['high']['id'], 
                tb_standard = playlist['snippet']['thumbnails']['standard']['id']))
                )
                session.commit()
            # next find all the videos in each playlist
            for video in service.playlistItems().list(part="id,snippet", playlistId=playlist['id']).execute()['items']:
                title = video['snippet']['title']
                description = video['snippet']['description']
                match = re.search(shorts_pattern, title+description) # check whether the title or description have the word "short" in it
                # combine the tags into a  single string due to datatype limitations in database - leave as array if your database can store arrays
                tags = " | ".join(service.videos().list(part='snippet,contentDetails', id=video['snippet']['resourceId']['videoId']).execute()['items'][0]['snippet']['tags'])
                if match:
                    style = "m"
                else:
                    style = "f"

                # to capture titles with title conventon used in yt_videoupload.py
                title_components = title.split("|")
                if len(title_components) > 1:
                    titleName = title_components[-1].strip()
                
                else: # incase title does not follow current convention
                    titleName = title
                
                # find clip and original filename in clips database
                for clip_id, filename in session.query(Clip_Tracker.id, Clip_Tracker.video_name).where(Clip_Tracker.title == titleName).all():
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
                            playlist_id = playlist['id'],
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
                                        playlist_id = playlist['id'],
                                        tb_default = video['snippet']['thumbnails']['default']['id'], 
                                        tb_medium = video['snippet']['thumbnails']['medium']['id'],
                                        tb_high = video['snippet']['thumbnails']['high']['id'], 
                                        tb_standard = video['snippet']['thumbnails']['standard']['id'],
                                        tags = tags
                                    )
                                )
                                )
                            session.commit()

            # Next, check whether clips have been published by checking them vs the YT table
            for clip_id in session.query(Clip_Tracker.id).where(Clip_Tracker.published == None):
                # query where we count number of videos with each clip_id
                for title, style in session.query(YT_Video.title, YT_Video.style).where(YT_Video.clip_id == clip_id[0]).group_by(YT_Video.title).having(func.count(YT_Video.style) == 2).all():
                    if bool(title): # If there is a title for a query with 2 counts, then we update the video as f
                        session.query(Clip_Tracker).where(Clip_Tracker == clip_id[0]).update({'published': PublishingStatus.f})
                        session.commit()
                        print(title, style)
                # queries with 1 count, determine if mobile or short has been uploaded - design script to catch up videos with only one type of publishing complete.
                for title, style in session.query(YT_Video.title, YT_Video.style).where(YT_Video.clip_id == clip_id[0]).group_by(YT_Video.title).having(func.count(YT_Video.style) == 1).all():
                    if bool(title) and style.name == "f":
                        session.query(Clip_Tracker).where(Clip_Tracker == clip_id[0]).update({'published': PublishingStatus.d})
                        session.commit()
                    else:
                        session.query(Clip_Tracker).where(Clip_Tracker == clip_id[0]).update({'published': PublishingStatus.m})
                        session.commit()
                
if __name__ == "__main__":
    main(engine, service)

