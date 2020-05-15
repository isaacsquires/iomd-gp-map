import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
from mapping import make_map, read_in_data, LA_to_LSOA, LSOA_to_IoMD, gp_surgeries_from_LA, gp_surgeries_from_LSOA, gp_coords_from_LA, filter_LSOAs_by_decile
import pandas as pd
import numpy as np
import plotly.express as px
import os
import dash_bootstrap_components as dbc

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = [dbc.themes.DARKLY]
port = int(os.environ.get("PORT", 5000))

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Index of Multiple Deprivation and GP Surgery Mapping Tool'
server = app.server

print('READING IN SHAPEFILE DATA...')
LA_data, LA_df = read_in_data('LA')
_, iomd_df = read_in_data('IoMD')
LSOA_data, _ = read_in_data('LSOA')
LA_list = LA_data['lad17nm']
iomd_decile_list = np.append(np.unique(iomd_df['imd_decile']), 'None')
datasets = ['IoMD Decile','IoMD Rank', 'LSOA']
surgery_df_empty, missing_postcodes = gp_coords_from_LA('A')

def placeholder_map():
    england_lat = 53
    england_lon = -3
    center = {'lat':england_lat, 'lon': england_lon}
    df_holder = pd.DataFrame({'lat':[england_lat], 'lon':[england_lon]})
    fig = px.scatter_mapbox(data_frame=df_holder, lat='lat', lon='lon', mapbox_style = 'dark', center=center, opacity=0, zoom=5)
    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))
    return fig

app.layout = html.Div(children=[
    html.H1(children='Index of Multiple Deprivation and GP Surgery Mapping Tool', style = {'padding-bottom': '40px'}),
    dbc.Row(
            [
                dbc.Col(html.Div(children=[
                    html.H4(children='Choose a local authority from the dropdown or select on the map', style = {'padding-bottom': '40px'}),
                    dcc.Dropdown(
                    id='LA-dropdown',
                    options=[{'label': k, 'value': k} for k in LA_list],
                    value='LA',
                    ),
                    dcc.Graph(
                            id='main-map',
                            figure=make_map(LA_data, LA_df, 'color', show_scalebar=False),
                            style = {'padding-top': '70px'}
                        ),
                        ]),),

                dbc.Col(html.Div(children=[
                    html.H4(children='Select a dataset'),
                    dcc.RadioItems(
                    id='dataset-radio',
                    options=[{'label': k, 'value': k} for k in datasets],
                    value='IoMD Decile',
                    labelStyle={'display': 'inline-block', 'padding':'5px'},
                    style = {'padding-top': '10px'}
                        ),
                    html.H4(children='Show GP surgery points'),
                    dcc.RadioItems(
                                    id='surgery-radio',
                                    options=[{'label': 'on', 'value': 'on'}, {'label': 'off', 'value': 'off'}],
                                    value='on',
                                    style = {'padding-top': '10px'},
                                    labelStyle={'display': 'inline-block', 'padding':'5px'},
                                ),
                    dcc.Graph(
                        id='second-map',
                        figure=placeholder_map(),
                        style = {'padding-top': '10px', 'padding-bottom': '10px'},
                    ),
                    html.H4(children='Filter by deprivation decile'),
                        dcc.Dropdown(
                    id='iomd-dropdown',
                    options=[{'label': k, 'value': k} for k in iomd_decile_list],
                    value= 'None',
                    style = {'padding-bottom': '10px'},
                ),
                    dcc.Textarea(
                                id='textarea-second-map',
                                value='Select a GP surgery on the map for more info',
                                style={'width': '100%'},
                            ),
                ]),
                ),
            ]
        ),

    
#     html.H4(children='Table of GP surgeries in the selected local authority'),
#     dash_table.DataTable(
#                             id='gp-datatable',
#                             columns=[{"name": i, "id": i} for i in surgery_df_empty.columns],
#                             data=surgery_df_empty.to_dict('records'),
# ),
                
])

# LA Callback

@app.callback(
    Output('second-map', 'figure'),
    [Input('dataset-radio', 'value'),Input('LA-dropdown', 'value'), Input('surgery-radio', 'value'), Input('iomd-dropdown', 'value'),])
def update_map(dataset, selected_LA, surgery_switch, iomd_decile):
    if surgery_switch == 'on':
        print('Switching on GP Surgery Points')
        surgery_data, missing_postcodes = gp_coords_from_LA(selected_LA)
        print(missing_postcodes)
    elif surgery_switch == 'off':
        print('Switching off GP Surgery Points')
        surgery_data = None
    
    if dataset == 'IoMD Decile':
        iomd_decile = None if iomd_decile == 'None' else iomd_decile
        if iomd_decile is not None:
            iomd_decile = int(iomd_decile)
            
            selected_LSOA_data, selected_iomd_df = filter_LSOAs_by_decile(selected_LA, LSOA_data, iomd_df, iomd_decile)
        else:
            selected_LSOA_data, selected_LSOA_df = LA_to_LSOA(selected_LA, LSOA_data)
            selected_iomd_df = LSOA_to_IoMD(selected_LSOA_data, iomd_df)
        fig = make_map(selected_LSOA_data, selected_iomd_df, 'imd_decile', LA_name=selected_LA, LA_data=LA_data, surgery_data=surgery_data)

    elif dataset == 'IoMD Rank':
        selected_LSOA_data, selected_LSOA_df = LA_to_LSOA(selected_LA, LSOA_data)
        selected_iomd_df = LSOA_to_IoMD(selected_LSOA_data, iomd_df)
        fig = make_map(selected_LSOA_data, selected_iomd_df, 'imd_rank', LA_name=selected_LA, LA_data=LA_data, surgery_data=surgery_data)

    elif dataset == 'LSOA':
        selected_LSOA_data, selected_LSOA_df = LA_to_LSOA(selected_LA, LSOA_data)
        fig = make_map(selected_LSOA_data, selected_LSOA_df, 'color', LA_name=selected_LA, LA_data=LA_data, surgery_data=surgery_data)

    else:
        selected_LSOA_data, selected_LSOA_df = LA_to_LSOA(selected_LA, LSOA_data)
        fig = make_map(selected_LSOA_data, selected_LSOA_df, 'color', LA_name=selected_LA, LA_data=LA_data, surgery_data=surgery_data)

    return fig

@app.callback(
    Output('LA-dropdown', 'value'),
    [Input('main-map', 'clickData')]) 
def display_click_data(clickData):
    selected_LA = clickData['points'][0]['hovertext']
    return selected_LA

@app.callback(
    Output('textarea-second-map', 'value'),
    [Input('second-map', 'clickData')]) 
def display_click_data(clickData):
    return_data = 'Surgery name: '+str(clickData['points'][0]['customdata'][0])+'\n'+'PCN: '\
                    +str(clickData['points'][0]['customdata'][2])+'\n'+'Phone number: '\
                        +str(clickData['points'][0]['customdata'][3])+'\n'+'Postcode: '\
                        +str(clickData['points'][0]['customdata'][1])
    return return_data

if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=port)