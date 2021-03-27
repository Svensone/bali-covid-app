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

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html

# Multi-dropdown options
from controls import REGENCIES
import controls


# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

# ------------------------------------------------------------------------------
# 1. Data
# ------------------------------------------------------------------------------

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
# Create app layout
# -----------------------------
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
                                "height": "80px",
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
                                # html.H6("Data per Regency",
                                #         style={"margin-top": "0px"}),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("frangi.png"),
                            id="header-image",
                            style={
                                "height": "90px",
                                "width": "auto", },
                        ),
                    ],
                    className="one column",
                    id="header-image2",
                ),
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
                                html.P("Regency/County:",
                                       className="control_label"
                                       ),
                                dcc.Dropdown(
                                    id="regency_selector",
                                    options=regency_options,
                                    multi=False,
                                    value='',
                                    className="dcc_control",
                                ),
                            ],
                            id="regency_selector_div",
                            # className= "dcc_control" ,
                        ),
                        html.P("Compare data with:",
                               className='control_label'),
                        dcc.Dropdown(
                            id='compare_with',
                            options=[
                                {'label': 'World', 'value': 'World'},
                                {'label': 'Indonesia', 'value': 'Indonesia'},
                                {'label': 'Australia', 'value': 'Australia'},
                                {'label': 'Germany', 'value': 'Germany'},
                                {'label': 'United Kingdom',
                                    'value': 'United Kingdom'},
                                {'label': 'Italy', 'value': 'Italy'},
                            ],
                            multi=False,
                            value='',
                            className='dcc_control'
                        ),
                    ],
                    className="pretty_container two columns"
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(id="info_box_paragraph",
                                               ),
                                        html.H6(
                                            id="info_box",
                                            className='info_text'),
                                    ],
                                    id="info_box1",
                                    className="pretty_container",
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.P("Case Fatality Rate",
                                                       style={'text-align': 'center'}),
                                                html.H6(
                                                    id="cases_mortality",
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
                                                    'text-align': 'center'})
                                            ],

                                            id="gas",
                                            className="pretty_container",
                                        ),
                                        html.Div(
                                            [
                                                html.P("deaths per 100k", style={
                                                    'text-align': 'center'}),
                                                html.H6(id="deaths_per_100k", style={
                                                    'text-align': 'center'}),
                                            ],
                                            id="oil",
                                            className="pretty_container",
                                        ),
                                        html.Div(
                                            [
                                                html.P("Growth-Rate",
                                                       style={'text-align': 'center'}),
                                                html.H6(id="growth_rate", style={
                                                    'text-align': 'center'}),
                                            ],
                                            id="water",
                                            className="pretty_container",
                                        ),
                                    ],
                                    id="tripleContainer",
                                )

                            ],
                            id="infoContainer",
                            className="row"
                        ),
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

        # # Controls Panel Component
        # # ------------------------------

        #         html.P('NOT YET !!', className="control_label",),
        #         html.P("Date or Timerange:",
        #                className="control_label",
        #                ),
        #         dcc.RangeSlider(
        #             id="year_slider",
        #             min=1960,
        #             max=2017,
        #             value=[1990, 2010],
        #             className="dcc_control",
        #         ),

        # Mini Container Row 2
        # -----------------------
        html.Div(
            [
                html.Div(
                    [html.H6(
                        id="compare_info_box",
                        style={'text-align': 'center'}),
                     ],
                    id="compare_info_box1",
                    className="mini_container",
                ),
                html.Div(
                    [
                        html.H6(
                            id="compare_cases_mortality",
                            style={'text-align': 'center'}),
                    ],
                    id="compare_cases_mortality1",
                    className="mini_container",
                ),
                html.Div(
                    [
                        html.H6(id="compare_cases_per_100k", style={
                            'text-align': 'center'})
                    ],
                    id="compare_cases_per_100k1",
                    className="mini_container",
                ),
                html.Div(
                    [
                        html.H6(id="compare_deaths_per_100k", style={
                            'text-align': 'center'}),
                    ],
                    id="compare_deaths_per_100k1",
                    className="mini_container",
                ),
                html.Div(
                    [
                        html.H6(id="compare_growth_rate", style={
                            'text-align': 'center'}),
                    ],
                    id="compare_growth_rate1",  # originally id='water' -> change in .css file
                    className="mini_container",
                ),
                # html.Div(
                #     [
                #         html.P("Fun_Facts", style={'text-align': 'center'}),

                #         html.P("Male Smokers", style={'text_align': 'left'}),
                #         html.H6(id="compare_male_smokers",
                #                 style={'text-align': 'center'}),
                #         html.P("Stringency Index", style={
                #                'text_align': 'left'}),
                #         html.H6(id="compare_stringency_index",
                #                 style={'text-align': 'center'}),
                #         html.P("Median Age", style={'text_align': 'left'}),
                #         html.H6(id="compare_median_age", style={
                #                 'text-align': 'center'}),
                #         # Fun data: ‘Male_smokers’, hospital_beths_per_thousands, median_age, stringency_index, people_fully_vaccinated
                #         # Positivity_rate, test_per_cases

                #     ],
                #     id="compare_fun_facts1",
                #     className="mini_container",
                # ),
            ],
            id="info-container1",
            className="row container-display thirteen columns",
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
        
        # Vaccination Graph Component
        # --------------------
        html.Div([
            html.Div(
                [dcc.Graph(id="count_graph2")],
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
            # className="row container-display",
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
                                html.P(["Bali: https://infocorona.baliprov.go.id/", html.Br(), "Indonesia: https://www.kaggle.com/hendratno/covid19-indonesia"],
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

# Create callbacks
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
        Output('growth_rate', 'children')
    ],

    [Input('regency_selector', 'value'),
     Input('region_selector', 'value')],

)
def update_mini_containers1(regency, region):
    print(regency + " infocontainer")
    # print(region)
    if region == 'indo':
        df = pd.read_csv(data_world)
        selected_region = df[df['location'].str.match('Indonesia')]
        region_select = 'Indonesia'

    elif region == 'bali' and regency == '' or regency == None:
        df = pd.read_csv(data_covid_indo)
        selected_region = df[df['Name_EN'].str.match('bali')]
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
    selected_region['growth_rate_new_cases'] = selected_region['new_cases'].pct_change(
        fill_method='ffill', periods=7)

    growth_rate = selected_region.loc[:,
                                      ('growth_rate_new_cases')].iloc[-1].round()
    return '{}'.format(str(date)), '{}'.format(region_select), '{}'.format(str(round(cfr, 2))), '{}'.format(str(round(cp100k, 2))), '{}'.format(round(dp100k, 0)), '{}'.format(str(growth_rate) + '%')

#######################################
# Selector -> Mini-Container Comparison
#######################################
# only visible if selected


@app.callback(
    Output(component_id='info-container1', component_property='style'),
    Input('compare_with', 'value')
)
def show_regency_selector(compare_with):
    if compare_with == '' or compare_with == None:
        return {'display': 'none'}
    else:
        return {'display': 'flex', 'flex-direction': 'row'}


@app.callback(
    [Output("compare_info_box", "children"),
        Output("compare_cases_mortality", "children"),
        Output('compare_cases_per_100k', 'children'),
        Output('compare_deaths_per_100k', 'children'),
        Output('compare_growth_rate', 'children'),
        # Output('compare_male_smokers', 'children'),
        # Output('compare_stringency_index', 'children'),
        # Output('compare_median_age', 'children'),
     ],
    [
        Input('compare_with', 'value'),
    ],
)
def update_mini_containers1(compare_with):
    # print(compare_with)
    df = pd.read_csv(data_world)
    selected_region = df[df['location'].str.match(compare_with)]

    date = selected_region["Date"].iloc[-1]
    cfr = selected_region['CFR'].iloc[-1]
    # cfr = cfr.apply(pd.to_numeric)  # .round(2)
    cp100k = selected_region['total_cases_per_100k'].iloc[-1].round(2)
    dp100k = selected_region['total_deaths_per_100k'].iloc[-1].round(2)
    selected_region['growth_rate_new_cases'] = selected_region['new_cases'].pct_change(
        fill_method='ffill', periods=7)
    growth_rate = selected_region['growth_rate_new_cases'].iloc[-1].round(2)

    median_age = selected_region['median_age'].iloc[-1]
    stringency = selected_region['stringency_index'].iloc[-1]
    male_smokers = selected_region['male_smokers'].iloc[-1]

    # , '{}'.format(str(male_smokers)), '{}'.format(str(stringency)), '{}'.format(str(median_age))
    return '{} {}'.format(str(date), compare_with), '{}'.format(str(round(cfr, 2))), '{}'.format(str(round(cp100k, 2))),    '{}'.format(str(round(dp100k, 2))),    '{}'.format(str(growth_rate) + '%')
##################################
# Selectors -> time series graph
###################################


@app.callback(
    Output("count_graph", "figure"),
    [Input('region_selector', 'value'), Input(
        'regency_selector', 'value')],)
def make_count_figure(region, regency):
    print(region)
    print(regency)

    if region == 'indo':
        df = pd.read_csv(data_covid_indo)
        region_selected = 'indonesia'
    elif region == 'bali' and regency == '' or regency == None:
        df = pd.read_csv(data_covid_indo)
        region_selected = 'bali'
    else:
        df = pd.read_csv(data_covid_bali)
        region_selected = str(regency)

    df = df[df['Name_EN'].str.match(region_selected)]

    df_test = df  # .tail(100)
    days = df_test.Date.to_list()

    # fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    selected_cases = ['new_cases', 'new_recovered']
    colors = px.colors.sequential.Blues
    count = 0
    for selected in selected_cases:
        count += 2
        fig.add_trace(
            go.Bar(
                x=days,
                y=df_test[selected],
                name=selected,
                marker_color=colors[count],
            ),
            secondary_y=False,
        )
    # test plots for new cases and
    count = 0
    selected_new = ['total_deaths_per_100k', 'CFR', ]
    for selected in selected_new:
        count += 2
        fig.add_trace(
            go.Scatter(
                x=days,
                y=df_test[selected],
                # mode='lines',
                name=selected,
                line=dict(color=colors[count], width=2),
            ),
            secondary_y=True

        )

    fig.update_layout(
        title={
            'text': 'Daily Cases in {}'.format(region_selected),
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_tickfont_size=6,
        yaxis=dict(
            tickfont_size=6,
        ),
        plot_bgcolor=colors[0],
        paper_bgcolor=colors[0],
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='white',
            bordercolor='white',
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )

    # Set x-axis title
    fig.update_yaxes(tickfont_size=6, secondary_y=True)

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
    # print(region)
    # print(case_type)
    # print(main_graph_layout)

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
        hover_data=['CFR', "new_cases", "new_deaths", "growth_rate_new_cases"],
        # animation_frame="Date",
        color_continuous_scale='blues',
        zoom=zoom,
        center=center,
        opacity=0.5,
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
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

# Selectors  -> regency_info_bar Charts


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
    colors = px.colors.sequential.Blues

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=regions,
            y=df_latest[c_type[0]],
            name=c_type[0],
            marker_color=colors[4]
        ))
        ## Compare or Add different Metric 
        ###################################
    # fig.add_trace(
    #     go.Bar(
    #         x=regions,
    #         y=df_latest[c_type[1]],
    #         name=c_type[1],
    #         marker_color=colors[6]
    #     ))

    fig.update_layout(
        # title='{}'.format(df_latest['Date'].iloc(1)),
        xaxis_tickfont_size=6,
        yaxis=dict(
            tickfont_size=6,
        ),
        plot_bgcolor=colors[0],
        paper_bgcolor=colors[1],
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='white',
            bordercolor='white',
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )

    # Set x-axis title
    # fig.update_yaxes(tickfont_size=6, secondary_y=True)

    return fig


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
