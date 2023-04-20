import ffmpeg
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, VideoType
from StreamMaster import *
import regex as re
from moviepy.editor import *
import moviepy.video as mpy
from moviepy.video.tools.drawing import color_split
import glob
from collections import defaultdict
from string import punctuation
strtString = func.substring_index(TwitchVideos.title, "|", 1)
endString = func.substring_index(TwitchVideos.title, "|", -1)
midString = func.trim(func.substring(
    TwitchVideos.title,
    func.length(strtString)+2,
    func.length(TwitchVideos.title) - func.length(strtString) - func.length(endString)-2
))

highlightMode = func.substring_index(midString, ' ', 1)
highlightModeIx = func.substring_index(midString, ' ', -1)

def create_mobile_video(logo_path, file_input, file_output, x_center, width, height):
    v1 = (
    ffmpeg
    .input(file_input)
    .crop(x_center, 0, width, height)
    .filter('eq', brightness=-1)
    )
    a1 = ffmpeg.input(file_input).audio
    v2 = (
        ffmpeg
        .input(file_input)
        .filter('scale', 614,-1)
    )

    overlay_file = ffmpeg.input(logo_path)

    (
        ffmpeg
        .concat(v1,a1, v=1, a=1)
        .overlay(overlay_file)
        .overlay(v2, y=300)
        .output(file_output)
        .run()
    )

def add_overlay(logo_path, file_input):
    overlay_file = ffmpeg.input(logo_path)
    return (
        ffmpeg
        .input(file_input)
        .overlay(overlay_file, x='main_w-overlay_w')
    )


def create_full_video(logo_path, file_input, file_output):
    # overlay_file = ffmpeg.input(logo_path)
    a1 = ffmpeg.input(file_input).audio
    # Create Video
    v1 = add_overlay(logo_path, file_input)

    (
        ffmpeg
        .concat(v1, a1, v=1, a=1)
        .output(file_output, enc_time_base='1/60')
        .run()
    )

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


def updateGames_data(session_engine, twitch, item):
    with Session(session_engine) as session:
        if not bool(session.query(Game_Meta).where(Game_Meta.game_id==item['game_id']).all()):
            session.add(Game_Meta(game_id=item['game_id'], game_name= twitch.get_games(item['game_id'])['data'][0]['name'], Purchased=True, downloaded=True, platform="PS5"))
            session.commit()
        checkID, download_status = session.query(Game_Meta.game_id, Game_Meta.downloaded).where(Game_Meta.game_id==item['game_id']).first()
        if not bool(download_status):
            session.execute(update(Game_Meta).where(Game_Meta.game_id == checkID).values({'downloaded': True}))
        session.commit()

def updateTables(session_engine, seed, twitch, video_mode=TwitchVideoStyle.CLIP):
    with Session(session_engine) as session: # Loop for first page
        for item in adjust_output(seed, TwitchVideos):
            updateGames_data(session_engine, twitch, item)
            item['video_name'] = item['title'] + ".mp4"
            item['audio_filename'] = item['title'] + ".wav"
            

            if not bool(session.query(TwitchVideos).where(TwitchVideos.id==item['id']).all()):
                session.add(TwitchVideos(**item))
                session.commit()
            else:
                session.execute(update(TwitchVideos).where(TwitchVideos.id == item['id']).values({'view_count': item['view_count'], 'title':item['title'], 'video_name': item['video_name'], 'audio_filename': item['audio_filename'], 'video_type':video_mode}))
                session.commit()


def find_game_id(returns) -> int:
    patterns = "game_id: \d*"
    game_id = re.findall(patterns, returns['description'])[0]
    return int(game_id.split(':')[-1].strip())



def find_coop(returns) -> list:
    patterns = "COOP: .*"
    coops = re.findall(patterns, returns['description'])[0]
    return [x.strip() for x in coops.split(':')[-1].split(',')]



