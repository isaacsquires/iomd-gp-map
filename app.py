import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
from mapping import make_map, read_in_data, LA_to_LSOA, LSOA_to_IoMD, gp_surgeries_from_LA, gp_surgeries_from_LSOA, gp_coords_from_LA, filter_LSOAs_by_decile
import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

print('READING IN SHAPEFILE DATA...')
LA_data, LA_df = read_in_data('LA')
_, iomd_df = read_in_data('IoMD')
LSOA_data, _ = read_in_data('LSOA')
LA_list = LA_data['lad17nm']
iomd_decile_list = np.append(np.unique(iomd_df['imd_decile']), 'None')
datasets = ['IoMD Decile','IoMD Rank', 'LSOA']
surgery_df_empty, missing_postcodes = gp_coords_from_LA('A')

app.layout = html.Div(children=[
    html.H1(children='Inverse Care Mapping Tool'),

    html.Div(children='''
        A map of the UK's PCN, GP surgeries and Index of Multiple Deprivation \n
        Select a local authority on the map or from the dropdown menu
    '''),

    dcc.Graph(
        id='main-map',
        figure=make_map(LA_data, LA_df, 'color')
    ),
    html.H2(children='Choose a LA from the dropdown'),
    dcc.Dropdown(
                    id='LA-dropdown',
                    options=[{'label': k, 'value': k} for k in LA_list],
                    value='LA'
                ),
    html.H2(children='Select a dataset'),
    dcc.RadioItems(
                    id='dataset-radio',
                    options=[{'label': k, 'value': k} for k in datasets],
                    value='LSOA'
                ),
    html.H2(children='Show GP surgery points'),
    dcc.RadioItems(
                    id='surgery-radio',
                    options=[{'label': 'on', 'value': 'on'}, {'label': 'off', 'value': 'off'}],
                    value='on'
                ),
    html.H2(children='Filter by deprivation decile'),
    dcc.Dropdown(
                    id='iomd-dropdown',
                    options=[{'label': k, 'value': k} for k in iomd_decile_list],
                    value= 'None'
                ),
    dcc.Graph(
        id='second-map',
        figure=make_map(LA_data, LA_df, 'color')
    ),
    html.H3(children='Table of GP surgeries in the selected local authority'),
    dash_table.DataTable(
                            id='gp-datatable',
                            columns=[{"name": i, "id": i} for i in surgery_df_empty.columns],
                            data=surgery_df_empty.to_dict('records'),
),
                
])

# LA Callback

@app.callback(
    [Output('second-map', 'figure'), Output('gp-datatable', 'data')],
    [Input('dataset-radio', 'value'),Input('LA-dropdown', 'value'), Input('surgery-radio', 'value'), Input('iomd-dropdown', 'value'),])
def update_map(dataset, selected_LA, surgery_switch, iomd_decile):
    print(dataset, selected_LA)
    if surgery_switch == 'on':
        print('Switching on GP Surgery Points')
        surgery_data, missing_postcodes = gp_coords_from_LA(selected_LA)
        print(missing_postcodes)
    elif surgery_switch == 'off':
        print('Switching off GP Surgery Points')
        surgery_data = None
    
    if dataset == 'IoMD Decile':
        print(iomd_decile)
        print(type(iomd_decile))
        iomd_decile = None if iomd_decile == 'None' else iomd_decile
        print(iomd_decile)
        print(type(iomd_decile))
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

    return fig, surgery_data.to_dict('records')

@app.callback(
    Output('LA-dropdown', 'value'),
    [Input('main-map', 'clickData')]) 
def display_click_data(clickData):
    selected_LA = clickData['points'][0]['hovertext']
    print(selected_LA)
    return selected_LA

# @app.callback(
#     [Output('gp-datatable', 'data'),Output('gp-textarea', 'value')],
#     [Input('second-map', 'clickData')]) 
# def display_click_data(clickData):
#     print(clickData)
#     # selected_LA = clickData['points'][0]['hovertext']
#     # LSOA_code = clickData['points'][0]['location']
#     # gp_data = gp_surgeries_from_LSOA(LSOA_code)
#     # if gp_data.empty:
#     #     message = 'No GP surgeries in selected LSOA'
#     #     gp_df = gp_data.to_dict('records')
#     # else:
#     #     message = str(len(gp_data))+' GP surgeries found in LSOA'
#     #     gp_df = gp_data.to_dict('records')
#     return gp_df, message

if __name__ == '__main__':
    app.run_server(debug=True)