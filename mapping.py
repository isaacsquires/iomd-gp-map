from urllib.request import urlopen
import json
from dotenv import load_dotenv
import os
from os.path import join, dirname
dotenv_path = join('.env')
load_dotenv(dotenv_path)
import pandas as pd
import geopandas as gpd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import seaborn as sns

england_lat = 53
england_lon = -3

print('Reading in postcode lookup tables...')
postcode_lsoa_lookup = pd.read_pickle('data/postcode_lookup_reduced.pkl.zip')
print('Reading in lookup tables...')
lookup = pd.read_pickle('data/lookup_reduced.pkl.zip')
print('Reading in GP surgery data...')
surgery_data = pd.read_pickle('data/PCN_GP_data.pkl.zip')
surgery_data['PCN'] = surgery_data['PCN'].replace(np.nan,'unknown')
try:
    access_token = os.getenv("MAPBOX_ACCESS_TOKEN")
    px.set_mapbox_access_token(access_token)
except:
    print('No access token found')
    access_token = ''

def read_in_data(name):

    if name == 'LSOA':
        print('Reading in LSOA shapefile')
        LSOA_shp_filepath = 'zip://./data/LSOA_clipped_general.zip'
        LSOA_data = gpd.read_file(LSOA_shp_filepath)
        data = LSOA_data.to_crs('epsg:4326')
        df=None

    elif name == 'IoMD':
        print('Reading in IoMD shapefile')
        imd_df = pd.read_excel(io='data/IoMD.xlsx', sheet_name='IMD2019')
        imd_df = imd_df.rename(columns={'LSOA code (2011)':'code', 'Index of Multiple Deprivation (IMD) Rank': 'imd_rank',
                            'Index of Multiple Deprivation (IMD) Decile': 'imd_decile','LSOA name (2011)':'name'})
        df = imd_df.drop(columns=['Local Authority District code (2019)',
                            'Local Authority District name (2019)'])
        data = None
        df['hover_data'] = imd_df['imd_rank']

    
    elif name == 'LA':
        print('reading in LA shapefile')
        LA_shp_filepath = 'zip://./data/LAD_general.zip'
        LA_data = gpd.read_file(LA_shp_filepath)
        LA_data = LA_data.to_crs('epsg:4326')
        LA_data = LA_data.rename(columns={'lad17cd':'code'})
        data = LA_data[LA_data['lad17nm'].isin(lookup['LAD11NM'].unique())]
        lin_index = np.ones(len(LA_data))
        df = pd.DataFrame({'color':lin_index, 'code':LA_data['code'], 'name':LA_data['lad17nm'], 'hover_data':LA_data['lad17nm']})

    return data, df

def get_LA_centroid(LA_name, LA_data):
    geometry = LA_data[LA_data['lad17nm']==LA_name]['geometry'].values
    centroid = geometry.centroid
    try:
        for coord in centroid:
            lat = coord.y
            lon = coord.x
    except:
        lat = england_lat
        lon = england_lon
    return centroid, {'lat':lat, 'lon':lon}


def make_map(gpd_df, chloro_df, color, LA_name=None, LA_data=None, surgery_data=None, show_scalebar=True):
    print('Mapping start')
    if LA_name is None:
        center = {'lat': england_lat, 'lon': england_lon}
        zoom=5
    else:
        zoom=11
        centroid, center = get_LA_centroid(LA_name, LA_data)
    fig = px.choropleth_mapbox(chloro_df, geojson=gpd_df, color=color, locations='code', 
                    featureidkey='properties.code',hover_name='hover_data', center=center, zoom=zoom, color_continuous_scale=px.colors.sequential.PuBuGn[::-1])

    if surgery_data is not None:
        surgery_data['pcn'] = surgery_data['pcn'].replace(np.nan,'unknown')
        unique = np.unique(surgery_data['pcn'])
        color_array = np.zeros(len(surgery_data['pcn']))
        color_map = []
        color_palette = sns.color_palette("Paired_r", len(unique))
        for i, pcn in enumerate(unique):

            color_palette[i] = tuple([int(z * 256) for z in color_palette[i]])
            color_map.append([i/(len(unique)-1), 'rgb'+str(color_palette[i])])
            for j, surgery_pcn in enumerate(surgery_data['pcn']):
                if surgery_pcn == pcn:
                    color_array[j] = i/(len(unique)-1)
        surgery_data['color'] = color_array
        surgery_trace = px.scatter_mapbox(surgery_data, lat="lat", lon="lon", size='size', color='color', hover_name='hover_data',custom_data=['surgery_name','postcode', 'pcn', 'phone_number'], size_max=15)
        surgery_trace['data'][0]['marker']['coloraxis'] = 'coloraxis2'
        surgery_trace['data'][0]['marker']['opacity'] = 1.0
        fig.add_trace(surgery_trace['data'][0])
        tick_vals = [x[0] for x in color_map]
        fig.data[1]['hovertemplate'] = '<b>%{hovertext}</b><extra></extra>'
        fig['layout']['coloraxis2'] = {'showscale':True,
                                   'colorscale': color_map,
                                    'colorbar':{
                                        'x':1.15,
                                        'ticktext':unique,
                                        'tickvals':tick_vals,
                                    },}
    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5), mapbox_style="dark", clickmode='event+select', hovermode='closest')
    if show_scalebar is False:
        fig.update_layout(coloraxis_showscale=False)
    print('Mapping complete')
    return fig

