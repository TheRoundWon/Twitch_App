from StreamMaster import *

audio_folder = os.listdir(os.environ['AUDIO_FOLDER'])
with Session(mysql_engine) as session:
    
    for clip in session.query(Clip_Tracker).all():
        if clip.title + ".wav" in audio_folder:
            AUDIO_PROCESSING = True
            print(clip.title)
        else:
            AUDIO_PROCESSING = False
        session.add(TwitchVideos(
            id = clip.id,  
            url = clip.url,  
            embed_url = clip.embed_url,  
            broadcaster_id = clip.broadcaster_id,  
            creator_id  = clip.creator_id,   
            creator_name = clip.creator_name,  
            video_id = clip.video_id,  
            game_id  = clip.game_id,   
            language  = clip.language,   
            title  = clip.title, 
            view_count = clip.view_count, 
            video_name = clip.video_name, 
            video_type = TwitchVideoStyle.CLIP, 
            yt_filename = clip.yt_filename,  
            audio_filename = clip.title + ".wav",  
            created_at = clip.created_at, 
            thumbnail_url = clip.thumbnail_url,  
            duration = clip.duration, 
            published = clip.published,  
            downloaded = clip.downloaded,  
            audio_processed = AUDIO_PROCESSING, 
            category = None,  
            mobiles_videos_processed = clip.mobiles_videos_processed 
            ))
        session.commit()