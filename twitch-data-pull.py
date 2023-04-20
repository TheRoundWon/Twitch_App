""" Check Associated iPython Notebook for better documentation - the following
script is designed to be run on a schedule (ideally daily) where the script checks for the newest clips created for a channel and downloads them to the appropriate locations
specified in the .env file
"""
#Import necessary packages
import os
import sys

import pandas as pd
import numpy as np


from dotenv import load_dotenv
from datetime import datetime, timedelta, date
import time
from StreamMaster import *
from _utils import *
load_dotenv()




def twitch_data_pull(session_engine):
    # Initialize starting variables of key folders needed for this process
    clips_folder = os.environ['CLIPS_FOLDER']
    mobile_folder = os.environ['MOBILE_FOLDER']
    inprocess_folder = os.environ['IN_PROCESS_HIGHLIGHTS']
    highlight_folder = os.environ['HIGHLIGHT_FOLDER']
    analytics_folder = os.environ['ANALYTICS_FOLDER']
    ml_folder = os.environ['ML_FOLDER']
    assets = os.environ['ASSETS']
    audio_folder = os.environ['AUDIO_FOLDER']

    # Connecting to a rasberry pi sql data base, mysql was in this instance
    

    
    #Initiate Twitch API connection
    twitch = Twitch(os.environ['TWITCH_APP_ID'], os.environ['TWITCH_APP_SECRET'])


    # # pull clips from twitch api and incorporate into database
    seed = twitch.get_clips(os.environ['TWITCH_CHANNEL_ID'])

    updateTables(session_engine, seed, twitch)

    
    while bool(seed['pagination']): # Loop for remaining pages
        nextPage = seed['pagination']['cursor']
        seed = twitch.get_clips(os.environ['TWITCH_CHANNEL_ID'], after=nextPage)

        updateTables(session_engine, seed, twitch)

        time.sleep(.5)
    print("Clips Finished")
    
    # # pull highlights from twitch api and incorporate into database
    seed = twitch.get_videos(user_id=os.environ['TWITCH_CHANNEL_ID'], video_type = VideoType.HIGHLIGHT)
    seed['data'] = [{**ix, **{'game_id': find_game_id(ix), 'duration': convert_duration_to_sec(ix['duration'])}} for ix in seed['data']]
    updateTables(session_engine, seed, twitch, TwitchVideoStyle.HIGHLIGHT)

    
    while bool(seed['pagination']): # Loop for remaining pages
        nextPage = seed['pagination']['cursor']
        seed = twitch.get_videos(user_id=os.environ['TWITCH_CHANNEL_ID'], video_type = VideoType.HIGHLIGHT, after=nextPage)
        seed['data'] = [{**ix, **{'game_id': find_game_id(ix), 'duration': convert_duration_to_sec(ix['duration'])}} for ix in seed['data']]

        updateTables(session_engine, seed, twitch, TwitchVideoStyle.HIGHLIGHT)

        time.sleep(.5)
    print("Highlights Finished")

    # Set up subqueries for clips with the same names
    sub_query = select(TwitchVideos.title).group_by(TwitchVideos.title).having( func.count(TwitchVideos.title).label("video_count") > 1) # used as input in sub_query2
    sub_query2 = select(TwitchVideos.title, TwitchVideos.created_at, TwitchVideos.video_type.label('video_type'), func.dense_rank().over(order_by=TwitchVideos.created_at, partition_by=[TwitchVideos.title, TwitchVideos.video_type]).label("counts") ).where(TwitchVideos.title.in_(sub_query)).subquery()


    # numerize the clips with the same name
    with Session(session_engine) as session:

        adjustments = session.query(sub_query2).where(sub_query2.c.video_type == TwitchVideoStyle.CLIP).all() #alter video names which had groupings of the same name
        for adjustment in adjustments:
            session.execute(update(TwitchVideos).where(TwitchVideos.title == adjustment[0]).where(TwitchVideos.created_at == adjustment[1]).values(video_name=adjustment[0]+" "+str(adjustment[3])+".mp4"))
        session.commit()

        adjustments = session.query(sub_query2).where(sub_query2.c.video_type == TwitchVideoStyle.HIGHLIGHT).all() #alter video names which had groupings of the same name
        for adjustment in adjustments:
            session.execute(update(TwitchVideos).where(TwitchVideos.title == adjustment[0]).where(TwitchVideos.created_at == adjustment[1]).values(video_name=adjustment[0]+" "+str(adjustment[3])+".mp4"))
        session.commit()

        print("Updating Video Titles Completed")
        # query to check if the videos have been downloaded and processed

        videos = os.listdir(clips_folder)
        mobile_videos = os.listdir(mobile_folder)
        audios = os.listdir(audio_folder)
        for video in session.query(TwitchVideos.video_name).where(TwitchVideos.video_type == TwitchVideoStyle.CLIP).all():
            if video[0] in videos: # check to see if the video has been downloaded
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(downloaded=True))
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(downloaded=False))
            if video[0] in audios: # check to see if the fullscreen video has been processed
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(audio_processed=True))
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(audio_processed=False))
            if video[0] in mobile_videos: # check to see if the mobilescreen video has been processed
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(mobiles_videos_processed=True))
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(mobiles_videos_processed=False))
        

        print("Updating Clip metadata Completed")

        videos = os.listdir(highlight_folder)
        inprocess_videos = os.listdir(inprocess_folder)
        audios = os.listdir(audio_folder)
        for video in session.query(TwitchVideos.video_name).where(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT).all():
            if video[0] in videos: # check to see if the video has been downloaded
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(downloaded=True))
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(downloaded=False))
            if video[0] in audios: # check to see if the fullscreen video has been processed
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(audio_processed=True))
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(audio_processed=False))
            if video[0] in inprocess_videos: # check to see if the mobilescreen video has been processed
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(mobiles_videos_processed=True))
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.video_name == video[0]).values(mobiles_videos_processed=False))

        print("Updating HIGHLIGHT metadata Completed")

        session.commit()

if __name__ == "__main__":
    twitch_data_pull(mysql_engine)