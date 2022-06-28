""" Check Associated iPython Notebook for better documentation - the following
script is designed to be run on a schedule (ideally daily) where the script checks for the newest clips created for a channel and downloads them to the appropriate locations
specified in the .env file
"""
#Import necessary packages
import os
import sys
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
import pandas as pd
import numpy as np
import subprocess

from dotenv import load_dotenv
from datetime import datetime, timedelta, date
import time
from StreamMaster import *
load_dotenv()
def adjust_output(output: dict, cls,  mode='data', schema_mapper=schema_mapper): 
        """ The following function is designed to help construct the necessary dictionaries needed for the class construction

        Args:
            output (dictionary): output from each twitch API call.
            cls: ORM to map the dictionary object to and add to dictionary
            mode (str, optional): key value to pull from the output dictionary. Defaults to 'data'.
            schema_mapper (dictionary, optional): Mapper for schema. Defaults to schema_mapper.

        Yields:
            dict: Adusted dictionary necessary for class initialization
        """
        for report in output[mode]:
            newReport = {}
            for col, value in report.items():
                try:
                    attr = getattr(cls, col)
            
                    if value == 'None' or not bool(value):
                        newReport[col] = None
                    else:
                        newType = schema_mapper.get(attr.type)
                        if isinstance(attr.type, DATETIME):
                            print
                            newReport[col] = datetime.fromisoformat(value[:-1])
                        
                        elif bool(newType):
                            newReport[col] = newType(value)
                        else:
                            newReport[col] = value

            
                        
                except Exception as e:
                    pass

            yield newReport



def main():
    # Initialize starting variables of key folders needed for this process
    clips_folder = os.environ['CLIPS_FOLDER']
    mobile_folder = os.environ['MOBILE_FOLDER']
    fullscreen_folder = os.environ['FULLSCREEN_FOLDER']
    analytics_folder = os.environ['ANALYTICS_FOLDER']
    ml_folder = os.environ['ML_FOLDER']
    assets = os.environ['ASSETS']

    # Connecting to a rasberry pi sql data base, mysql was in this instance
    engine = create_engine(f"mysql+mysqlconnector://{os.environ['USER_NAME']}:{os.environ['PASSWORD']}@{os.environ['PI']}/{os.environ['MAIN_DB']}" )

    
    #Initiate Twitch API connection
    twitch = Twitch(os.environ['TWITCH_APP_ID'], os.environ['TWITCH_APP_SECRET'])


    # # pull data from twitch api and incorporate into database
    seed = twitch.get_clips(os.environ['TWITCH_CHANNEL_ID'])

    with Session(engine) as session: # Loop for first page
        for item in adjust_output(seed, Clip_Tracker):
                if not bool(session.query(Game_Meta).where(Game_Meta.game_id==item['game_id']).all()):
                    session.add(Game_Meta(game_id=item['game_id'], game_name= twitch.get_games(item['game_id'])['data'][0]['name'], Purchased=True, downloaded=True, platform="PS5"))
                    session.commit()
                item['video_name'] = item['title'] + ".mp4"

                if not bool(session.query(Clip_Tracker).where(Clip_Tracker.id==item['id']).all()):
                    session.add(Clip_Tracker(**item))
                    session.commit()
                else:
                    pass
        while bool(seed['pagination']): # Loop for remaining pages
            nextPage = seed['pagination']['cursor']
            seed = twitch.get_clips(os.environ['TWITCH_CHANNEL_ID'], after=nextPage)

            for item in adjust_output(seed, Clip_Tracker):
                if not bool(session.query(Game_Meta).where(Game_Meta.game_id==item['game_id']).all()):
                    session.add(Game_Meta(game_id=item['game_id'], game_name= twitch.get_games(item['game_id'])['data'][0]['name'], Purchased=True, downloaded=True, platform="PS5"))
                    session.commit()
                    # print(item)
                item['video_name'] = item['title'] + ".mp4"

                if not bool(session.query(Clip_Tracker).where(Clip_Tracker.id==item['id']).all()):
                    session.add(Clip_Tracker(**item))
                    session.commit()
                    # print(item)
                else:
                    session.execute(update(Clip_Tracker).where(Clip_Tracker.id == item['id']).values(view_count=item['view_count']))
                    session.commit()
                    
            time.sleep(.5)

    # Set up subqueries for clips with the same names
    sub_query = select(Clip_Tracker.title).group_by(Clip_Tracker.title).having( func.count(Clip_Tracker.title).label("video_count") > 1) # used as input in sub_query2
    sub_query2 = select(Clip_Tracker.title, Clip_Tracker.created_at, func.dense_rank().over(order_by=Clip_Tracker.created_at, partition_by=Clip_Tracker.title).label("counts") ).where(Clip_Tracker.title.in_(sub_query))


    # numerize the clips with the same name
    with Session(engine) as session:

        adjustments = session.execute(sub_query2).all() #alter video names which had groupings of the same name
        for adjustment in adjustments:
            session.execute(update(Clip_Tracker).where(Clip_Tracker.title == adjustment[0]).where(Clip_Tracker.created_at == adjustment[1]).values(video_name=adjustment[0]+" "+str(adjustment[2])+".mp4"))
        session.commit()

        # query to check if the videos have been downloaded and processed

        videos = os.listdir(clips_folder)
        fullscreen_videos = os.listdir(fullscreen_folder)
        mobile_videos = os.listdir(mobile_folder)
        for video in session.query(Clip_Tracker.video_name).all():
            if video[0] in videos: # check to see if the video has been downloaded
                session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == video[0]).values(downloaded=True))
            else:
                session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == video[0]).values(downloaded=False))
            if video[0] in fullscreen_videos: # check to see if the fullscreen video has been processed
                session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == video[0]).values(full_screen_videos_processed=True))
            else:
                session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == video[0]).values(full_screen_videos_processed=False))
            if video[0] in mobile_videos: # check to see if the mobilescreen video has been processed
                session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == video[0]).values(mobiles_videos_processed=True))
            else:
                session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == video[0]).values(mobiles_videos_processed=False))


        session.commit()

        # Download the undownloaded videos
        for video_name, url, ID in session.query(Clip_Tracker.video_name, Clip_Tracker.url, Clip_Tracker.id).where(Clip_Tracker.downloaded == False).all():
            subprocess.call(['twitch-dl', 'download', '-q', 'source', url, '-o', os.path.join(clips_folder, video_name)])
            session.execute(update(Clip_Tracker).where(Clip_Tracker.id == ID).values(downloaded=True))
            session.commit()
        print("All Done!")

if __name__ == "__main__":
    main()