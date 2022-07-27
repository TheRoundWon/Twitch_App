from DashboardInputs import *
def render_overview():
    data_seed = {}
    category_mapper = {'m': "Mobile Only", 'f': "Fully Published", "d": 'Desktop Only'}
    with Session(mysql_engine) as session:
        # for url in session.query(Clip_Tracker.url).where(Clip_Tracker.published == None).order_by(Clip_Tracker.view_count.desc()).all()[:2]:
        for title, game_name, view_count, publishing_status, created_date in session.query(Clip_Tracker.title,Game_Meta.game_name, Clip_Tracker.view_count, Clip_Tracker.published, Clip_Tracker.created_at).select_from(join(Clip_Tracker, Game_Meta)).order_by(Clip_Tracker.view_count.desc()).all():
            if isinstance(publishing_status, PublishingStatus):
                publshing_status_name = category_mapper[publishing_status.name]
            else:
                if publishing_status != None:
                    print(publishing_status)
                publshing_status_name = "Not Published"
            if bool(data_seed.get(publshing_status_name)):
                data_seed[publshing_status_name]['y'].append(game_name)
                data_seed[publshing_status_name]['x'].append(view_count)
                data_seed[publshing_status_name]['text'].append(title)
            else:
                data_seed[publshing_status_name] = {'x': [], 'y': [], 'text': []}
                data_seed[publshing_status_name]['x'].append(view_count)
                data_seed[publshing_status_name]['y'].append(game_name)
                data_seed[publshing_status_name]['text'].append(title)


        # print(session.query(distinct(Clip_Tracker.game_id), Game_Meta.game_name).select_from(join(Clip_Tracker, Game_Meta)).where(Clip_Tracker.published == None).order_by(Clip_Tracker.view_count.desc()).all())
            # print(url[0])

    data = []

    odered_list = ['Fully Published', "Mobile Only", 'Desktop Only', "Not Published"]
    # for key, value in data_seed.items():
    for key in odered_list:
        category_name = key
        data.append(go.Bar(x=data_seed[key]['x'], y = data_seed[key]['y'], text = data_seed[key]['text'], name= category_name, orientation='h'))
    return go.Figure(data, go.Layout(width = 1200, height=600, barmode='stack', title={'text': "Performance By Game and Publishing Status"}, xaxis = {'title': {'text': "View Count"}},yaxis={'categoryorder': 'total ascending', 'title': {'text': 'Game Title'}}))



def render_ts_graph(publishing):
    data_seed = {}
    with Session(mysql_engine) as session:
        if publishing == 'Published':
            queries = session.query(Clip_Tracker.title,Game_Meta.game_name, Clip_Tracker.created_at,  Clip_Tracker.view_count).select_from(join(Clip_Tracker, Game_Meta)).where(Clip_Tracker.published != None).order_by(Clip_Tracker.view_count.desc()).all()
            chart_title = "Performance of Published Clips"
        else:
            queries = session.query(Clip_Tracker.title,Game_Meta.game_name, Clip_Tracker.created_at,  Clip_Tracker.view_count).select_from(join(Clip_Tracker, Game_Meta)).where(Clip_Tracker.published == None).order_by(Clip_Tracker.view_count.desc()).all()
            chart_title = "Performance of Un-Published Clips"
        
        # for url in session.query(Clip_Tracker.url).where(Clip_Tracker.published == None).order_by(Clip_Tracker.view_count.desc()).all()[:2]:
        for title, game_name, created_date, view_count in queries:
            if bool(data_seed.get(game_name)):
                try:
                    data_seed[game_name]['x'].append(date(created_date.year, created_date.month, created_date.day))
                    data_seed[game_name]['y'].append(view_count)
                    data_seed[game_name]['text'].append(title)
                except:
                    data_seed[game_name]['x'] = [created_date]
                    data_seed[game_name]['y'] = [view_count]
                    data_seed[game_name]['color'] = game_colors[game_name]
            else:
                data_seed[game_name] = {'x': [], 'y': [], 'text': [] }
                data_seed[game_name]['x'].append(date(created_date.year, created_date.month, created_date.day))
                data_seed[game_name]['y'].append(view_count)
                data_seed[game_name]['text'].append(title)
                data_seed[game_name]['color'] = game_colors[game_name]
        # print(session.query(distinct(Clip_Tracker.game_id), Game_Meta.game_name).select_from(join(Clip_Tracker, Game_Meta)).where(Clip_Tracker.published == None).order_by(Clip_Tracker.view_count.desc()).all())
            # print(url[0])

    data = []
    for key, value in data_seed.items():
        data.append(go.Bar(x=value['x'], y = value['y'], text = value['text'], name=key, marker={'color': value['color']}))
    return go.Figure(data, go.Layout(barmode='stack', title={'text': chart_title}))



