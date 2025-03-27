import streamlit as st
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import json

# Configure the page
st.set_page_config(
    page_title="CloudFinWise",
    page_icon="☁️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .reportview-container {
        margin-top: -2em;
    }
    .stProgress > div > div > div > div {
        background-color: #1E90FF;
    }
</style>
""", unsafe_allow_html=True)

def scan_aws(services=None):
    """Scan AWS infrastructure"""
    try:
        params = {}
        if services:
            params['services'] = services
        response = requests.post("http://localhost:8006/scan/aws", params=params)
        return response.json()
    except Exception as e:
        st.error(f"Error scanning AWS: {str(e)}")
        return None

def scan_azure(subscription_id, services=None):
    """Scan Azure infrastructure"""
    try:
        params = {'subscription_id': subscription_id}
        if services:
            params['services'] = services
        response = requests.post("http://localhost:8006/scan/azure", params=params)
        return response.json()
    except Exception as e:
        st.error(f"Error scanning Azure: {str(e)}")
        return None

def query_aws(question):
    """Query AWS infrastructure using natural language"""
    try:
        response = requests.post(
            "http://localhost:8006/query/aws",
            json={"question": question}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error querying AWS infrastructure: {str(e)}")
        return None

def query_azure(question):
    """Query Azure infrastructure using natural language"""
    try:
        response = requests.post(
            "http://localhost:8006/query/azure",
            json={"question": question}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error querying Azure infrastructure: {str(e)}")
        return None

def query_all(question):
    """Query both AWS and Azure infrastructure"""
    try:
        response = requests.post(
            "http://localhost:8006/query",
            json={"question": question}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error querying infrastructure: {str(e)}")
        return None

def create_resource_chart(data, title):
    """Create a bar chart for resource counts"""
    resource_counts = {}
    
    # Count resources
    for key, value in data.items():
        if isinstance(value, list):
            resource_counts[key] = len(value)
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=list(resource_counts.keys()),
            y=list(resource_counts.values()),
            marker_color='#1E90FF'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Resource Type",
        yaxis_title="Count",
        template="plotly_white"
    )
    
    return fig

# Sidebar navigation
with st.sidebar:
    selected = option_menu(
        "CloudFinWise",
        ["Dashboard", "AWS Scanner", "Azure Scanner", "Query Infrastructure"],
        icons=['house', 'cloud-fill', 'microsoft', 'chat-dots'],
        menu_icon="cloud",
        default_index=0,
    )

# Main content
if selected == "Dashboard":
    st.title("☁️ CloudFinWise Dashboard")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Scan AWS Infrastructure", key="dash_aws"):
            with st.spinner("Scanning AWS..."):
                aws_data = scan_aws()
                if aws_data:
                    st.plotly_chart(create_resource_chart(
                        aws_data['data'],
                        "AWS Resources Overview"
                    ))
    
    with col2:
        azure_sub_id = st.text_input("Azure Subscription ID")
        if st.button("🔄 Scan Azure Infrastructure", key="dash_azure"):
            if azure_sub_id:
                with st.spinner("Scanning Azure..."):
                    azure_data = scan_azure(azure_sub_id)
                    if azure_data:
                        st.plotly_chart(create_resource_chart(
                            azure_data['data'],
                            "Azure Resources Overview"
                        ))
            else:
                st.warning("Please enter Azure Subscription ID")

elif selected == "AWS Scanner":
    st.title("AWS Infrastructure Scanner")
    st.markdown("---")
    
    services = st.multiselect(
        "Select services to scan",
        ["ec2", "vpc", "s3", "rds", "lambda", "cloudwatch"],
        default=["ec2", "vpc"]
    )
    
    if st.button("🔍 Scan AWS"):
        with st.spinner("Scanning AWS infrastructure..."):
            result = scan_aws(services)
            if result:
                st.success("Scan completed!")
                st.json(result['data'])

elif selected == "Azure Scanner":
    st.title("Azure Infrastructure Scanner")
    st.markdown("---")
    
    subscription_id = st.text_input("Azure Subscription ID")
    services = st.multiselect(
        "Select services to scan",
        ["compute", "network", "storage", "web", "container", "cosmos", "sql"],
        default=["compute", "storage"]
    )
    
    if st.button("🔍 Scan Azure"):
        if subscription_id:
            with st.spinner("Scanning Azure infrastructure..."):
                result = scan_azure(subscription_id, services)
                if result:
                    st.success("Scan completed!")
                    st.json(result['data'])
        else:
            st.warning("Please enter Azure Subscription ID")

elif selected == "Query Infrastructure":
    st.title("Query Infrastructure")
    st.markdown("---")
    
    # Select which cloud to query
    cloud = st.radio(
        "Select Cloud Provider",
        ["AWS Only", "Azure Only", "Both Clouds"],
        horizontal=True
    )
    
    st.markdown("""
    Ask questions about your infrastructure in natural language. Examples:
    
    **AWS Examples:**
    - How many EC2 instances are running?
    - List all S3 buckets with public access
    - What's the total EBS volume size?
    
    **Azure Examples:**
    - Show me all VMs in East US
    - Which storage accounts are not encrypted?
    - List all SQL databases
    
    **Cross-Cloud Examples:**
    - Compare compute resources between AWS and Azure
    - Show total storage across both clouds
    - Which cloud has more running services?
    """)
    
    question = st.text_input("Your question")
    
    if st.button("🤖 Ask"):
        if question:
            with st.spinner("Analyzing..."):
                if cloud == "AWS Only":
                    result = query_aws(question)
                elif cloud == "Azure Only":
                    result = query_azure(question)
                else:  # Both Clouds
                    result = query_all(question)
                    
                if result:
                    if 'error' in result:
                        if result['error'] in ['no_data', 'no_azure_data', 'no_aws_data']:
                            st.warning(result['answer'])
                        else:
                            st.error(result['answer'])
                    else:
                        st.success("Analysis complete!")
                        st.markdown("### Answer")
                        st.write(result['answer'])
                        
                        # Show which cloud was queried
                        if 'cloud' in result:
                            st.info(f"Analyzed {result['cloud'].upper()} infrastructure")
                        elif 'clouds' in result:
                            st.info(f"Analyzed infrastructure from: {', '.join(result['clouds']).upper()}")
        else:
            st.warning("Please enter a question")