def LA_to_LSOA(LSOA_name, LSOA_data):
    lookup_select = lookup[lookup['LAD11NM'] == LSOA_name]
    LSOA_list = lookup_select['LSOA11CD'].unique()
    selected_LSOA_data = LSOA_data[LSOA_data['code'].isin(LSOA_list)]
    lin_index = np.ones(len(selected_LSOA_data))
    selected_LSOA_df = pd.DataFrame({'color':lin_index, 'code':selected_LSOA_data['code'],'hover_data':selected_LSOA_data['name'], 'hover_data':selected_LSOA_data['name']})
    return selected_LSOA_data, selected_LSOA_df

def LSOA_to_IoMD(LSOA_df, IoMD_df):
    selected_IoMD_df = IoMD_df[IoMD_df['code'].isin(LSOA_df.code)]
    return selected_IoMD_df

def gp_surgeries_from_LSOA(LSOA_code):
    selected_postcode_lsoa_lookup = postcode_lsoa_lookup[postcode_lsoa_lookup['lsoa11cd']==LSOA_code]
    selected_surgery_data = surgery_data[surgery_data['postcode'].isin(selected_postcode_lsoa_lookup['pcd8'])]
    selected_surgery_data = pd.concat([selected_surgery_data,(surgery_data[surgery_data['postcode'].isin(selected_postcode_lsoa_lookup['pcd7'])])])
    selected_surgery_data = pd.concat([selected_surgery_data, (surgery_data[surgery_data['postcode'].isin(selected_postcode_lsoa_lookup['pcds'])])])
    selected_surgery_data = selected_surgery_data.drop_duplicates()
    return selected_surgery_data

def gp_surgeries_from_LA(LA_name):
    selected_postcode_lsoa_lookup = postcode_lsoa_lookup[postcode_lsoa_lookup['ladnm']==LA_name]
    selected_surgery_data = surgery_data[surgery_data['postcode'].isin(selected_postcode_lsoa_lookup['pcd8'])]
    selected_surgery_data = pd.concat([selected_surgery_data,(surgery_data[surgery_data['postcode'].isin(selected_postcode_lsoa_lookup['pcd7'])])])
    selected_surgery_data = pd.concat([selected_surgery_data,(surgery_data[surgery_data['postcode'].isin(selected_postcode_lsoa_lookup['pcds'])])])
    selected_surgery_data = selected_surgery_data.drop_duplicates()
    return selected_surgery_data

def gp_coords_from_LA(LA_name):
    size= 15
    selected_surgery_data = gp_surgeries_from_LA(LA_name)
    postcodes = {"postcodes":selected_surgery_data['postcode'].values[:].tolist()}
    missing_postcode_df = pd.DataFrame({'postcode':[]})
    request_url = 'http://api.getthedata.com/postcode/'
    gp_coord_df = pd.DataFrame({'lon':[],'lat':[],'postcode':[],'surgery_name':[],
                                   'pcn':[]})
    for postcode in postcodes['postcodes']:
        try:
            postcode = postcode.replace(" ", '')
            response = requests.get(request_url+postcode)
            res = response.json()
            selected_postcode = res['data']['postcode']
            surgery_data_temp = selected_surgery_data[selected_surgery_data['postcode']==selected_postcode]
            surgery_name = surgery_data_temp['surgery_name'].values[0]
            phone_number = surgery_data_temp['phone_number'].values[0]
            pcn = surgery_data_temp['PCN'].values[0]
            lon = float(res['data']['longitude'])
            lat = float(res['data']['latitude'])
            gp_coord_df_temp = pd.DataFrame({'lon':[lon],'lat':[lat],'size':size, 'postcode':selected_postcode, 
                                                'surgery_name': surgery_name,
                                                'pcn': pcn,'phone_number': phone_number, 'hover_data':str(surgery_name)+', '+str(pcn)})
            gp_coord_df = pd.concat([gp_coord_df,(gp_coord_df_temp)])
        except:
            missing_postcode_df_temp = pd.DataFrame({'postcode':[res['input']]})
            missing_postcode_df = pd.concat([missing_postcode_df,(missing_postcode_df_temp)])

    return gp_coord_df, missing_postcode_df

def filter_LSOAs_by_decile(LA_name, LSOA_data, iomd_df, decile):
    selected_LSOA_data, selected_LSOA_df = LA_to_LSOA(LA_name, LSOA_data)
    selected_iomd_df = iomd_df[iomd_df['code'].isin(selected_LSOA_data['code'])]
    selected_iomd_df = selected_iomd_df[selected_iomd_df['imd_decile']==decile]
    selected_LSOA_data = selected_LSOA_data[selected_LSOA_data['code'].isin(selected_iomd_df['code'])]
    return selected_LSOA_data, selected_iomd_df