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



def main(engine, service, args):
    with Session(engine)as session:
        for clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url in session.query(Clip_Tracker.id, Game_Meta.game_name, Clip_Tracker.creator_name, Game_Meta.platform, Clip_Tracker.title, Clip_Tracker.video_name, Clip_Tracker.url).select_from(join(Game_Meta,Clip_Tracker)).where(and_(Clip_Tracker.published == None,  Clip_Tracker.mobiles_videos_processed == True)).order_by(Clip_Tracker.view_count.desc()).all()[:args.videos]:
            # print(game_title, clip_creator, console, clip_title, video_name)
            try: # First Upload
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
                mediaFile = MediaFileUpload(os.path.join(clips_folder, video_name))
                normal_response_upload = service.videos().insert(
                    part='snippet,status',
                    body=request_body,
                    media_body=mediaFile
                ).execute()
                # pause after upload
                print("Normal Upload complete", clip_title)
            except Exception as e:
                print("Normal Failed", e)
            try:
                for key, thumbnail in normal_response_upload['snippet']['thumbnails'].items(): # first ensure that thumbnails are mapped in thumbnail table
                    if not bool(session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()):
                        session.add(Thumbnails(asset=thumbnail['url'], width = thumbnail['width'], height=thumbnail['height']))
                        session.commit()
                    normal_response_upload['snippet']['thumbnails'][key]['id'] = session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()[0]
            except Exception as e:
                print("Full Video Thumbnails mapping failed", e, normal_response_upload)
            try:
                style = 'f'
                session.add( Video_yt(id = normal_response_upload.get('id'), 
                            clip_id=clip_id, 
                            title = normal_response_upload.get('snippet').get('title'),
                            filename = video_name,
                            style = style,
                            description = normal_response_upload.get('snippet').get('description'),
                            tb_default = normal_response_upload.get('snippet').get('snippet').get('thumbnails')('default')('id'), 
                            tb_medium = normal_response_upload.get('snippet').get('snippet').get('thumbnails')('medium')('id'),
                            tb_high = normal_response_upload.get('snippet').get('snippet').get('thumbnails')('high')('id'), 
                            tb_standard = normal_response_upload.get('snippet').get('snippet').get('thumbnails')('high')('id') ,
                            tags = normal_response_upload.get('snippet').get('snippet').get('tags')
                            
                            )
                            )
                session.commit()
                time.sleep(5)
            except Exception as e:
                print("Full Video adding to sql failed", e)
            try:
                normal_playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%{game_title}%')).first()[0]
                service.playlistItems().insert(part = "snippet", body = {"snippet": {'playlistId': normal_playlistId, 'resourceId': {'videoId': normal_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()
                

                #upload the short
                request_body['description'] = createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url, mode='shorts')
                mediaFile = MediaFileUpload(os.path.join(mobile_folder, video_name))
                mobile_response_upload = service.videos().insert(
                    part='snippet,status',
                    body=request_body,
                    media_body=mediaFile
                ).execute()
                time.sleep(5)
            except Exception as e:
                print("Mobile video upload failed", e)
            try:
                for key, thumbnail in mobile_response_upload['snippet']['thumbnails'].items(): # first ensure that thumbnails are mapped in thumbnail table
                    if not bool(session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()):
                        session.add(Thumbnails(asset=thumbnail['url'], width = thumbnail['width'], height=thumbnail['height']))
                        session.commit()
                    mobile_response_upload['snippet']['thumbnails'][key]['id'] = session.query(Thumbnails.id).where(Thumbnails.asset == thumbnail['url']).first()[0]
            except Exception as e:
                print("Mobile Video Thumbnails mapping failed", e, mobile_response_upload)
            try:
                mobile_playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%short%')).first()[0]
                service.playlistItems().insert(part = 'snippet', body = {"snippet": {'playlistId': mobile_playlistId, 'resourceId': {'videoId': mobile_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()
                style = 'm'
                session.add( Video_yt(id = mobile_response_upload.get('id'), 
                            clip_id=clip_id, 
                            title = mobile_response_upload.get('snippet').get('title'),
                            filename = video_name,
                            style = style,
                            description = mobile_response_upload.get('snippet').get('description'),
                            tb_default = mobile_response_upload.get('snippet').get('snippet').get('thumbnails')('default')('id'), 
                            tb_medium = mobile_response_upload.get('snippet').get('snippet').get('thumbnails')('medium')('id'),
                            tb_high = mobile_response_upload.get('snippet').get('snippet').get('thumbnails')('high')('id'), 
                            tb_standard = mobile_response_upload.get('snippet').get('snippet').get('thumbnails')('high')('id') ,
                            tags = mobile_response_upload.get('snippet').get('snippet').get('tags')
                            
                            )
                            )
                session.commit()
            except Exception as e:
                print("Mobile video YT table addition failed", e)
                session.execute(update(Clip_Tracker).where(Clip_Tracker.id == clip_id).values({'published' : PublishingStatus.f}))
                session.commit()
            try:
                with Session(engine) as session:
                    session.execute(insert(yt_vid_pl_mapper).values({"yt_playlist_id": mobile_playlistId, 'yt_video_id': mobile_response_upload.get('id')}))
                    session.execute(insert(yt_vid_pl_mapper).values({"yt_playlist_id": normal_playlistId, 'yt_video_id': normal_response_upload.get('id')}))
                    session.commit()


            except Exception as e:
                print("Playlist and Video Mappings failed", clip_title, e)



if __name__ == "__main__":
    main(engine, service, args)