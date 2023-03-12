#############################
# Assignment 2
# CIS600
#############################

from TwitterCookbook import oauth_login, crawl_network
from graph_utils import save_graph_info, save_graph_vis
import networkx as nx
import json

def main(status):
    if status=='crawl':
        # Set twitter API settings
        twitter_api = oauth_login()

        # Crawl network with seed username
        # crawl_network() is my own code from TwitterCookbook
        network = crawl_network(twitter_api, "")

        # Save data
        json_data = json.dumps(network)
        # write JSON-formatted string to a file
        with open('./data/network_data.json', 'w') as f:
            f.write(json_data)
    
    elif status=='load':
        # Load data
        with open('./data/network_data.json', 'r') as f:
            json_data = f.read()

        # Parse JSON data into a dictionary
        result_dict = json.loads(json_data)
        new_dict = {int(key): value for key, value in result_dict.items()}  # Change key to integer like the list of ids in value
        
        # Initialize the network graph
        G = nx.Graph(new_dict)
        # Save network information into a new file
        save_graph_info(G, "./data/networkInfo.txt")
        # Save network visualization
        save_graph_vis(G, "./data/networkVis")
    else:
        raise Exception("Only input 'crawl' or 'load'")

if __name__ == "__main__":
    main('load')