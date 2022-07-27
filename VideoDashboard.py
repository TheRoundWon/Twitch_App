


from DashboardFunctions import *


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1(f'{CHANNEL} Dashboard'),
    dcc.Tabs(id="tabs-example-graph", value='clips-ov-graph', children=[
        dcc.Tab(label='Clips Overview', value='clips-ov-graph'),
        dcc.Tab(label='Clips Time Series Performance', value='clips-ts-graph'),
        dcc.Tab(label='Clips Metrics', value='clips-met-graph'),
        dcc.Tab(label='YouTube Overlay', value='yt-graph')

    ]),html.Div(
    [dcc.RadioItems(['Published', 'Un-Published'], 'Published', id='published-select', inline=True),
     dcc.Dropdown(
                id='game-select',
                options=[{'label': value, 'value': value} for key, value in games.items()],
                value="Demon's Souls"
            , style={'display': 'none'})]),
    html.Div(id='tabs-content-example-graph'),
    dcc.Graph(id='main-chart')
])


figure_title = {
    'clips-ts-graph': html.Div([
            html.H3('Clips Time Series Performance')
        ]),
    'clips-ov-graph': html.Div([
            html.H3('Clips Overview Performance')
        ]),
    'clips-met-graph': html.Div([
            html.H3('Clips Metrics Overview')
        ]),
    'yt-graph': html.Div([
            html.H3('Clips Metrics Overview')
        ]),
}

figure_dict = {
    'clips-ts-graph': render_ts_graph,
    'clips-ov-graph': render_overview,
    'clips-met-graph': render_clips_metrics,
    'yt-graph': render_yt_graph
}

video_seed, video_metrics = build_video_seed(youtubeAnalytics)
clip_metrics_df = pd.DataFrame(video_metrics['rows'], columns=['video_id', 'estimatedMinutesWatched', 'views', 'likes', 'dislikes', 'subscribersGained', 'subscribersLost']).set_index('video_id').join(pd.DataFrame(video_seed).set_index('video_id'))
clip_metrics_df['likes_ratio'] = (clip_metrics_df['likes']/(clip_metrics_df['likes'] + clip_metrics_df['dislikes'])).fillna(0)
@app.callback(Output('main-chart', 'figure'),
[Input('published-select', 'value'), Input('game-select', 'value'), Input('tabs-example-graph', 'value')]
)
def render_published_videos(publishing, game_select, tab):
    if tab == 'clips-ts-graph':
        return figure_dict[tab](publishing)
    elif tab == 'yt-graph':
        return figure_dict[tab](clip_metrics_df, game_select)
    else:
        return figure_dict[tab]()

# @app.callback(Output('main-chart', 'figure'),
# [Input('game-select', 'value'), Input('tabs-example-graph', 'value')]
# )
# def render_published_videos(game_select, tab):
#     if tab == 'yt-graph':
#         return figure_dict[tab](game_select)
#     else:
#         return figure_dict[tab]()


@app.callback([Output('tabs-content-example-graph', 'children'), Output('published-select', 'style'), Output('game-select', 'style')],
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    if tab == 'clips-ts-graph':
        return figure_title[tab], {'display': 'block'}, {'display': 'none'}
    elif tab == 'yt-graph':
        return figure_title[tab], {'display': 'none'}, {'display': 'block'}
    else:
        return figure_title[tab], {'display': 'none'}, {'display': 'none'}

if __name__ == '__main__':

    app.run_server(debug=True, port="8050")