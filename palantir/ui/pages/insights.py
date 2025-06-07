"""Insights page component."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import networkx as nx

from ...models.processors import ObjectProcessor, DataEnricher
from ...ontology.repository import OntologyRepository
from ...analytics.metrics import calculate_metrics
from ...analytics.forecasting import TimeSeriesForecaster

# Initialize components
repo = OntologyRepository()
processor = ObjectProcessor()
enricher = DataEnricher()
forecaster = TimeSeriesForecaster()


def render_object_insights():
    """Render object-level insights."""
    st.markdown("### 📊 Object Insights")
    
    # Object type selector
    obj_type = st.selectbox(
        "Select Object Type",
        ["Customer", "Order", "Product"]
    )
    
    # Analysis type
    analysis_type = st.radio(
        "Analysis Type",
        ["Basic Insights", "Clustering Analysis", "Anomaly Detection"],
        horizontal=True
    )
    
    if st.button("Generate Insights"):
        with st.spinner("Analyzing objects..."):
            # Get objects
            objects = repo.search_objects(obj_type=obj_type)
            
            if not objects:
                st.warning("No objects found for analysis")
                return
            
            if analysis_type == "Basic Insights":
                # Generate insights for each object
                insights = []
                for obj in objects:
                    analysis = processor.analyze_object(obj, obj_type)
                    insights.append(analysis)
                
                # Display summary
                st.markdown("#### Key Findings")
                
                # Aggregate insights
                all_key_points = [
                    point
                    for insight in insights
                    for point in insight.key_points
                ]
                
                all_suggestions = [
                    suggestion
                    for insight in insights
                    for suggestion in insight.suggestions
                ]
                
                # Display top insights
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Common Patterns**")
                    for point in all_key_points[:5]:
                        st.write(f"• {point}")
                
                with col2:
                    st.markdown("**Top Recommendations**")
                    for suggestion in all_suggestions[:5]:
                        st.write(f"• {suggestion}")
                
                # Add metric visualizations
                metrics = calculate_metrics(objects)
                
                st.markdown("#### Key Metrics")
                
                # Create metrics dashboard
                fig = go.Figure()
                
                for metric_name, values in metrics.items():
                    fig.add_trace(go.Indicator(
                        mode="number+delta",
                        value=values["current"],
                        delta={"reference": values["previous"]},
                        title={"text": metric_name},
                        domain={"row": 0, "column": 0}
                    ))
                
                st.plotly_chart(fig, use_container_width=True)
            
            elif analysis_type == "Clustering Analysis":
                # Prepare data for clustering
                df = pd.DataFrame(objects)
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                
                if len(numeric_cols) < 2:
                    st.warning("Not enough numeric features for clustering")
                    return
                
                # Standardize features
                X = StandardScaler().fit_transform(df[numeric_cols])
                
                # Perform clustering
                n_clusters = st.slider("Number of Clusters", 2, 10, 3)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = kmeans.fit_predict(X)
                
                # Reduce dimensionality for visualization
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(X)
                
                # Create clustering visualization
                cluster_df = pd.DataFrame({
                    "PC1": X_pca[:, 0],
                    "PC2": X_pca[:, 1],
                    "Cluster": clusters
                })
                
                fig = px.scatter(
                    cluster_df,
                    x="PC1",
                    y="PC2",
                    color="Cluster",
                    title="Object Clusters"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Analyze clusters
                st.markdown("#### Cluster Analysis")
                
                for i in range(n_clusters):
                    with st.expander(f"Cluster {i} Analysis"):
                        cluster_objects = [obj for j, obj in enumerate(objects) if clusters[j] == i]
                        cluster_insights = processor.analyze_cluster(cluster_objects)
                        
                        st.markdown("**Characteristics:**")
                        for char in cluster_insights.characteristics:
                            st.write(f"• {char}")
                        
                        st.markdown("**Recommendations:**")
                        for rec in cluster_insights.recommendations:
                            st.write(f"• {rec}")
            
            else:  # Anomaly Detection
                # Prepare data for anomaly detection
                df = pd.DataFrame(objects)
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                
                if len(numeric_cols) < 1:
                    st.warning("No numeric features for anomaly detection")
                    return
                
                # Detect anomalies using IQR method
                anomalies = {}
                for col in numeric_cols:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    anomalies[col] = df[
                        (df[col] < lower_bound) | (df[col] > upper_bound)
                    ]
                
                # Display anomalies
                st.markdown("#### Anomaly Detection Results")
                
                for col, anomaly_df in anomalies.items():
                    if not anomaly_df.empty:
                        with st.expander(f"Anomalies in {col}"):
                            st.dataframe(anomaly_df)
                            
                            # Create box plot
                            fig = go.Figure()
                            fig.add_trace(go.Box(
                                y=df[col],
                                name=col,
                                boxpoints="outliers"
                            ))
                            
                            st.plotly_chart(fig, use_container_width=True)


def render_trend_analysis():
    """Render trend analysis section."""
    st.markdown("### 📈 Trend Analysis")
    
    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        ["Last Week", "Last Month", "Last Quarter", "Last Year"]
    )
    
    # Metric selector
    metric = st.selectbox(
        "Metric",
        ["Order Volume", "Revenue", "Customer Growth", "Product Performance"]
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        show_forecast = st.checkbox("Show Forecast", value=True)
    
    with col2:
        show_seasonality = st.checkbox("Show Seasonality Analysis", value=True)
    
    if st.button("Analyze Trends"):
        # Get historical data
        historical_data = repo.get_historical_data(metric, time_range)
        
        if historical_data.empty:
            st.warning("No historical data available")
            return
        
        # Create trend visualization
        fig = go.Figure()
        
        # Add historical data
        fig.add_trace(go.Scatter(
            x=historical_data.index,
            y=historical_data.values,
            name="Historical",
            mode="lines"
        ))
        
        if show_forecast:
            # Generate forecast
            forecast = forecaster.predict(historical_data, periods=30)
            
            # Add forecast
            fig.add_trace(go.Scatter(
                x=forecast.index,
                y=forecast.values,
                name="Forecast",
                mode="lines",
                line=dict(dash="dash")
            ))
            
            # Add confidence intervals
            fig.add_trace(go.Scatter(
                x=forecast.index,
                y=forecast["upper_bound"],
                fill=None,
                mode="lines",
                line_color="rgba(0,100,80,0)",
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast.index,
                y=forecast["lower_bound"],
                fill="tonexty",
                mode="lines",
                line_color="rgba(0,100,80,0)",
                name="Confidence Interval"
            ))
        
        fig.update_layout(title=f"{metric} Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # Add trend indicators
        col1, col2, col3 = st.columns(3)
        
        current_value = historical_data.iloc[-1]
        previous_value = historical_data.iloc[-2]
        
        with col1:
            st.metric(
                "Current Value",
                f"{current_value:.2f}",
                f"{(current_value - previous_value):.2f}"
            )
        
        with col2:
            st.metric(
                "Average",
                f"{historical_data.mean():.2f}"
            )
        
        with col3:
            growth_rate = ((current_value - historical_data.iloc[0]) / 
                         historical_data.iloc[0] * 100)
            st.metric(
                "Growth Rate",
                f"{growth_rate:.1f}%"
            )
        
        if show_seasonality:
            st.markdown("#### Seasonality Analysis")
            
            # Perform seasonal decomposition
            decomposition = forecaster.decompose(historical_data)
            
            # Create decomposition plot
            fig = go.Figure()
            
            components = ["Trend", "Seasonal", "Residual"]
            for component, values in zip(components, decomposition):
                fig.add_trace(go.Scatter(
                    x=historical_data.index,
                    y=values,
                    name=component
                ))
            
            fig.update_layout(title="Seasonal Decomposition")
            st.plotly_chart(fig, use_container_width=True)


def render_relationship_insights():
    """Render relationship insight section."""
    st.markdown("### 🔗 Relationship Insights")
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        # Select relationship type
        relationship_type = st.selectbox(
            "Relationship Type",
            ["Customer-Order", "Order-Product", "Customer-Product"]
        )
    
    with col2:
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Basic", "Detailed", "Advanced"],
            value="Detailed"
        )
    
    if st.button("Analyze Relationships"):
        # Get relationship data
        source_type, target_type = relationship_type.split("-")
        
        source_objects = repo.search_objects(obj_type=source_type)
        target_objects = repo.search_objects(obj_type=target_type)
        
        if not source_objects or not target_objects:
            st.warning("Not enough data for analysis")
            return
        
        # Analyze relationships
        insights = []
        relationships = []
        
        for source in source_objects[:5]:  # Limit for demo
            for target in target_objects[:5]:
                insight = processor.analyze_relationship(
                    source,
                    target,
                    relationship_type,
                    depth=analysis_depth
                )
                insights.append(insight)
                
                # Get relationship data
                rel = repo.get_relationship(source["id"], target["id"])
                if rel:
                    relationships.append(rel)
        
        # Display relationship network
        st.markdown("#### Relationship Network")
        
        G = nx.Graph()
        
        # Add nodes
        for obj in source_objects + target_objects:
            G.add_node(
                str(obj["id"]),
                label=f"{obj['type']}: {obj.get('name', 'Unnamed')}"
            )
        
        # Add edges
        for rel in relationships:
            G.add_edge(
                str(rel["source_id"]),
                str(rel["target_id"]),
                weight=rel.get("weight", 1.0)
            )
        
        # Create network visualization
        pos = nx.spring_layout(G)
        
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines"
        )
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace["x"] += (x0, x1, None)
            edge_trace["y"] += (y0, y1, None)
        
        node_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode="markers",
            hoverinfo="text",
            marker=dict(
                showscale=True,
                colorscale="YlGnBu",
                size=10
            )
        )
        
        for node in G.nodes():
            x, y = pos[node]
            node_trace["x"] += (x,)
            node_trace["y"] += (y,)
            node_trace["text"] += (G.nodes[node]["label"],)
        
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title="Relationship Network",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display insights
        st.markdown("#### Relationship Insights")
        
        for i, insight in enumerate(insights, 1):
            with st.expander(f"Insight {i}: {insight.description}"):
                st.write(f"**Significance:** {insight.significance}")
                
                if analysis_depth in ["Detailed", "Advanced"]:
                    st.write(f"**Impact Score:** {insight.impact_score}")
                    st.write(f"**Confidence:** {insight.confidence}%")
                
                st.markdown("**Key Findings:**")
                for finding in insight.findings:
                    st.write(f"• {finding}")
                
                st.markdown("**Recommendations:**")
                for rec in insight.recommendations:
                    st.write(f"• {rec}")
                
                if analysis_depth == "Advanced":
                    st.markdown("**Detailed Analysis:**")
                    st.json(insight.detailed_analysis)


def render_page():
    """Render the insights page."""
    st.title("💡 Insights")
    
    st.markdown("""
        Discover patterns, trends, and insights in your data.
        Get AI-powered recommendations and analysis.
    """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs([
        "Object Insights",
        "Trend Analysis",
        "Relationship Insights"
    ])
    
    with tab1:
        render_object_insights()
    
    with tab2:
        render_trend_analysis()
    
    with tab3:
        render_relationship_insights() 