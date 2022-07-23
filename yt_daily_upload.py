"""
The following script is designed to access the Youtube Data API and confirm which Youtube videos
have already been uploaded and whether all the videos are accounted for and correctly mapped to the right playlists

"""


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


load_dotenv()

parser = argparse.ArgumentParser()

parser.add_argument("videos", type=int, nargs = "?", const=1, default=1, help="number of videos to upload")

args = parser.parse_args()


engine = create_engine(f"mysql+mysqlconnector://{os.environ['USER_NAME']}:{os.environ['PASSWORD']}@{os.environ['PI']}/{os.environ['MAIN_DB']}" )


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
def createDescription(game_title, channel_id, clip_creator, console, twitch_channel, clip_url, tag_seed = ['videogames', 'followme', 'twitch', 'casualplay', 'TheRoundWon'], mode = None):
    
    if clip_creator == "TheRoundWon":
        clip_creator = "TheSquareWon"
    intro_string = "Follow me on Twitch for weekly live gameplay\n"
    twitch_url = f"https://twitch.tv/{twitch_channel}\n"
    clip_url = f"Check out the original clip on Twitch! {clip_url}\n\n"
    tags = ["#"+game_title.replace(" ", "").replace("'", "")] + ['#'+sd for sd in tag_seed]  + ["#"+console]
    if mode == "Shorts" or mode == "shorts":
        tags = tags + ["#"+mode] 
       
    tagString = " ".join(tags)+"\n"
    game_string = f"Game play Footage from {game_title}\n"
    thank_string = f"Big Thanks to {clip_creator} for capturing the footage!\n\n"
    subscribe_string = f"Subscribe to get notified of new videos:\nhttps://www.youtube.com/channel/{channel_id}?sub_confirmation=1"
    return intro_string+twitch_url+clip_url+tagString+game_string+thank_string+subscribe_string


def main(engine, service, args):
    with Session(engine)as session:
        for clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url in session.query(Clip_Tracker.id, Game_Meta.game_name, Clip_Tracker.creator_name, Game_Meta.platform, Clip_Tracker.title, Clip_Tracker.video_name, Clip_Tracker.url).select_from(join(Game_Meta,Clip_Tracker)).where(and_(or_(Clip_Tracker.published == None, Clip_Tracker == PublishingStatus.d), Clip_Tracker.mobiles_videos_processed == True)).order_by(Clip_Tracker.view_count.desc()).all()[:args.videos]:
            # print(game_title, clip_creator, console, clip_title, video_name)
            try:
                # First upload the full screen
                request_body = {
                    'snippet': {
                        'categoryI': 20,
                        'title': " | ".join([console, game_title+" Gameplay", clip_title]),
                        'description': createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url),
                        'tags': ["Video Games", game_title, console, "Gaming"]
                        },
                        'status': {
                            'privacyStatus': 'public',
                            'selfDeclaredMadeForKids': False, 
                            'madeForKids': False,
                        },
                        'notifySubscribers': True
                    }
                # mediaFile = MediaFileUpload(os.path.join(fullscreen_folder, video_name))
                # normal_response_upload = service.videos().insert(
                #     part='snippet,status',
                #     body=request_body,
                #     media_body=mediaFile
                # ).execute()
                # # pause after upload
                # print("Normal Upload complete", clip_title)
                # time.sleep(5)
                # playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%{game_title}%')).first()[0]
                # service.playlistItems().insert(part = "snippet", body = {"snippet": {'playlistId': playlistId, 'resourceId': {'videoId': normal_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()

                #upload the short
                request_body['description'] = createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url, mode='shorts')
                mediaFile = MediaFileUpload(os.path.join(mobile_folder, video_name))
                mobile_response_upload = service.videos().insert(
                    part='snippet,status',
                    body=request_body,
                    media_body=mediaFile
                ).execute()
                time.sleep(5)
                playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%short%')).first()[0]
                service.playlistItems().insert(part = 'snippet', body = {"snippet": {'playlistId': playlistId, 'resourceId': {'videoId': mobile_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()
                session.execute(update(Clip_Tracker).where(Clip_Tracker.id == clip_id).values({'published' : PublishingStatus.m}))
                session.commit()
                print("Short Upload complete", clip_title)

            except Exception as e:
                print("Upload failed", clip_title, e)



if __name__ == "__main__":
    main(mysql_engine, service, args)