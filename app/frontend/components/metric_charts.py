import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

def create_time_series_chart(data: dict, title: str = None):
    """Create an interactive time series chart using Plotly."""
    fig = go.Figure()
    
    # Convert timestamps to datetime if they're strings
    timestamps = [
        t if isinstance(t, datetime) else datetime.fromisoformat(t.rstrip('Z'))
        for t in data['timestamps']
    ]
    
    # Add the main metric line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=data['values'],
        mode='lines',
        name=data['label'],
        line=dict(width=2)
    ))
    
    # Add range selector and slider
    fig.update_layout(
        title=title or data['label'],
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    return fig

def render_metric_chart(metric_data: dict, container=None):
    """Render a metric chart in Streamlit."""
    container = container or st
    
    # Create chart
    fig = create_time_series_chart(metric_data)
    
    # Add chart to Streamlit
    container.plotly_chart(fig, use_container_width=True)
    
    # Add statistics
    if metric_data['values']:
        stats = pd.Series(metric_data['values']).describe()
        cols = container.columns(4)
        cols[0].metric("Average", f"{stats['mean']:.2f}")
        cols[1].metric("Maximum", f"{stats['max']:.2f}")
        cols[2].metric("Minimum", f"{stats['min']:.2f}")
        cols[3].metric("Std Dev", f"{stats['std']:.2f}")

def render_multi_metric_chart(metrics_data: list, title: str = None, container=None):
    """Render multiple metrics in a single chart."""
    container = container or st
    
    fig = go.Figure()
    
    for data in metrics_data:
        timestamps = [
            t if isinstance(t, datetime) else datetime.fromisoformat(t.rstrip('Z'))
            for t in data['timestamps']
        ]
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=data['values'],
            mode='lines',
            name=data['label'],
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title=title,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    
    container.plotly_chart(fig, use_container_width=True)

# Example usage in Streamlit:
"""
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

# Sample data
timestamps = [datetime.now() - timedelta(minutes=i) for i in range(60)]
values = np.random.normal(50, 10, 60)
data = {
    'timestamps': timestamps,
    'values': values,
    'label': 'CPU Usage (%)'
}

st.title('Infrastructure Metrics')
render_metric_chart(data)
"""
