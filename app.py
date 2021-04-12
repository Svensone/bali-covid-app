# Import required libraries
import pickle
import copy
import pathlib
import urllib.request
import dash
import math
import datetime as dt
import pandas as pd
import json
import os 

## Plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html

## MongoDB Atlas Connect
from dotenv import load_dotenv
import pymongo # dont forget dnspython add to req.txt

# Multi-dropdown options
from controls import REGENCIES
import controls

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

# ------------------------------------------------------------------------------
# 1. Data
# ------------------------------------------------------------------------------
## FROM MONGODB ATLAS

load_dotenv()
client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
db = client.bali_covid
collection = db.bali_regency_data

data_bali1 = pd.DataFrame(list(db.bali_regency_data.find()))
# print(data_bali1.head())

## FROM CSV
# bali regencies
data_covid_bali = DATA_PATH.joinpath('bali_regency_data.csv')
# indo provinces (change to kawalcovid)
data_covid_indo = DATA_PATH.joinpath('indo_province_data.csv')
# delete bw Data
data_covid_germany = DATA_PATH.joinpath('county_covid_BW.csv')
# data comparison and indo !
data_world = DATA_PATH.joinpath('world_data.csv')

geojson_bali = DATA_PATH.joinpath('new_bali_id.geojson')
geojson_indo = DATA_PATH.joinpath('new_indo_id.geojson')
geojson_germany = DATA_PATH.joinpath('geojson_ger.json')

### Color Model
################
# Use sequential.Blues
color1 = 'rgb(8,48,107)'
color_comp = 'rgb(66,146,198)'

# Initialize App
# -----------------------------
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server

# Create controls
# ---------------------
# own controls for Bali_Covid Dash-App
regency_options = [
    {'label': str(REGENCIES[x]), 'value': str(REGENCIES[x])} for x in REGENCIES
]

# Create global chart template
# -----------------------------
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=114, lat=-8.54),
        zoom=7,
    ),
)

