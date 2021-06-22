import pandas
import random
import geopandas
import numpy as np
from pyproj import CRS
from scipy import stats
import matplotlib.pyplot as plt
from shapely.geometry import Point
from networkx import nx
from IPython.display import HTML


# Data Aggregation Part

# Read all Data from GTFS Dataset
df_stopstime = pandas.read_csv('gtfs_fp2021_2021-04-14_09-10/stop_times.txt',low_memory=False)
df_routes = pandas.read_csv('gtfs_fp2021_2021-04-14_09-10/routes.txt')
df_trips = pandas.read_csv('gtfs_fp2021_2021-04-14_09-10/trips.txt')
df_stops = pandas.read_csv('stops.txt')

# Convert to Dataframe and Add CRS to set 0 point of the Map

df_stops = geopandas.GeoDataFrame(df_stops, geometry=geopandas.points_from_xy(df_stops.stop_lon, df_stops.stop_lat))
df_stops.crs = CRS('epsg:4326') 

# Join the GeoJSON of the Swiss Map with the Stops of the Dataset
df_stops_ch = geopandas.sjoin(df_stops, df_ch)

# Filter only InterCity and InterRegio
df_routes_filtered = df_routes.query('route_type == [102,103]')

# Join the Datasets together
routes_trips = pandas.merge(df_routes_filtered,df_trips,on='route_id')
routes_trips_stoptime = pandas.merge(routes_trips, df_stopstime,on='trip_id')
routes_trips_stoptime_stop = pandas.merge(routes_trips_stoptime, df_stops_ch,on='stop_id')


# Remove duplicate entries
stops_ch_unique = routes_trips_stoptime_stop.drop_duplicates('stop_name')
route_ch_unique = routes_trips_stoptime_stop.drop_duplicates(subset=['stop_id'])
routes_trips_stoptime_stop.to_csv(r'routes_trips_stoptime_stop.csv', index = False)


#Generating the Graph from the Pandas DataFrame
import networkx as nx
G = nx.Graph()
for name, group in routes_trips_stoptime_stop.groupby('trip_id'):
    n = False
    for row_index, row in group.sort_values(by='stop_sequence').iterrows():
        if(n !=False):
            G.add_edge(row.stop_name,n)
        G.add_node(row.stop_name)
        n = row.stop_name  

# Creates a Copy of the origin Graph and runs the Function to remove Nodes based on betweenness centrality
P = G.copy()
p_wiener = []
p_randic = []
for _ in  range(int(P.number_of_nodes()*0.2)):
    p_wiener.append(get_wienerindex(P))
    p_randic.append(get_randicindex(P))
    P.remove_nodes_from(get_betweenness_centrality_list(P,1))
    
# Creates a Copy of the origin Graph and runs the Function to randomly remove Nodes

R = G.copy()
r_wiener = []
r_randic = []
for _ in  range(int(R.number_of_nodes()*0.2)):
    r_wiener.append(get_wienerindex(R))
    r_randic.append(get_randicindex(R))
    R.remove_nodes_from(get_random_nodes(R,1))
        
        
# Function for Text Part

def get_wienerchart():
    plt.title("Wiener Index")
    plt.xlabel('Node')
    plt.ylabel('Value')
    plt.plot(r_wiener, label = "Zufall Wiener Index")
    plt.plot(p_wiener, label = "Gezielt Wiener Index")
    plt.legend()
    plt.show()

def get_randicchart():
    plt.title("Randic Index")
    plt.xlabel('Node')
    plt.ylabel('Value')
    plt.plot(r_randic, label = "Zufall Randic Index")
    plt.plot(p_randic, label = "Gezielt Randic Index")
    plt.legend()
    plt.show()

def get_gezkorrelation():
    plt.title("Gezielter Ausfall, Korrelation: " + str(stats.pearsonr(p_wiener,p_randic)[0]))
    plt.xlabel('Node')
    plt.ylabel('Value')
    plt.plot([1/max(p_wiener)*s for s in p_wiener], label = "Gezielt Wiener")
    plt.plot([1/max(p_randic)*s for s in p_randic], label = "Gezielt Randic")
    plt.legend()
    plt.show()

def get_randkorrelation():
    plt.title("Zufälliger Ausfall, Korrelation: " + str(stats.pearsonr(r_wiener,r_randic)[0]))
    plt.xlabel('Node')
    plt.ylabel('Value')
    plt.plot([1/max(r_wiener)*s for s in r_wiener], label = "Zufall Wiener")
    plt.plot([1/max(r_randic)*s for s in r_randic], label = "Zufall Randic")
    plt.legend()
    plt.show()
    
def get_outagestats():
    HTML(pandas.DataFrame(data={'Gezielte Ausfälle': [str(len([s for s in nx.connected_components(P)]))], 'Zufällige Ausfälle': [str(len([s for s in nx.connected_components(R)]))]}).to_html(index=False))

def get_degreedist():
    plt.title("Degree distribution")
    plt.xlabel('Degree')
    plt.ylabel('Nodes')
    plt.hist(dict(G.degree).values())
    plt.show()
#Get Random Number of Nodes
def get_random_nodes(G,num=1):
    return random.sample(G.nodes(), num)

# Wiener Index
def get_wienerindex(G):
    return 0.5*sum([sum(i.values()) for s,i in nx.shortest_path_length(G)])

# Randic Index
def get_randicindex(G):
    c =0
    for n in G.nodes():
        for e in G.edges(n):
            c += 1/((G.degree(n)*G.degree(e[1]))**0.5)
    return c

# Draw the Graph from The Networkx Data

def get_graph(G,size=10,title=''):
    options = {
        'node_color': 'orange',
        'node_size': 10,
        'width': 1,
    }
    plt.figure(figsize=(size,size))
    pos = nx.spring_layout(G)
    cluster = str(len([s for s in nx.connected_components(G)]))
    plt.title(title + "Cluster: " + cluster)
    nx.draw(G,pos, **options)
    nx.draw_networkx_labels(G,pos, font_size=size*0.8)
    
# Gets a list with Nodes, ordered by betwenness Centrality
def get_betweenness_centrality_list(G,num=0):
    return [s for s,n in sorted(nx.betweenness_centrality(G,normalized=False).items(), key=lambda x: x[1], reverse=True)][:num]


  
def get_stopsch():
    f, ax = plt.subplots(figsize=(10, 10))
    geopandas.GeoDataFrame(stops_ch_unique).plot(ax=ax)
    ax.set_axis_off()
    plt.show()
    
def show_transportdata():
    f, ax = plt.subplots(figsize=(15, 15))
    geopandas.GeoDataFrame(df_stops).plot(ax=ax,markersize=0.1)
    geopandas.GeoDataFrame(df_stops_ch).plot(ax=ax,markersize=0.1)
    ax.set_axis_off()
    plt.show()

def show_geojson():
    df_ch = geopandas.read_file("switzerland.geojson")
    f, ax = plt.subplots(figsize=(10, 10))
    geopandas.GeoDataFrame(df_ch).plot(ax=ax)
    ax.set_axis_off()
    plt.show()