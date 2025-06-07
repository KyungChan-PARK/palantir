"""Ontology viewer page component."""

from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

import networkx as nx
import plotly.graph_objects as go
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import community
import pandas as pd
from networkx.algorithms import centrality

from ...ontology.repository import OntologyRepository
from ...analytics.graph_metrics import calculate_graph_metrics

# Initialize repository
repo = OntologyRepository()


def create_graph_data(
    filter_types: Optional[List[str]] = None,
    min_weight: float = 0.0
) -> Tuple[List[Node], List[Edge]]:
    """Create graph visualization data from the ontology.
    
    Args:
        filter_types: Optional list of object types to include.
        min_weight: Minimum weight threshold for edges.
    
    Returns:
        Tuple of (nodes, edges) for visualization.
    """
    nodes = []
    edges = []
    
    # Get all objects
    objects = repo.search_objects()
    if filter_types:
        objects = [obj for obj in objects if obj["type"] in filter_types]
    
    # Create nodes
    for obj in objects:
        nodes.append(
            Node(
                id=str(obj["id"]),
                label=f"{obj['type']}: {obj.get('name', 'Unnamed')}",
                size=20,
                color=get_node_color(obj["type"]),
                title=json.dumps(obj["properties"], indent=2)  # Hover information
            )
        )
    
    # Get relationships
    for obj in objects:
        linked = repo.get_linked_objects(obj["id"])
        for link in linked:
            weight = float(link["relationship"].get("weight", 1.0))
            if weight >= min_weight:
                edges.append(
                    Edge(
                        source=str(obj["id"]),
                        target=str(link["object"]["id"]),
                        label=link["relationship"]["type"],
                        weight=weight
                    )
                )
    
    return nodes, edges


def get_node_color(obj_type: str) -> str:
    """Get color for node based on object type.
    
    Args:
        obj_type: Type of the object.
        
    Returns:
        Hex color code.
    """
    colors = {
        "Customer": "#FF6B6B",
        "Order": "#4ECDC4",
        "Product": "#45B7D1",
        "Service": "#96CEB4",
        "Employee": "#FFEEAD",
        "Location": "#D4A5A5"
    }
    return colors.get(obj_type, "#95A5A6")


def create_networkx_graph(nodes: List[Node], edges: List[Edge]) -> nx.Graph:
    """Create NetworkX graph from nodes and edges.
    
    Args:
        nodes: List of Node objects.
        edges: List of Edge objects.
    
    Returns:
        NetworkX graph object.
    """
    G = nx.Graph()
    
    # Add nodes with attributes
    for node in nodes:
        G.add_node(
            node.id,
            label=node.label,
            color=node.color
        )
    
    # Add edges with weights
    for edge in edges:
        G.add_edge(
            edge.source,
            edge.target,
            weight=edge.weight,
            label=edge.label
        )
    
    return G


