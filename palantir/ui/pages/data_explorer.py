"""Data explorer page component."""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from ...models.llm import QueryGenerator
from ...ontology.repository import OntologyRepository
from ...analytics.metrics import calculate_metrics

# Initialize components
repo = OntologyRepository()
query_gen = QueryGenerator()


def prepare_visualization_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Prepare data for visualization.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (processed DataFrame, numeric columns)
    """
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Handle dates
    date_cols = df.select_dtypes(include=['datetime64']).columns
    for col in date_cols:
        df[f"{col}_days_ago"] = (datetime.now() - df[col]).dt.days
        numeric_cols.append(f"{col}_days_ago")
    
    return df, numeric_cols


def create_correlation_heatmap(df: pd.DataFrame, numeric_cols: List[str]) -> go.Figure:
    """Create correlation heatmap.
    
    Args:
        df: Input DataFrame.
        numeric_cols: List of numeric column names.
        
    Returns:
        Plotly figure object.
    """
    corr_matrix = df[numeric_cols].corr()
    
    return go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=numeric_cols,
        y=numeric_cols,
        colorscale='RdBu',
        zmin=-1,
        zmax=1
    ))


def create_pca_visualization(df: pd.DataFrame, numeric_cols: List[str]) -> go.Figure:
    """Create PCA visualization.
    
    Args:
        df: Input DataFrame.
        numeric_cols: List of numeric column names.
        
    Returns:
        Plotly figure object.
    """
    # Prepare data
    X = df[numeric_cols].fillna(0)
    X_scaled = StandardScaler().fit_transform(X)
    
    # Apply PCA
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    
    # Create visualization
    fig = go.Figure(data=go.Scatter(
        x=components[:, 0],
        y=components[:, 1],
        mode='markers',
        text=df.index,
        hovertemplate="<b>Index: %{text}</b><br>" +
                     "PC1: %{x:.2f}<br>" +
                     "PC2: %{y:.2f}"
    ))
    
    fig.update_layout(
        title="PCA Visualization",
        xaxis_title="First Principal Component",
        yaxis_title="Second Principal Component"
    )
    
    return fig


def render_search_section():
    """Render the search interface."""
    st.markdown("### 🔍 Search Objects")
    
    # Search type selector
    search_type = st.radio(
        "Search Method",
        ["Natural Language", "Advanced Query", "Visual Query Builder"],
        horizontal=True
    )
    
    if search_type == "Natural Language":
        # Natural language search
        query = st.text_input(
            "Describe what you're looking for",
            placeholder="e.g., Find all customers who made purchases in the last month"
        )
        
        if query:
            with st.spinner("Generating query..."):
                structured_query = query_gen.generate_query(query)
                
                # Show generated query
                with st.expander("View Generated Query"):
                    st.json(structured_query)
                
                # Execute search
                results = repo.search_objects(**structured_query)
                display_results(results)
    
    elif search_type == "Advanced Query":
        # Advanced query builder
        col1, col2 = st.columns(2)
        
        with col1:
            obj_type = st.selectbox(
                "Object Type",
                ["Customer", "Order", "Product"]
            )
        
        with col2:
            property_field = st.text_input(
                "Property Filter (JSON)",
                placeholder='{"status": "pending"}'
            )
        
        if st.button("Search"):
            try:
                properties = json.loads(property_field) if property_field else None
                results = repo.search_objects(
                    obj_type=obj_type,
                    properties=properties
                )
                display_results(results)
            except json.JSONDecodeError:
                st.error("Invalid JSON in property filter")
    
    else:  # Visual Query Builder
        st.markdown("#### Visual Query Builder")
        
        # Object type selection
        obj_type = st.selectbox(
            "Select Object Type",
            ["Customer", "Order", "Product"]
        )
        
        # Property filters
        st.markdown("##### Add Filters")
        
        filters = []
        col1, col2, col3 = st.columns(3)
        
        with col1:
            property_name = st.text_input("Property")
        with col2:
            operator = st.selectbox(
                "Operator",
                ["equals", "greater_than", "less_than", "contains"]
            )
        with col3:
            value = st.text_input("Value")
        
        if st.button("Add Filter"):
            filters.append({
                "property": property_name,
                "operator": operator,
                "value": value
            })
        
        if filters:
            st.json(filters)
            
            if st.button("Execute Query"):
                results = repo.search_objects(
                    obj_type=obj_type,
                    filters=filters
                )
                display_results(results)


def display_results(results: List[Dict]):
    """Display search results.
    
    Args:
        results: List of object dictionaries.
    """
    if not results:
        st.info("No results found")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(results)
    
    # Prepare data for visualization
    df_viz, numeric_cols = prepare_visualization_data(df)
    
    # Display controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        view_type = st.radio(
            "View As",
            ["Table", "JSON", "Basic Charts", "Advanced Analytics"],
            horizontal=True
        )
    
    with col2:
        if view_type == "Basic Charts":
            chart_type = st.selectbox(
                "Chart Type",
                ["Bar", "Line", "Scatter", "Pie", "Box", "Violin"]
            )
    
    # Display results
    if view_type == "Table":
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "id": st.column_config.TextColumn(
                    "ID",
                    width="medium"
                )
            }
        )
        
        # Show basic statistics
        if st.checkbox("Show Statistics"):
            st.markdown("#### Basic Statistics")
            st.dataframe(df.describe())
    
    elif view_type == "JSON":
        st.json(results)
    
    elif view_type == "Basic Charts":
        if len(df) > 0:
            try:
                # Column selection for visualization
                x_col = st.selectbox("X-axis", df.columns)
                y_col = st.selectbox("Y-axis", numeric_cols if numeric_cols else df.columns)
                
                if chart_type == "Bar":
                    fig = px.bar(df, x=x_col, y=y_col)
                elif chart_type == "Line":
                    fig = px.line(df, x=x_col, y=y_col)
                elif chart_type == "Scatter":
                    fig = px.scatter(df, x=x_col, y=y_col)
                elif chart_type == "Pie":
                    fig = px.pie(df, values=y_col, names=x_col)
                elif chart_type == "Box":
                    fig = px.box(df, x=x_col, y=y_col)
                else:  # Violin
                    fig = px.violin(df, x=x_col, y=y_col)
                
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Could not create chart: {str(e)}")
        else:
            st.info("Not enough data for visualization")
    
    else:  # Advanced Analytics
        st.markdown("#### Advanced Analytics")
        
        # Correlation analysis
        if st.checkbox("Show Correlation Analysis"):
            if numeric_cols:
                st.markdown("##### Correlation Heatmap")
                fig = create_correlation_heatmap(df_viz, numeric_cols)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No numeric columns available for correlation analysis")
        
        # PCA visualization
        if st.checkbox("Show PCA Visualization"):
            if len(numeric_cols) >= 2:
                st.markdown("##### PCA Analysis")
                fig = create_pca_visualization(df_viz, numeric_cols)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough numeric columns for PCA visualization")
        
        # Time series analysis (if applicable)
        if any(df.dtypes.str.contains('datetime')):
            if st.checkbox("Show Time Series Analysis"):
                st.markdown("##### Time Series Analysis")
                date_col = st.selectbox(
                    "Select Date Column",
                    df.select_dtypes(include=['datetime64']).columns
                )
                metric_col = st.selectbox(
                    "Select Metric",
                    numeric_cols
                )
                
                # Create time series plot
                fig = px.line(
                    df,
                    x=date_col,
                    y=metric_col,
                    title=f"{metric_col} Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)


def render_filters_section():
    """Render the filters sidebar."""
    st.sidebar.markdown("### 🎯 Filters")
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
    )
    
    # Status filter
    selected_status = st.sidebar.multiselect(
        "Status",
        ["Active", "Pending", "Completed", "Cancelled"]
    )
    
    # Value range filter
    value_range = st.sidebar.slider(
        "Value Range",
        min_value=0,
        max_value=1000,
        value=(0, 1000)
    )
    
    # Export filtered data
    if st.sidebar.button("Export Filtered Data"):
        # TODO: Implement export functionality
        pass


def render_page():
    """Render the data explorer page."""
    st.title("🔍 Data Explorer")
    
    st.markdown("""
        Search and explore your data using natural language or advanced queries.
        Visualize results and discover patterns in your ontology objects.
    """)
    
    # Main layout
    render_search_section()
    
    # Sidebar filters
    render_filters_section() 