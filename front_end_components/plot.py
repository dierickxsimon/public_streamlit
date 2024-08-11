import numpy as np
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px

from data_handler.utils import create_graph



def plot_with_vertical_lines(red_line_position, obj):
    # Create line chart
    x_values = obj.df_raw['(Sample number)'][20:]
    y_values = obj.df_raw[obj.analysis_based_on][20:]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines',
        line=dict(color='blue', width=2),
        showlegend=False
    ))

    # Add red vertical line
    fig.add_shape(
        type="line",
        x0=red_line_position,
        y0=min(y_values),
        x1=red_line_position,
        y1=max(y_values),
        line=dict(color="red", width=3, dash="dash"),
        xref='x',
        yref='y'
    )
    
    #add black line
    for line_position, marker in obj.markers.markers.items():
        fig.add_shape(
            type="line",
            x0=line_position,
            y0=min(y_values),
            x1=line_position,
            y1=max(y_values),
            line=dict(color="black", width=1, dash="dash"),
            xref='x',
            yref='y',
        )
        
        fig.add_annotation(
            x=line_position,
            y=max(y_values),
            text=marker, 
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-30
        )


    # Update layout
    fig.update_layout({"uirevision": "foo"}, 
                    overwrite=True,
    xaxis_title='time',
    yaxis_title=obj.analysis_based_on,
    coloraxis=dict(colorscale='Viridis'),
)

    return fig


def plot_oxcap_model(obj):
    if len(obj.df_analysis)>0:
            x = np.linspace(0, obj.df_analysis['time'].max(), 400)
            x,y = create_graph((obj.data['Y_end'], obj.data['A'], obj.data['Tau']), x)
    else:
        x=0
        y=0
        
    fig = px.scatter(
        obj.df_analysis,
        'time',
        'B1',
        'type'
    )
    
    if isinstance(obj.outliers, pd.DataFrame) and len(obj.outliers) > 0:
        fig.add_trace(go.Scatter(
            x=obj.outliers['time'],
            y=obj.outliers['B1'],
            mode='markers',
            marker=dict(color='red'),
            name='Outliers'
            ))
    
    
    fig.add_trace(go.Scatter(
        x=x,
        y=y,  
        mode='lines',
        name='Model',  
        line=dict(color='black', width=2), 
            ))
        
    return fig
                    