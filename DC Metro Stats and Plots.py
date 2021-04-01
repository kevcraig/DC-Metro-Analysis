#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 10:12:52 2021

@author: kevincraig
"""

import pandas as pd
import networkx as nx 
import matplotlib.pyplot as plt
from operator import itemgetter
import geopandas as gpd 
import json
from networkx.readwrite import json_graph
from cartopy import crs
import geoviews as gv
from bokeh.models import HoverTool
gv.extension('bokeh')

#%% Import metro data that we manually organized
df_stations2 = pd.read_csv('Datasets/network_order_vf.csv') # manually ordered version of network_order.csv

#%% Create graph nodes and edges
df_stations2['lag_stop'] = df_stations2.sort_values(by = ['Color', 'Stop']).groupby(['Color'])['Name'].shift(1) # previous stop
df_stations2['lead_stop'] = df_stations2.sort_values(by = ['Color', 'Stop']).groupby(['Color'])['Name'].shift(-1) # next stop
df_stations3 = df_stations2[df_stations2['lag_stop'].isnull() == False]
df_stations4 = df_stations3[df_stations2['lead_stop'].isnull() == False]

# nodes
station_list = list(df_stations2['Name'].unique()) # nodes are stations

# edges
name_lag = df_stations4[['Name', 'lag_stop']].to_records(index=False) # edges are connected stops
name_lead = df_stations4[['Name', 'lead_stop']].to_records(index=False) # edges are connected stops
name_lag = list(name_lag) 
name_lead = list(name_lead)

#%%Graph
G = nx.Graph() # initiate graph object

# nodes
G.add_nodes_from(station_list) # add nodes
G.number_of_nodes()
nx.draw(G, with_labels=True, font_weight='bold')

# edges
G.add_edges_from(name_lag) # add edges - before and after stops
G.add_edges_from(name_lead)
nx.draw(G, with_labels=True, font_weight='bold')

# adjacency matrix
A = nx.adjacency_matrix(G)
Adj_Matrix = pd.DataFrame(A.todense())
Adj_Matrix.columns = station_list # name y index
Adj_Matrix.index = station_list # name y index

#%% Adjacency matrix stats
# Degree - this is just matrix math
Adj_Matrix.sum(axis=0).sort_values(ascending = False) # L'Enfant has the most connections
Degrees = Adj_Matrix.sum(axis=0).sort_values(ascending = False)
plt.hist(Degrees)

#%% Graph stats
# network density
density = nx.density(G)
print("Network density:", density)

# shortest path implementation - this could have some cool applications if you have dynamic wait time and breakdown info
ustreet_to_pentagon = nx.shortest_path(G, source="U Street/African-Amer Civil War Memorial/Cardozo", target="Pentagon")
print("Shortest path", ustreet_to_pentagon)

# Look at degree in graph form
degree_dict = dict(G.degree(G.nodes()))
nx.set_node_attributes(G, degree_dict, 'degree')
sorted_degree = sorted(degree_dict.items(), key=itemgetter(1), reverse=True)
df_degree = pd.DataFrame(sorted_degree, columns = ['Station', 'Degree'])
print("Top 20 nodes by degree:")
for d in sorted_degree[:20]:
    print(d)

### centrality
# betweeness
betweenness_dict = nx.betweenness_centrality(G) # Run betweenness centrality
sorted_betweenness = sorted(betweenness_dict.items(), key=itemgetter(1), reverse=True)
df_betweenness = pd.DataFrame(sorted_betweenness, columns = ['Station', 'Betweenness'])
print("Top 20 nodes by betweenness centrality:")
for b in sorted_betweenness[:20]:
    print(b)
    
# closeness
closeness_dict = nx.closeness_centrality(G) # Run betweenness centrality
sorted_closeness = sorted(closeness_dict.items(), key=itemgetter(1), reverse=True)
df_closeness = pd.DataFrame(sorted_closeness, columns = ['Station', 'Closeness'])
print("Top 20 nodes by closeness centrality:")
for b in sorted_closeness[:20]:
    print(b)
    
#%% Write out data for visual analysis through gephi and d3
# gephi output
nx.write_gexf(G, 'Datasets/wmata_network.gexf')

# json output for D3
json_data = json_graph.node_link_data(G)
with open('Datasets/wmata_network.json', 'w') as outfile:
    json.dump(json_data, outfile)

#%% Metro plotting

#Import line data via opendata arcgis api. Geopandas knows how to handle these shapefiles
metro_stops = gpd.read_file("https://opendata.arcgis.com/datasets/e3896b58a4e741d48ddcda03dae9d21b_51.geojson")
metro_lines = gpd.read_file("https://opendata.arcgis.com/datasets/ead6291a71874bf8ba332d135036fbda_58.geojson")

# combnine network stats into one df
metro_stops = metro_stops.merge(df_betweenness, left_on='NAME', right_on='Station')
metro_stops = metro_stops.merge(df_closeness, left_on='NAME', right_on='Station')
metro_stops = metro_stops.merge(df_degree, left_on='NAME', right_on='Station')


# make stop colors black
metro_stops['color'] = 'black'

# stations bokeh object
stations = gv.Points(metro_stops, vdims=['color']).opts(color='color')

# lines bokeh object
lines = gv.Path(metro_lines, vdims=['NAME']).opts(projection=crs.LambertConformal(), height=500, width=500, color='NAME', line_width = 7)

# stations + lines - add tooltip for degree, betweenness, closeness
hover = HoverTool(tooltips=[("Station", "@NAME"), 
                            ('Degree', '@Degree'),
                            ('Betweenness', '@Betweenness'),
                            ('Closeness', '@Closeness')])
# add tooltip to stations
stations = gv.Points(metro_stops, vdims=['color', 'NAME', 'Degree', 'Betweenness', 'Closeness']).opts(tools=[hover],color='color', size = 8)

# plot stations on top of lines
stations_lines = (lines * stations)

# Render
renderer = gv.renderer('bokeh') # use bokeh

# output an HTML file
renderer.save(stations_lines, 'WMATA Network Bokeh')