#######################
# Create app layout
#######################
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),

        # Header Component
        # ------------------------------
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("Barong-Mask.png"),
                            id="plotly-image",
                            style={
                                "height": "90px",
                                "width": "auto", },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2("Bali", style={
                                        "margin-bottom": "0px"},),
                                html.H6("DailyCovid Numbers on District-Level",
                                        style={"margin-top": "0px"}),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                # html.Div(
                #     [
                #         html.Img(
                #             src=app.get_asset_url("Barong-Mask.png"),
                #             id="header-image",
                #             style={
                #                 "height": "90px",
                #                 "width": "auto", },
                #         ),
                #     ],
                #     className="one column",
                #     id="header-image2",
                # ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "10px"},
        ),

        # #############################################
        # Row with Selector and 2-rows on right side
        # ##############################################
        html.Div(
            [
                # Left Side Control Panel
                # #######################
                html.Div(
                    [
                        html.P("Chooose a Region:", className='control_label'),
                        dcc.RadioItems(
                            id='region_selector',
                            options=[
                                {'label': 'Indonesia', 'value': 'indo'},
                                {'label': 'Bali', 'value': 'bali'},
                            ],
                            labelStyle={"display": "inline-block"},
                            value="bali",
                            className="dcc_control",),

                        html.Div(
                            [
                                html.P("Regency/County:",className="control_label info_text"),
                                dcc.Dropdown(
                                    id="regency_selector",
                                    options=regency_options,
                                    multi=False,
                                    value='',
                                    className="dcc_control info_text",
                                ),
                            ],
                            id="regency_selector_div",
                            # className= "dcc_control" ,
                        ),

                        html.P("Compare data with:", className='control_label'),
                        dcc.Dropdown(
                            id='compare_with',
                            options=[
                                {'label': 'World', 'value': 'World'},
                                {'label': 'Indonesia', 'value': 'Indonesia'},
                                {'label': 'Australia', 'value': 'Australia'},
                                {'label': 'Germany', 'value': 'Germany'},
                                {'label': 'United Kingdom','value': 'United Kingdom'},
                                {'label': 'Italy', 'value': 'Italy'},
                            ],
                            multi=False,
                            value='Germany',
                            clearable=False,
                            className='dcc_control info_text'
                        ),
                    ],
                    className="pretty_container two columns"
                ),

                # Right Side
                # #######################
                html.Div(
                    [
                        # Info Boxes 1
                        ###############
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(id="info_box_paragraph",className='info_text' ),
                                        html.H6(
                                            id="info_box",
                                            className='info_text'),
                                        html.H6(
                                            id="info_box2",
                                            className='info_text'),
                                    ],
                                    id="info_box1",
                                    className="pretty_container",
                                ),
                                # Triple Container
                                ##############
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.P("Case Fatality Rate",
                                                style={'text-align': 'center'}),
                                                html.H6(
                                                    id="cases_mortality",
                                                    style={'text-align': 'center'}),
                                                html.H6(
                                                    id="compare_cases_mortality",
                                                    style={'text-align': 'center'}),
                                            ],
                                            id="cfr",
                                            className="pretty_container",
                                        ),
                                        html.Div(
                                            [
                                                html.P("cases per 100k", style={
                                                    'text-align': 'center'}),
                                                html.H6(id="cases_per_100k", style={
                                                    'text-align': 'center'}),
                                                html.H6(id="compare_cases_per_100k",
                                                        style={'text-align': 'center'})
                                            ],
                                            id="cp100k",
                                            className="pretty_container",
                                        ),
                                        html.Div(
                                            [
                                                html.P("deaths per 100k", style={
                                                    'text-align': 'center'}),
                                                html.H6(id="deaths_per_100k", style={
                                                    'text-align': 'center'}),
                                                html.H6(id="compare_deaths_per_100k", style={
                                                    'text-align': 'center'}),
                                            ],
                                            id="dp100k",
                                            className="pretty_container",
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "Growth-Rate", style={'text-align': 'center'}),
                                                html.H6(id="growth_rate", style={
                                                    'text-align': 'center'}),
                                                html.H6(id="compare_growth_rate", style={
                                                        'text-align': 'center'}),
                                            ],
                                            id="g_rate",
                                            className="pretty_container",
                                        ),
                                    ],
                                    id="tripleContainer",
                                )
                            ],
                            id="infoContainer",
                            className="row"
                        ),
                        # Graph Time Series right Side
                        ##############
                        html.Div(
                            [
                                dcc.Graph(
                                    id='count_graph',
                                )
                            ],
                            id="countGraphContainer",
                            style={"minHeight": "50vh"},
                            className="pretty_container"
                        )
                    ],
                    id="rightCol",
                    className="ten columns"
                )
            ],
            className="row"
        ),

        # Control Bar 2
        # --------------------
        html.Div([
            html.Div([
                html.Div([
                    html.P("Cases:", className='control_label'),
                    dcc.RadioItems(
                        id='case_type_selector',
                        options=[
                            {'label': 'Confirmed', 'value': 'total_cases_per_100k'},
                            {'label': 'Recovered', 'value': 'total_recovered'},
                            {'label': 'Deaths', 'value': 'total_deaths_per_100k'},
                        ],
                        labelStyle={"display": "inline-block"},
                        value="total_cases_per_100k",
                        className="dcc_control",),
                ],),
            ],
                className='pretty_container thirteen columns',
                style={'display': 'inline-block'},
            )
        ],
            id='',
            className="row flex-display",
        ),

        # Choropleth Map and Comparison of Region
        # --------------------
        html.Div(
            [
                html.Div(
                    [dcc.Graph(
                        id="main_graph",
                        style={'max-width': '100%',
                               'max-height': '100%'
                               },
                    )],
                    className="pretty_container eight columns",
                ),
                html.Div(
                    [dcc.Graph(id="regency_info_graph")],
                    id="regency_info_div",
                    style={'max-width': '100%', 'max-height': '100%'},
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        # --------------------
        # Vaccination Graph Component
        # --------------------
        html.Div([
            html.Div(
                [dcc.Graph(id="vacc_graph")],
                id="countGraphContainer2",
                style={"minHeight": "70vh"},
                className="pretty_container nine columns",
            ),
            html.Div(
                [
                    html.Div(
                        html.Img(
                            src=app.get_asset_url('pic1.jpg'),
                            style={
                                'max-width': '100%',
                                'max-height': '100%',
                                #    'background-size': 'cover',
                            }))
                ],
                className="pretty_container four columns",
            ),
        ],
            id="graph-container",
            className="row flex-display",
        ),
        # Footer Component
        # ------------------------------
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("Barong-Mask.png"),
                            id="mage",
                            style={
                                "height": "80px",
                                "width": "auto", },
                        )
                    ],
                    className="one column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6("Sources", style={
                                        "margin-bottom": "0px"},),
                                html.P(["Code : https://github.com/Svensone/bali-covid-app"],
                                       style={"margin-top": "5px", "margin-left": "20px"}),
                                html.P([
                                    "Bali: https://infocorona.baliprov.go.id/",
                                    html.Br(),
                                    "Indonesia: https://www.kaggle.com/hendratno/covid19-indonesia",
                                    html.Br(),
                                    "World: ",
                                ],
                                    style={"margin-top": "5px", "margin-left": "20px"}),
                            ]
                        )
                    ],
                    className="ten column",
                    style={"margin-left": "20px"},
                    id="footer-des",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("About Me", id="learn-more-button"),
                            href="https://portfolio-sven.netlify.app/", target='_blank',
                        ),
                    ],
                    className="one column",
                ),
            ],
            id="footer",
            className="row flex-display",
            style={"margin-bottom": "10px"},
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)
##################
# Create callbacks
###################
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)

