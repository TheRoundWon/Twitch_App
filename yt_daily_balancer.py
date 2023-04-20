from yt_shorts_upload import *




def main(engine, service):
    folder_mapper = {'d': mobile_folder, 'm': clips_folder}
    mode_mapper = {'d': "shorts", 'm': None}
    with Session(engine)as session:
        for clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url, publishing_status in session.query(Clip_Tracker.id, Game_Meta.game_name, Clip_Tracker.creator_name, Game_Meta.platform, Clip_Tracker.title, Clip_Tracker.video_name, Clip_Tracker.url, Clip_Tracker.published).select_from(join(Game_Meta,Clip_Tracker)).where(and_(Clip_Tracker.published != PublishingStatus.f,  Clip_Tracker.published != None, Clip_Tracker.mobiles_videos_processed == True)).order_by(Clip_Tracker.view_count.desc()).all()[:1]:
            # print(game_title, clip_creator, console, clip_title, video_name)
            try:
                # First upload the full screen
                request_body = {
                    'snippet': {
                        'categoryI': 20,
                        'title': " | ".join([console, game_title+" Gameplay", clip_title]),
                        'description': createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url, mode=mode_mapper[publishing_status.name]),
                        'tags': ["Video Games", game_title, console, "Gaming"]
                        },
                        'status': {
                            'privacyStatus': 'public',
                            'selfDeclaredMadeForKids': False, 
                            'madeForKids': False,
                        },
                        'notifySubscribers': True
                    }
                mediaFile = MediaFileUpload(os.path.join(folder_mapper[publishing_status.name], video_name))
                normal_response_upload = service.videos().insert(
                    part='snippet,status',
                    body=request_body,
                    media_body=mediaFile
                ).execute()
                # pause after upload
                if mode_mapper[publishing_status.name] == 'shorts':
                    print("Shorts Upload complete", clip_title)
                    search_title = 'shorts'
                else:                        
                    print("Normal Upload complete", clip_title)
                    search_title = game_title
                playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%{search_title}%')).first()[0]
                service.playlistItems().insert(part = "snippet", body = {"snippet": {'playlistId': playlistId, 'resourceId': {'videoId': normal_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()
                session.execute(update(Clip_Tracker).where(Clip_Tracker.id == clip_id).values({'published' : PublishingStatus.f}))
                session.commit()

            except Exception as e:
                print("Upload failed", clip_title, e)

if __name__ == "__main__":
    main(mysql_engine, service)