def convert_duration_to_sec(duration) -> float:
    """Convert twitch time stamps into seconds of duration"""
    hour_splits = duration.split('h')
    hours = 0
    minutes = 0
    if len(hour_splits) > 1:
        hours = int(hour_splits[0]) * 60 * 60
        duration = hour_splits[-1]
    minute_splits = duration.split('m')
    if len(minute_splits) > 1:
        minutes = int(minute_splits[0]) * 60
        duration = minute_splits[-1]
    seconds = int(duration.split('s')[0])

    return hours+minutes+seconds



def convert_duration_to_timestamp(duration: float)-> str:
    """Convert duration of seconds into youtube friendly timestamp"""
    hours = int(duration//(60*60))
    duration -= hours*(60*60)
    minutes = int(duration // 60)
    duration -= minutes*(60)
    return f"{hours:02d}:{minutes:02d}:{int(duration):02d}"



def create_title(title_text, filename = "title_holder.mp4"):
    return (
        ffmpeg.input(filename)
        .drawtext(title_text, x='(w-text_w)/2', y='(h-text_h)/2', fontsize=24, fontcolor='white'
        )
    )



def add_transition(stream):
    return (
        stream
        .filter('fade', type='in', start_time=0, duration=0.5)
        .filter('fade', type='out', start_time=2.5, duration=0.5)
    )



def clear_tempfiles(root: str = 'tmp_folder/*_ts.mp4'):
    """Remove temp files"""
    [os.remove(path) for path in glob.glob(root)]



def generate_timestamps(session_engine: engine.base.Engine, title: str, duration_offset = 3) -> dict:

    substamps = {}
    total_duration = duration_offset
    modes = ['QUEST', 'BOSS', 'FAIL', 'BLOOPER']
    bossCounter = defaultdict(int)
    with Session(session_engine) as session:
        for mode in modes:
            if bool(session.query(strtString, TwitchVideos.video_name, endString).where(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT).order_by(endString, highlightModeIx).where(highlightMode == mode).where(endString == title).all()):
                total_duration += 3

                for duration, fil, end in  session.query(TwitchVideos.duration, TwitchVideos.video_name, strtString).where(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT).order_by(endString, highlightModeIx).where(highlightMode == mode).where(endString == title).all():
                    bossCounter[end.strip()] += 1
                    if bool(substamps.get(end.strip())):
                        substamps[end.strip() + f" {bossCounter[end.strip()]}"] = convert_duration_to_timestamp(total_duration)
                    else:
                        substamps[end.strip()] = convert_duration_to_timestamp(total_duration)
                    total_duration += duration + 3
    return substamps



def timestamps_to_string(timestamp: dict) -> str:
    """Convert dictionary of timestamps into string

    Args:
        timestamp (dict): dictionary of time stamps {'name': 'timestamp'}

    Returns:
        str: Youtube friendly timestamp string
    """
    output_str = "00:00:00 - Intro\n"
    for key, value in timestamp.items():
        output_str += value + f" - {key}\n"
    return output_str



def createDescription(game_title, channel_id, clip_creator, console, twitch_channel, clip_url, tag_seed = ['videogames', 'followme', 'twitch', 'casualplay', 'TheRoundWon'], mode = None) -> str:
    
    if clip_creator == "TheRoundWon":
        clip_creator = "TheSquareWon"
    intro_string = "Follow me on Twitch for weekly live gameplay\n"
    twitch_url = f"https://twitch.tv/{twitch_channel}\n"
    clip_url = f"Check out the original clip on Twitch! {clip_url}\n\n"
    tags = ["#"+game_title.translate(str.maketrans('','',punctuation)).replace(" ", "")] + ['#'+sd for sd in tag_seed]  + ["#"+console]
    if mode == "Shorts" or mode == "shorts":
        tags = tags + ["#"+mode] 
    elif isinstance(mode, dict):
        clip_url += timestamps_to_string(mode) + '\n'
       
    tagString = " ".join(tags)+"\n"
    game_string = f"Game play Footage from {game_title}\n"
    thank_string = f"Big Thanks to {clip_creator} for capturing the footage!\n\n"
    subscribe_string = f"Subscribe to get notified of new videos:\nhttps://www.youtube.com/channel/{channel_id}?sub_confirmation=1"
    return intro_string+twitch_url+clip_url+tagString+game_string+thank_string+subscribe_string



def unfinished_highlights(session_engine: engine.base.Engine, processed_highlights = 'PROCESSED_HIGHLIGHTS') -> list:
    with Session(session_engine) as session:
        titles = [ix[0]for ix in session.query(func.distinct(endString)).where(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT).all()]
        titles = [f"{title}.mp4" for title in titles]
        completed_highlights = os.listdir(os.environ[processed_highlights])
        return [title[:-4] for title in titles if title not in completed_highlights]



def ready_highlights(session_engine: engine.base.Engine) -> list:
    titles = unfinished_highlights(session_engine)
    with Session(session_engine) as session:
        unfinished = [ix[0]for ix in session.query(func.distinct(endString)).where(endString.in_(titles)).where(TwitchVideos.mobiles_videos_processed == False).all()]
        return [title for title in titles if title not in unfinished]
    


def make_highlight_segment(session_engine: engine.base.Engine, title_files: list, title:str,  tmp_folder: str, mode: str, input_highlights: str) -> list:
    a1 = ffmpeg.input("title_holder.mp4").audio
    with Session(session_engine) as session:
        if bool(session.query(strtString, TwitchVideos.video_name, endString).where(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT).order_by(endString, highlightModeIx).where(highlightMode == mode).where(endString == title).all()):
            ffmpeg.concat(add_transition(create_title(mode+ " Highlights", 'title_holder.mp4')), a1, v=1, a=1).output(os.path.join(tmp_folder, f"{mode}_ts.mp4"), enc_time_base='1/60').run()
            mode_title_path = os.path.join(tmp_folder, f"{mode}_ts.mp4")
            title_files.append(f"'{mode_title_path}'")
            for bossName, fil, end in  session.query(strtString, TwitchVideos.video_name, endString).where(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT).order_by(endString, highlightModeIx).where(highlightMode == mode).where(endString == title).all():
                boss_title_path = os.path.join(tmp_folder, f"{bossName}_ts.mp4")
                if f"{bossName}_ts.mp4" not in os.listdir(tmp_folder):
                    ffmpeg.concat(add_transition(create_title(bossName, 'title_holder.mp4')), a1, v=1, a=1).output(os.path.join(tmp_folder, f"{bossName}_ts.mp4"), enc_time_base='1/60').run()
                title_files.append(f"'{boss_title_path}'")
                title_files.append(f"'{os.path.join(input_highlights, fil)}'")
        return title_files
    



def make_highlights_compilation(session_engine: engine.base.Engine, input_file_path: str, output_file_path: str, modes: list = ['QUEST', 'BOSS', 'FAIL', 'BLOOPER']):
    tmp_folder = os.environ['TMP_FOLDER']
    titles = ready_highlights(session_engine)
    for title in titles:
        clear_tempfiles()
        title_files = []
        a1 = ffmpeg.input("title_holder.mp4").audio
        ffmpeg.concat(add_transition(create_title(title, 'title_holder.mp4')), a1, v=1, a=1).output(f"tmp_folder/{title}_ts.mp4", enc_time_base='1/60').run()
        main_title_path = os.path.join(tmp_folder, f"{title}_ts.mp4")
        title_files.append(f"'{main_title_path}'")
        for mode in modes:
            title_files = make_highlight_segment(session_engine, title_files, title, tmp_folder, mode, input_file_path)
        with open('concat.txt', 'w') as f:
            f.writelines([('file %s\n' % input_path) for input_path in title_files])
        ffmpeg.input('concat.txt', format='concat', safe=0).output(os.path.join(output_file_path, f'{title}.mp4'), c='copy', r=60).run()
        
        