#######################################
# Region Selector -> show Regency Option
#######################################
@app.callback(
    Output(component_id='regency_selector_div', component_property='style'),
    Input('region_selector', 'value')
)
def show_regency_selector(region):
    if region == 'bali':
        return {'display': 'inline-block'}  # , 'flex-direction': 'row'
    if region == 'indo':
        return {'display': 'none'}


#######################################
# Selector -> Mini-Container Numbers
######################################
@app.callback(
    [
        Output("info_box_paragraph", "children"),
        Output("info_box", "children"),
        Output("cases_mortality", "children"),
        Output('cases_per_100k', 'children'),
        Output('deaths_per_100k', 'children'),
        Output('growth_rate', 'children'),
        # ouputs for Comparison row
        Output("info_box2", "children"),
        Output("compare_cases_mortality", "children"),
        Output('compare_cases_per_100k', 'children'),
        Output('compare_deaths_per_100k', 'children'),
        Output('compare_growth_rate', 'children'),
    ],
    [Input('regency_selector', 'value'),
     Input('region_selector', 'value'),
     Input('compare_with', 'value'),
     ],
)
def update_mini_containers1(regency, region, compare_with):
    print(regency + " infocontainer")
    # print(region)
    # first row info containers
    ############################
    if region == 'indo':
        df = pd.read_csv(data_world)
        selected_region = df[df['location'].str.match('Indonesia')]
        region_select = 'Indonesia'

    elif region == 'bali' and regency == '' or regency == None:
        df = pd.read_csv(data_covid_indo)
        selected_region = df[df['Province'].str.match('Bali')]
        region_select = "Bali"
    else:
        df = pd.read_csv(data_covid_bali)
        selected_region = df[df['Name_EN'].str.match((regency.capitalize()))]
        region_select = 'Bali ' + regency

    date = selected_region["Date"].iloc[-1]
    cfr = selected_region['CFR'].iloc[-1]
    # cfr = cfr.apply(pd.to_numeric)  # .round(2)
    cp100k = selected_region['total_cases_per_100k'].iloc[-1]  # .round(2)
    dp100k = selected_region['total_deaths_per_100k'].iloc[-1]  # .round()
    selected_region['growth_rate_new_cases'] = selected_region.loc[:,['new_cases']].pct_change(
        fill_method='ffill', periods=7)

    growth_rate = selected_region.loc[:, ('growth_rate_new_cases')].iloc[-1].round()

    # second row info containers
    ############################
    df2 = pd.read_csv(data_world)
    selected_region2 = df2[df2['location'].str.match(str(compare_with))]
    date2 = selected_region2["Date"].iloc[-1]
    cfr2 = selected_region2['CFR'].iloc[-1]
    cp100k2 = selected_region2['total_cases_per_100k'].iloc[-1].round(2)
    dp100k2 = selected_region2['total_deaths_per_100k'].iloc[-1].round(2)
    selected_region2['growth_rate_new_cases'] = selected_region2.loc[:,['new_cases']].pct_change(
        fill_method='ffill', periods=7)
    growth_rate2 = selected_region2['growth_rate_new_cases'].iloc[-1].round(2)
    return (
        '{}'.format(str(date)),
        '{}'.format(region_select),
        '{}'.format(str(round(cfr, 2))),
        '{}'.format(str(round(cp100k, 2))),
        '{}'.format(round(dp100k, 0)),
        '{}'.format(str(growth_rate) + '%'),
        '{}'.format(str(compare_with)),
        '{}'.format(str(round(cfr2, 2))),
        '{}'.format(str(round(cp100k2, 2))),
        '{}'.format(str(round(dp100k2, 2))),
        '{}'.format(str(growth_rate2) + '%')
    )

