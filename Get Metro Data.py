#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 10:05:17 2021

@author: kevincraig
"""
import os
import http.client, urllib.request, urllib.parse, urllib.error, json, time 
import pandas as pd

#%%  API setup
# WMATA API key
api_key = open("WMATA_API_KEY.txt", "r") # you can get a free key here, but you will get rate limited. I requested a production key. https://developer.wmata.com/Products 
WMATA_KEY = api_key.read()

headers = {
    # Request headers
    'api_key': WMATA_KEY,
}

# Get station data from API
def get_stations(line_code):
    
    # define what line you want
    params = urllib.parse.urlencode({
    # Request parameters
    'LineCode': line_code})
    
    # hit api
    try:
        conn = http.client.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/Rail.svc/json/jStations?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        return(json.loads(data))
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
    
# Get line data from API
def get_lines():
    
    # hit api
    try:
        conn = http.client.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/Rail.svc/json/jLines?%s", "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        return(json.loads(data))
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        
#%% Get station data

lines = ['BL', 'GR', 'OR', 'RD', 'SV', 'YL'] # all lines in dc
station_data = []

# list of station dicts
for i in lines:
    station_data.append(get_stations(i))
    # time.sleep(2) # sleep so we dont get rate limited - if you have guest api key
    
# unpack dicts to dataframe
df_stations = pd.DataFrame(columns = ['Code', 'Name', 'StationTogether1', 'StationTogether2', 'LineCode1', 'LineCode2', 'LineCode3', 'LineCode4', 'Lat', 'Lon', 'Address'])    
for i in station_data:
    for x in i['Stations']:
        temp_df = pd.DataFrame(x.items()).T[1:]
        temp_df.columns = ['Code', 'Name', 'StationTogether1', 'StationTogether2', 'LineCode1', 'LineCode2', 'LineCode3', 'LineCode4', 'Lat', 'Lon', 'Address']
        df_stations = df_stations.append(temp_df)
    

#%% Get line data
line_data = get_lines()['Lines']

# unpack dicts to dataframe
df_lines = pd.DataFrame(columns = ['LineCode', 'DisplayName', 'StartStationCode', 'EndStationCode', 'InternalDestination1', 'InternalDestination2'])
for i in line_data:
    temp_df = pd.DataFrame(i.items()).T[1:]
    temp_df.columns = ['LineCode', 'DisplayName', 'StartStationCode', 'EndStationCode', 'InternalDestination1', 'InternalDestination2']
    df_lines = df_lines.append(temp_df)
    
#%% I/O for metro data
# write out data so we can order the stops manually. There is no indicator in the dataset for station order, so we need to do this outselves. I also include this file in the repo
df_stations.to_csv('/Users/kevincraig/Google Drive/Personal/DC Metro/Metro Project/network_order.csv')