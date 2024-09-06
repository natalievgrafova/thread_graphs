
import dash
from dash import html, dcc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import pandas as pd
import networkx as nx
import numpy as np
import os

app = dash.Dash(__name__)

# Load data
df = pd.read_csv('en_youtube.csv')
#df = df[:100]
df['reply_count'] = np.where(df['reply_count'] == 0, 0.1, df['reply_count'])

# Initialize graph
G = nx.DiGraph()
for index, row in df.iterrows():
    G.add_node(row['comment_id'], comment=row['comment_text'], like_count=row['reply_count'])
    if row['parent_id'] != 'root':
        G.add_edge(row['parent_id'], row['comment_id'])

# Function to scale node sizes based on likes
import math

def scale_node_size(likes, max_likes, min_size=15, max_size=50):
    if max_likes == 0 or likes == 0:  # Avoid division by zero
        return min_size
    # Using logarithmic scaling
    log_likes = math.log10(likes)
    log_max_likes = math.log10(max_likes)
    return min_size + (log_likes / log_max_likes) * (max_size - min_size)


# Find the maximum like count to scale node sizes accordingly
max_likes = df['reply_count'].max()

# Create elements for Cytoscape
elements = [
    {
        'data': {'id': str(node), 'comment': G.nodes[node]['comment']},
        'style': {
            'width': scale_node_size(G.nodes[node]['like_count'], max_likes),
            'height': scale_node_size(G.nodes[node]['like_count'], max_likes)
        }
    }
    for node in G.nodes()
] + [
    {'data': {'source': str(edge[0]), 'target': str(edge[1])}}
    for edge in G.edges()
]

# Stylesheet for the graph
stylesheet = [
    {
        'selector': 'node',
        'style': {
            'background-color': '#0074D9',
            'content': ''  # Hide labels
        }
    },

    {
        'selector': 'node[parent_id="root"]',  # Directly target the root node by its ID
        'style': {
            'background-color': '#FFA500'  # Orange color
        }
    },
    {
        'selector': 'edge',
        'style': {
            'line-color': '#888',
            'width': 2
        }
    }
]

# Layout of the app
app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-graph',
        elements=elements,
        layout={'name': 'cose', 'idealEdgeLength': 100, 'nodeOverlap': 20},
        style={'width': '100%', 'height': '400px'},
        stylesheet=stylesheet
    ),
    html.Pre(id='comment-text', style={
        'padding': '10px',
        'background-color': 'lightgrey',
        'color': 'black',
        'white-space': 'pre-wrap',
        'word-wrap': 'break-word',
        'max-width': '95%',
        'overflow-x': 'auto'
    })
])

# Callback to display node data
@app.callback(
    Output('comment-text', 'children'),
    Input('cytoscape-graph', 'tapNodeData')
)
def display_node_data(data):
    if data:
        return f"Comment: {data['comment']}"
    return "Click on a node to see the comment."

# Run the server
if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