def render_clips_metrics():
    data = []

    fig = make_subplots(rows=1, cols = 4, subplot_titles = ("Average Views per Clip", "Max Views for Clip", "Total Views of Clips", "Number of Clips"), shared_yaxes=True)
    with Session(mysql_engine) as session:
        # for title, game_name, view_count, publishing_status in session.query(Clip_Tracker.title,Game_Meta.game_name, Clip_Tracker.view_count, Clip_Tracker.published).select_from(join(Clip_Tracker, Game_Meta)).order_by(Clip_Tracker.view_count.desc()).all():
        cnt = 0
        for game_name, avg_cnt, max_cnt, sum_cnt, video_cnt in session.query(Game_Meta.game_name, func.avg(Clip_Tracker.view_count), func.max(Clip_Tracker.view_count), func.sum(Clip_Tracker.view_count), func.count(Clip_Tracker.title)).select_from(join(Game_Meta, Clip_Tracker)).group_by(Clip_Tracker.game_id).order_by(func.sum(Clip_Tracker.view_count).desc()).all():
            fig.add_trace(go.Bar(x=[avg_cnt], y = [game_name], orientation='h', showlegend=False, marker= dict(color = [game_colors[game_name]], coloraxis='coloraxis')),row=1, col=1)
            fig.add_trace(go.Bar(x=[max_cnt], y = [game_name], orientation='h', showlegend=False, marker= dict(color = [game_colors[game_name]], coloraxis='coloraxis')),row = 1, col=2)
            fig.add_trace(go.Bar(x=[sum_cnt], y = [game_name], orientation='h', showlegend=False, marker= dict(color = [game_colors[game_name]], coloraxis='coloraxis')), row = 1, col=3)
            fig.add_trace(go.Bar(x=[video_cnt], y = [game_name], orientation='h', showlegend=False, marker= dict(color = [game_colors[game_name]], coloraxis='coloraxis')), row=1,  col=4)
            # # data.append(go.Bar(x=[avg_cnt], y = [game_name]))
            cnt +=1
    fig.update_yaxes(type='category')
    fig.update_layout(barmode='group', yaxis={'categoryorder': 'category descending'}, title={'text': "Breaking each game by different statistics"})
    return fig

def build_video_seed(service):
    video_metrics = execute_api_request(
        service.reports().query,
        ids='channel==MINE',
        startDate='2022-03-01',
        endDate= datetime.today().strftime('%Y-%m-%d'),
        maxResults = 140,
        metrics='estimatedMinutesWatched,views,likes,dislikes,subscribersGained,subscribersLost',
        dimensions='video',
        sort='-estimatedMinutesWatched'
    )

    video_seed = {'video_id': [], 'style': [],'game_name': [], 'title': [], 'creator': [], 'view_count': []}
    with Session(mysql_engine) as session:
        for video_id, style, game_name,  title, creator,  view_count in session.query(Video_yt.id, Video_yt.style, Game_Meta.game_name, Clip_Tracker.title, Clip_Tracker.creator_name, Clip_Tracker.view_count ).select_from(join(join(Clip_Tracker, Game_Meta), Video_yt)).where(Clip_Tracker.published != None).all():
            video_seed['video_id'].append(video_id)
            video_seed['style'].append(style.name)
            video_seed['game_name'].append(game_name)
            video_seed['title'].append(title)
            video_seed['creator'].append(creator)
            video_seed['view_count'].append(view_count)
    return video_seed, video_metrics