##################################
# Selectors -> time series graph (1.st Graph)
###################################
@app.callback(
    Output("count_graph", "figure"),
    [
        Input('region_selector', 'value'),
        Input('regency_selector', 'value'),
        Input('compare_with', 'value'),
    ])
def make_count_figure(region, regency, compare_region):
    print(region, regency, compare_region)
    if region == 'indo':
        df = pd.read_csv(data_world)   # use owid_world data
        df = df[df['location'].str.match('Indonesia')]
        region_selected = 'Indonesia'
    elif region == 'bali' and regency == '' or regency == None:
        region_selected = 'Bali'
        df = pd.read_csv(data_covid_indo)
        df = df[df['Province'].str.match(region_selected)]
    else:
        df = pd.read_csv(data_covid_bali)
        region_selected = str(regency)
        df = df[df['Name_EN'].str.match(region_selected)]

    df_test = df  # .tail(100)
    days = df_test.Date.to_list()
    df_compare = pd.read_csv(data_world)
    df_compare = df_compare[df_compare['location'].str.match(compare_region)]

    # Graph
    #####################
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    
    # colors = px.colors.sequential.Blues
    # print(colors)
    # ['rgb(247,251,255)', 'rgb(222,235,247)', 
    # 'rgb(198,219,239)', 'rgb(158,202,225)', 
    # 'rgb(107,174,214)', 'rgb(66,146,198)', 
    # 'rgb(33,113,181)', 
    # 'rgb(8,81,156)', 'rgb(8,48,107)']
    
       ## Bar Plot
       ###############
    selected_cases = ['new_cases_per_mil'] #add 'new_deaths' , 'new_recovered' ?
    for selected in selected_cases:
            name_bar = [region_selected, compare_region] #compare_region,
            fig.add_trace(
                go.Bar(
                    x=days,
                    y=df[selected],
                    marker_color= color1,
                    name = (name_bar[0] +" "+ selected),
                ),
                secondary_y=False,
            ),
            fig.add_trace(
                go.Bar(
                    x=days,
                    y=df_compare['new_cases_per_million'],
                    marker_color= color_comp,
                    name = (name_bar[1] +": cases per million"),
                ),
                secondary_y=False,
            ),

        ### Line Chart
        ###############
    selected_new = [ 'CFR', ] # growth_rate_new_cases
    for selected in selected_new:
        fig.add_trace(
            go.Scatter(
                x=days,
                y=df_test[selected],
                # mode='lines',
                name= selected,
                line=dict(color= color1, width=2),
            ),
            secondary_y=True
        )
        fig.add_trace(
            go.Scatter(
                x=days,
                y=df_compare['CFR'],
                # mode='lines',
                name= selected,
                line=dict(color= color_comp, width=2),
            ),
            secondary_y=True
        )

    fig.update_layout(
        xaxis_tickfont_size=8,
        yaxis=dict(
            tickfont_size=8,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )
    # Set x-axis title
    fig.update_yaxes(tickfont_size=8, secondary_y=True)
    return fig

##################################
# Selectors -> choropleth graph
###################################
@app.callback(
    Output("main_graph", "figure"),
    [Input('region_selector', 'value'),
     Input('case_type_selector', 'value')],
    [State("main_graph", "relayoutData")],
)
def make_main_figure(region, case_type, main_graph_layout, ):
    PATH = pathlib.Path(__file__).parent
    if region == 'bali':
        df = pd.read_csv(data_covid_bali)
        geojson = json.load(open(geojson_bali))
        center = {"lat": -8.5002, "lon": 115.0129}
        zoom = 7
    elif region == 'indo':
        df = pd.read_csv(data_covid_indo)
        geojson = json.load(open(geojson_indo))
        center = {'lat': 0, 'lon': 109}
        zoom = 3
    else:
        df = pd.read_csv(data_covid_germany)
        geojson = json.load(open(geojson_germany))
        center = {"lat": 48.5002, "lon": 9.0129}
        zoom = 7

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations='id',
        color=case_type,
        mapbox_style='carto-positron',
        hover_name='Name_EN',
        hover_data=['CFR', "new_cases", "new_deaths",
                    "growth_rate_new_cases", "Date"],
        # animation_frame="Date",
        color_continuous_scale='blues',
        zoom=zoom,
        center=center,
        opacity=0.5,
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        )
    display_fig = go.Figure(fig)

    # relayoutData is None by default, and {'autosize': True} without relayout action
    if main_graph_layout is not None:
        if "mapbox.center" in main_graph_layout.keys():
            lon = float(main_graph_layout["mapbox.center"]["lon"])
            lat = float(main_graph_layout["mapbox.center"]["lat"])
            zoom = float(main_graph_layout["mapbox.zoom"])
            layout["mapbox"]["center"]["lon"] = lon
            layout["mapbox"]["center"]["lat"] = lat
            layout["mapbox"]["zoom"] = zoom

    # figure = dict(data=traces, layout=layout)
    return display_fig