def render_graph_view():
    """Render the graph visualization."""
    # Filter controls
    st.markdown("### Graph Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_types = st.multiselect(
            "Filter Object Types",
            ["Customer", "Order", "Product", "Service", "Employee", "Location"],
            default=["Customer", "Order", "Product"]
        )
    
    with col2:
        min_weight = st.slider(
            "Minimum Relationship Weight",
            0.0, 1.0, 0.0, 0.1
        )
    
    with col3:
        layout_type = st.selectbox(
            "Layout Algorithm",
            ["force", "circular", "hierarchical"]
        )
    
    # Create graph data
    nodes, edges = create_graph_data(filter_types, min_weight)
    
    # Graph configuration
    config = Config(
        width=800,
        height=600,
        directed=True,
        physics=True,
        hierarchical=(layout_type == "hierarchical"),
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6"
    )
    
    # Render graph
    agraph(
        nodes=nodes,
        edges=edges,
        config=config
    )
    
    # Create NetworkX graph for analysis
    G = create_networkx_graph(nodes, edges)
    
    # Graph metrics
    if st.checkbox("Show Graph Metrics"):
        st.markdown("#### Graph Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nodes", G.number_of_nodes())
            st.metric("Edges", G.number_of_edges())
        
        with col2:
            st.metric("Density", f"{nx.density(G):.3f}")
            st.metric("Average Degree", f"{sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
        
        with col3:
            if nx.is_connected(G):
                st.metric("Average Path Length", f"{nx.average_shortest_path_length(G):.2f}")
            st.metric("Clustering Coefficient", f"{nx.average_clustering(G):.3f}")


def render_object_details():
    """Render details of selected object."""
    if st.session_state.current_object:
        obj = st.session_state.current_object
        
        st.markdown(f"### {obj['type']} Details")
        
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Information")
            st.write(f"**ID:** {obj['id']}")
            st.write(f"**Type:** {obj['type']}")
            st.write(f"**Created:** {obj['created_at']}")
        
        with col2:
            st.markdown("#### Properties")
            for key, value in obj["properties"].items():
                st.write(f"**{key}:** {value}")
        
        # Relationships
        st.markdown("#### Relationships")
        
        tab1, tab2, tab3 = st.tabs(["Outgoing", "Incoming", "Network Analysis"])
        
        with tab1:
            outgoing = repo.get_linked_objects(obj["id"], direction="out")
            if outgoing:
                for link in outgoing:
                    st.write(
                        f"→ {link['relationship']['type']} → "
                        f"{link['object']['type']}: {link['object'].get('name', 'Unnamed')}"
                    )
                    
                    # Show relationship properties
                    with st.expander("Relationship Details"):
                        st.json(link["relationship"])
            else:
                st.info("No outgoing relationships")
        
        with tab2:
            incoming = repo.get_linked_objects(obj["id"], direction="in")
            if incoming:
                for link in incoming:
                    st.write(
                        f"← {link['relationship']['type']} ← "
                        f"{link['object']['type']}: {link['object'].get('name', 'Unnamed')}"
                    )
                    
                    # Show relationship properties
                    with st.expander("Relationship Details"):
                        st.json(link["relationship"])
            else:
                st.info("No incoming relationships")
        
        with tab3:
            # Create local network
            local_network = nx.ego_graph(
                create_networkx_graph(*create_graph_data()),
                str(obj["id"]),
                radius=2
            )
            
            st.markdown("##### Local Network Metrics")
            
            # Calculate centrality metrics
            degree_cent = centrality.degree_centrality(local_network)
            between_cent = centrality.betweenness_centrality(local_network)
            close_cent = centrality.closeness_centrality(local_network)
            
            metrics_df = pd.DataFrame({
                "Degree Centrality": degree_cent,
                "Betweenness Centrality": between_cent,
                "Closeness Centrality": close_cent
            }).round(3)
            
            st.dataframe(metrics_df)
            
            # Visualize local network
            fig = go.Figure(data=[
                go.Scatter(
                    x=list(range(len(metrics_df))),
                    y=metrics_df[col],
                    name=col,
                    mode="lines+markers"
                ) for col in metrics_df.columns
            ])
            
            fig.update_layout(
                title="Centrality Metrics",
                xaxis_title="Node Index",
                yaxis_title="Centrality Value"
            )
            
            st.plotly_chart(fig, use_container_width=True)


def render_relationship_analysis():
    """Render relationship analysis tools."""
    st.markdown("### 🔍 Relationship Analysis")
    
    # Analysis type selector
    analysis_type = st.radio(
        "Analysis Type",
        ["Type-based Analysis", "Community Detection", "Path Analysis"],
        horizontal=True
    )
    
    if analysis_type == "Type-based Analysis":
        # Select objects to analyze
        col1, col2 = st.columns(2)
        
        with col1:
            source_type = st.selectbox(
                "Source Object Type",
                ["Customer", "Order", "Product"]
            )
        
        with col2:
            target_type = st.selectbox(
                "Target Object Type",
                ["Customer", "Order", "Product"]
            )
        
        if st.button("Analyze Relationships"):
            # Get objects of selected types
            source_objects = repo.search_objects(obj_type=source_type)
            target_objects = repo.search_objects(obj_type=target_type)
            
            if not source_objects or not target_objects:
                st.warning("Not enough data for analysis")
                return
            
            # Create network analysis
            G = nx.DiGraph()
            
            for source in source_objects:
                for target in target_objects:
                    links = repo.get_linked_objects(
                        source["id"],
                        target_id=target["id"]
                    )
                    if links:
                        G.add_edge(
                            str(source["id"]),
                            str(target["id"]),
                            weight=len(links)
                        )
            
            # Calculate metrics
            st.markdown("#### Network Metrics")
            
            metrics = {
                "Total Relationships": G.number_of_edges(),
                "Average Degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
                "Density": nx.density(G)
            }
            
            col1, col2, col3 = st.columns(3)
            for (name, value), col in zip(metrics.items(), [col1, col2, col3]):
                with col:
                    st.metric(name, f"{value:.2f}")
            
            # Visualize relationship distribution
            degrees = [d for _, d in G.degree()]
            
            fig = go.Figure(data=[
                go.Histogram(x=degrees, nbinsx=10)
            ])
            fig.update_layout(
                title="Relationship Distribution",
                xaxis_title="Number of Relationships",
                yaxis_title="Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Community Detection":
        # Get full graph
        G = create_networkx_graph(*create_graph_data())
        
        # Detect communities
        communities = community.best_partition(G)
        
        # Analyze communities
        community_sizes = pd.Series(communities).value_counts()
        
        st.markdown("#### Community Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Number of Communities", len(community_sizes))
            st.metric("Modularity", community.modularity(communities, G))
        
        with col2:
            st.metric("Largest Community Size", community_sizes.max())
            st.metric("Average Community Size", f"{community_sizes.mean():.1f}")
        
        # Visualize community sizes
        fig = go.Figure(data=[
            go.Bar(
                x=community_sizes.index,
                y=community_sizes.values,
                name="Community Sizes"
            )
        ])
        
        fig.update_layout(
            title="Community Size Distribution",
            xaxis_title="Community ID",
            yaxis_title="Number of Nodes"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:  # Path Analysis
        st.markdown("#### Path Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_id = st.text_input("Source Object ID")
        
        with col2:
            target_id = st.text_input("Target Object ID")
        
        if source_id and target_id and st.button("Find Paths"):
            G = create_networkx_graph(*create_graph_data())
            
            try:
                # Find all simple paths
                paths = list(nx.all_simple_paths(G, source_id, target_id, cutoff=4))
                
                if paths:
                    st.markdown(f"Found {len(paths)} path(s)")
                    
                    for i, path in enumerate(paths, 1):
                        st.markdown(f"**Path {i}:**")
                        
                        # Create path visualization
                        path_edges = list(zip(path[:-1], path[1:]))
                        edge_trace = []
                        node_trace = []
                        
                        for node in path:
                            node_trace.append(
                                go.Scatter(
                                    x=[0],
                                    y=[0],
                                    mode="markers+text",
                                    text=[G.nodes[node]["label"]],
                                    marker=dict(size=20, color=G.nodes[node]["color"])
                                )
                            )
                        
                        for edge in path_edges:
                            edge_trace.append(
                                go.Scatter(
                                    x=[0, 1],
                                    y=[0, 0],
                                    mode="lines+text",
                                    text=[G.edges[edge]["label"]],
                                    line=dict(width=2)
                                )
                            )
                        
                        fig = go.Figure(data=node_trace + edge_trace)
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No paths found between the selected objects")
            
            except nx.NetworkXNoPath:
                st.error("No path exists between the selected objects")


def render_page():
    """Render the ontology viewer page."""
    st.title("🕸️ Ontology Viewer")
    
    st.markdown("""
        Explore and analyze the relationships between objects in your ontology.
        Visualize the network structure and discover patterns.
    """)
    
    # Main layout
    tab1, tab2 = st.tabs(["Graph View", "Relationship Analysis"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            render_graph_view()
        
        with col2:
            render_object_details()
    
    with tab2:
        render_relationship_analysis() 