def render_yt_graph(clip_metrics_df, value):
    fig = make_subplots(rows=1, cols=4, shared_yaxes=True, vertical_spacing=0.02)
    sub_group = clip_metrics_df.groupby('title').min()
    game_sub = sub_group.loc[sub_group['game_name'] == value]
    sub_filter = clip_metrics_df.loc[clip_metrics_df['game_name'] == value]
    mobile_sub = sub_filter.loc[sub_filter['style'] == 'm']
    full_sub = sub_filter.loc[sub_filter['style'] == 'f']
    # creators = mobile_sub['creator'].unique()
    if not bool(game_sub.empty):
        for creator, value in creators.items():
            fig.add_trace(go.Bar(x=game_sub.loc[game_sub.creator == creator, 'view_count'].values, y=game_sub.loc[game_sub.creator == creator].index, orientation='h', name=creator, legendgroup=creator, marker={'color': value}), row=1, col=1)
            fig.add_trace(go.Bar(x=mobile_sub.loc[mobile_sub.creator == creator, 'views'].values, y=mobile_sub.loc[mobile_sub.creator == creator, 'title'].values, orientation='h', name='Shorts', legendgroup = creator, showlegend=False, marker={'color': 'blue'} ), row=1, col=2)
            fig.add_trace(go.Bar(x=full_sub.loc[full_sub.creator == creator, 'views'].values, y=full_sub.loc[full_sub.creator == creator, 'title'].values, orientation='h', name='Full Screen',  legendgroup = creator, showlegend=False, marker={'color': 'purple'} ), row=1, col=2)
            fig.add_trace(go.Scatter(x=mobile_sub.loc[mobile_sub.creator == creator,'likes_ratio'].values, y=mobile_sub.loc[mobile_sub.creator == creator,'title'].values, mode='markers', name="Shorts", legendgroup = creator, showlegend=False, marker={'color': 'blue', 'size': mobile_sub.loc[mobile_sub.creator == creator,'likes'].values}), row=1, col=3)
            fig.add_trace(go.Scatter(x=full_sub.loc[full_sub.creator == creator,'likes_ratio'].values, y=full_sub.loc[full_sub.creator == creator,'title'].values, mode='markers', name="Full Screen", legendgroup = creator, showlegend=False, marker={'color': 'purple', 'size': full_sub.loc[full_sub.creator == creator,'likes'].values}), row=1, col=3)
            
            fig.add_trace(go.Bar(x=sub_filter.loc[sub_filter.creator == creator, 'subscribersGained'].values, y=sub_filter.loc[sub_filter.creator == creator,'title'].values, orientation='h', name=creator, legendgroup = creator, showlegend=False, marker={'color': 'green'} ), row=1, col=4)
            fig.add_trace(go.Bar(x=sub_filter.loc[sub_filter.creator == creator, 'subscribersLost'].values, y=sub_filter.loc[sub_filter.creator == creator,'title'].values, orientation='h', name=creator, legendgroup = creator, showlegend=False, marker={'color': 'red'} ), row=1, col=4)
    else:
        game_sub = sub_filter.loc[sub_filter['game_name'] == value]
        for creator, value in creators.items():
            fig.add_trace(go.Bar(x=game_sub.loc[game_sub.creator == creator, 'view_count'].values, y=game_sub.loc[game_sub.creator == creato, 'title'].values, orientation='h', name=creator, legendgroup=creator, marker={'color': value}), row=1, col=1)

    fig.update_layout(barmode='stack', xaxis3 = {'range': [0,1], 'tickformat': ".0%"}, xaxis4={'dtick': 1} )
    fig.layout.height = None
    return fig