#########################
# Selectors  -> regency_info_bar Charts
#########################
@app.callback(
    Output('regency_info_graph', 'figure'),
    [
        Input('region_selector', 'value'),
        Input('case_type_selector', 'value'), ]
)
def make_regency_info_fig(region, case_type):
    if region == 'indo':
        df = pd.read_csv(data_covid_indo)
        region_selected = 'Indonesia'
    elif region == 'bali':
        df = pd.read_csv(data_covid_bali)
        region_selected = 'bali'
    if case_type == "total_cases_per_100k":
        c_type = ['new_cases']
    elif case_type == 'total_deaths_per_100k':
        c_type = ['new_deaths']
    else:
        c_type = ['new_recovered']
    # get latest date
    # display per regency, new daily cases (Bar) and cases7 (Line)
    df_latest = df.sort_values(by=['Date'], ascending=False).head(10)
    regions = df_latest['Name_EN'].to_list()

    # Make Graph
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=regions,
            y=df_latest[c_type[0]],
            name=c_type[0],
            marker_color= color1
        ))
    
    fig.update_layout(
        # title='{}'.format(df_latest['Date'].iloc(1)),
        xaxis_tickfont_size=6,
        yaxis=dict(
            tickfont_size=6,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )
    # Set x-axis title
    # fig.update_yaxes(tickfont_size=6, secondary_y=True)
    return fig

##################################
# Selectors -> Vaccination graph
###################################
@app.callback(
    Output("vacc_graph", "figure"),
    Input('compare_with', 'value')
)
def make_vacc_graph(compare_with):
    print(compare_with)

    df = pd.read_csv(data_world)
    df_compare = df[df['location'].str.match(str(compare_with))].iloc[-100:]
    df_indo = df[df['location'].str.match(str("Indonesia"))].iloc[-100:]

    if compare_with == "Indonesia":
        dfs = [df_indo]
    else:
        dfs = [df_indo, df_compare]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = [color1, color_comp]
    names = ["Indonesia", compare_with]

    for index, data in enumerate(dfs):
        days = df_indo.Date.to_list()
        fig.add_trace(go.Bar(
            x=days,
            y=data['new_vaccinations_smoothed_per_million'],
            marker_color=colors[index],
            name=str(names[index] + ': new vacc. p.million')
        ),
            secondary_y=False,)
        fig.add_trace(go.Scatter(
            x=days,
            y=data['people_fully_vaccinated_per_hundred'],
            marker_color=colors[index],
            name=(names[index] + ': fully vacc. p.mil. in %')
        ),
            secondary_y=True)

    fig.update_layout(
        title= 'Vaccinations',
        xaxis_tickfont_size=8,
        yaxis=dict(
            tickfont_size=8,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )

    # Set x-axis title
    fig.update_yaxes(tickfont_size=8, secondary_y=True)

    return fig


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
