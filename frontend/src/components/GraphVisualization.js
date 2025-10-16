import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useNavigationContext } from '../contexts/NavigationContext';
import './GraphVisualization.css';

/**
 * GraphVisualization Component
 * 
 * Implements Epic 4 user stories:
 * - US-014: Visual representation of current scope in the graph
 * - US-015: Discover related equipment through graph visualization  
 * - US-016: Clear indication of orphaned sensors in visualization
 */
const GraphVisualization = ({ 
  width = 800, 
  height = 600, 
  className = '',
  enableNavigation = true,
  showLegend = true 
}) => {
  const { currentContext, setAreaContext, setEntityContext, getChatContext } = useNavigationContext();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fgRef = useRef();

  // Node type configurations for styling and behavior
  const nodeConfig = useMemo(() => ({
    Plant: {
      color: '#2563eb',
      size: 12,
      icon: '🏭',
      strokeColor: '#1d4ed8',
      strokeWidth: 2
    },
    AssetArea: {
      color: '#059669',
      size: 10,
      icon: '🏢',
      strokeColor: '#047857',
      strokeWidth: 2
    },
    Equipment: {
      color: '#dc2626',
      size: 8,
      icon: '⚙️',
      strokeColor: '#b91c1c',
      strokeWidth: 1.5
    },
    Sensor: {
      color: '#7c3aed',
      size: 6,
      icon: '📡',
      strokeColor: '#6d28d9',
      strokeWidth: 1
    },
    OrphanedSensor: {
      color: '#f59e0b',
      size: 6,
      icon: '📡',
      strokeColor: '#d97706',
      strokeWidth: 2,
      strokeDasharray: '3,3'
    }
  }), []);

  // Fetch contextual graph data from backend
  const fetchGraphData = useCallback(async (context) => {
    if (!context || !context.nodeType || !context.nodeName) {
      setGraphData({ nodes: [], links: [] });
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/graph/context/${context.nodeType}/${encodeURIComponent(context.nodeName)}?max_depth=${context.scopeDepth || 2}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch graph data: ${response.statusText}`);
      }

      const data = await response.json();
      const transformedData = transformToGraphData(data, context);
      setGraphData(transformedData);
      
    } catch (err) {
      console.error('Error fetching graph data:', err);
      setError(err.message);
      setGraphData({ nodes: [], links: [] });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Transform backend context data to force-graph format
  const transformToGraphData = (contextData, currentContext) => {
    const nodes = [];
    const links = [];
    const nodeMap = new Map();

    // Add central node
    if (contextData.central_node) {
      const centralNode = {
        id: contextData.central_node.name,
        name: contextData.central_node.name,
        type: contextData.central_node.labels?.[0] || 'Unknown',
        properties: contextData.central_node.properties || {},
        isCentral: true,
        depth: 0
      };
      nodes.push(centralNode);
      nodeMap.set(centralNode.id, centralNode);
    }

    // Add connected nodes and create links
    if (contextData.connected_nodes) {
      contextData.connected_nodes.forEach(node => {
        const nodeType = node.labels?.[0] || 'Unknown';
        const nodeId = node.name || `unnamed_${Math.random()}`;
        
        // Determine if sensor is orphaned (US-016)
        const isOrphanedSensor = nodeType === 'Sensor' && 
          (!node.relationship_path || node.relationship_path.length === 1) &&
          node.relationship_path?.[0] === 'HAS_SENSOR';

        const graphNode = {
          id: nodeId,
          name: node.name || 'Unnamed',
          type: isOrphanedSensor ? 'OrphanedSensor' : nodeType,
          properties: node.properties || {},
          depth: node.depth || 1,
          relationshipPath: node.relationship_path || [],
          isOrphaned: isOrphanedSensor
        };

        nodes.push(graphNode);
        nodeMap.set(nodeId, graphNode);

        // Create link to central node (simplified - in reality you'd track exact relationships)
        if (contextData.central_node) {
          links.push({
            source: contextData.central_node.name,
            target: nodeId,
            relationship: node.relationship_path?.[0] || 'CONNECTED',
            depth: node.depth || 1
          });
        }
      });
    }

    return { nodes, links };
  };

  // Handle node click for navigation (US-015)
  const handleNodeClick = useCallback((node) => {
    if (!enableNavigation) return;

    // Navigate to the clicked node's context
    if (node.type === 'AssetArea' || node.type === 'Area') {
      setAreaContext(node.name, { id: node.id, ...node.properties });
    } else if (node.type === 'Equipment' || node.type === 'Sensor' || node.type === 'OrphanedSensor') {
      const entityType = node.type === 'OrphanedSensor' ? 'Sensor' : node.type;
      setEntityContext(entityType, node.name, { id: node.id, ...node.properties });
    }
  }, [enableNavigation, setAreaContext, setEntityContext]);

  // Node styling function
  const getNodeColor = useCallback((node) => {
    const config = nodeConfig[node.type] || nodeConfig.Sensor;
    return node.isCentral ? '#ef4444' : config.color;
  }, [nodeConfig]);

  const getNodeSize = useCallback((node) => {
    const baseSize = nodeConfig[node.type]?.size || 6;
    return node.isCentral ? baseSize * 1.5 : baseSize;
  }, [nodeConfig]);

  // Custom node rendering with icons and labels
  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const label = node.name;
    const config = nodeConfig[node.type] || nodeConfig.Sensor;
    const size = getNodeSize(node);
    
    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
    ctx.fillStyle = getNodeColor(node);
    ctx.fill();

    // Draw border
    ctx.strokeStyle = config.strokeColor;
    ctx.lineWidth = config.strokeWidth / globalScale;
    if (node.type === 'OrphanedSensor') {
      ctx.setLineDash([3, 3]);
    } else {
      ctx.setLineDash([]);
    }
    ctx.stroke();

    // Draw label
    if (globalScale > 0.5) {
      const fontSize = Math.max(8, 12 / globalScale);
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#374151';
      ctx.fillText(label, node.x, node.y + size + fontSize);
    }

    // Draw central node indicator
    if (node.isCentral && globalScale > 0.3) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 3, 0, 2 * Math.PI, false);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2 / globalScale;
      ctx.setLineDash([2, 2]);
      ctx.stroke();
    }
  }, [nodeConfig, getNodeColor, getNodeSize]);

  // Link styling
  const getLinkColor = useCallback((link) => {
    const alpha = Math.max(0.3, 1 - (link.depth || 1) * 0.2);
    return `rgba(107, 114, 128, ${alpha})`;
  }, []);

  // Load graph data when context changes
  useEffect(() => {
    const context = getChatContext();
    if (context && context.nodeType && context.nodeName) {
      fetchGraphData(context);
    } else {
      setGraphData({ nodes: [], links: [] });
    }
  }, [getChatContext, fetchGraphData]);

  // Render legend
  const renderLegend = () => {
    if (!showLegend) return null;

    const legendItems = [
      { type: 'Plant', label: 'Plant' },
      { type: 'AssetArea', label: 'Area' },
      { type: 'Equipment', label: 'Equipment' },
      { type: 'Sensor', label: 'Sensor' },
      { type: 'OrphanedSensor', label: 'Orphaned Sensor' }
    ];

    return (
      <div className="graph-legend">
        <h4>Legend</h4>
        {legendItems.map(item => {
          const config = nodeConfig[item.type];
          return (
            <div key={item.type} className="legend-item">
              <div 
                className="legend-dot"
                style={{ 
                  backgroundColor: config.color,
                  border: `2px solid ${config.strokeColor}`,
                  borderStyle: item.type === 'OrphanedSensor' ? 'dashed' : 'solid'
                }}
              />
              <span>{item.label}</span>
            </div>
          );
        })}
        <div className="legend-item">
          <div className="legend-dot central-indicator" />
          <span>Current Focus</span>
        </div>
      </div>
    );
  };

  if (error) {
    return (
      <div className={`graph-visualization error ${className}`}>
        <div className="error-message">
          <h4>Graph Visualization Error</h4>
          <p>{error}</p>
          <button 
            onClick={() => fetchGraphData(getChatContext())}
            className="retry-button"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`graph-visualization loading ${className}`}>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading graph visualization...</p>
        </div>
      </div>
    );
  }

  if (!currentContext.type) {
    return (
      <div className={`graph-visualization empty ${className}`}>
        <div className="empty-state">
          <h4>No Context Selected</h4>
          <p>Navigate to a plant, area, or equipment to see the graph visualization.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`graph-visualization ${className}`}>
      <div className="graph-header">
        <h3>Graph View: {currentContext.name}</h3>
        <div className="graph-stats">
          <span>{graphData.nodes.length} nodes</span>
          <span>{graphData.links.length} connections</span>
        </div>
      </div>
      
      <div className="graph-container">
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          width={width}
          height={height}
          nodeCanvasObject={nodeCanvasObject}
          nodePointerAreaPaint={nodeCanvasObject}
          onNodeClick={handleNodeClick}
          linkColor={getLinkColor}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleWidth={1}
          cooldownTicks={100}
          onEngineStop={() => fgRef.current?.zoomToFit(200, 50)}
          enableNodeDrag={true}
          enablePanInteraction={true}
          enableZoomInteraction={true}
        />
        
        {renderLegend()}
      </div>
      
      {graphData.nodes.length > 0 && (
        <div className="graph-footer">
          <p className="graph-hint">
            💡 Click on any node to navigate and explore its connections
          </p>
        </div>
      )}
    </div>
  );
};

export default GraphVisualization;