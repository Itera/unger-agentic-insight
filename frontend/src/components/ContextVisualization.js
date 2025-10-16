import React, { useState } from 'react';
import styled from 'styled-components';
import { Eye, EyeOff, Target, MapPin, Database, Activity, Settings, Zap, Box, ChevronDown, ChevronUp } from 'lucide-react';

const ContextContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid rgba(102, 126, 234, 0.2);
  backdrop-filter: blur(10px);
`;

const ContextHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${props => props.expanded ? '1rem' : '0'};
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s ease;

  &:hover {
    background: rgba(102, 126, 234, 0.05);
  }
`;

const ContextTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #333;
`;

const ContextSummary = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: #666;
`;

const ExpandButton = styled.button`
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: background 0.2s ease;

  &:hover {
    background: rgba(102, 126, 234, 0.1);
  }
`;

const ContextDetails = styled.div`
  animation: fadeIn 0.3s ease;

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const ScopeSection = styled.div`
  margin-bottom: 1rem;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionTitle = styled.h4`
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const NodesList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.5rem;
`;

const NodeItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.85rem;
`;

const NodeIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  color: white;
  flex-shrink: 0;
  background: ${props => {
    switch(props.type) {
      case 'AssetArea': return 'linear-gradient(135deg, #a29bfe, #6c5ce7)';
      case 'Equipment': return 'linear-gradient(135deg, #ff6b6b, #ee5a24)';
      case 'Sensor': return 'linear-gradient(135deg, #4ecdc4, #44a08d)';
      default: return 'linear-gradient(135deg, #667eea, #764ba2)';
    }
  }};
`;

const NodeName = styled.span`
  font-weight: 500;
  color: #333;
  flex: 1;
`;

const NodeType = styled.span`
  color: #666;
  font-size: 0.75rem;
  background: #e9ecef;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 1.25rem;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 0.25rem;
`;

const StatLabel = styled.div`
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ModeIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: ${props => props.scoped ? '#667eea' : '#666'};
  font-weight: ${props => props.scoped ? '600' : 'normal'};
`;

const ContextVisualization = ({ 
  context, 
  contextData, 
  mode = 'scoped', 
  isVisible = true 
}) => {
  const [expanded, setExpanded] = useState(false);

  if (!isVisible) return null;

  const getNodeIcon = (labels) => {
    if (!labels || !Array.isArray(labels)) return <Box size={14} />;
    
    const primaryType = labels[0];
    switch (primaryType) {
      case 'AssetArea': return <MapPin size={14} />;
      case 'Equipment': return <Settings size={14} />;
      case 'Sensor': return <Activity size={14} />;
      default: return <Box size={14} />;
    }
  };

  const getContextSummary = () => {
    if (mode === 'global') {
      return 'AI has access to all available data sources';
    }
    
    if (!context || !contextData) {
      return 'No specific context - using global scope';
    }

    const totalNodes = contextData.total_nodes || 0;
    const centralNode = contextData.central_node?.name || 'Unknown';
    
    return `Focused on ${centralNode} with ${totalNodes} connected entities`;
  };

  const renderCentralNode = () => {
    if (!contextData?.central_node) return null;

    const node = contextData.central_node;
    const labels = node.labels || [];
    
    return (
      <ScopeSection>
        <SectionTitle>
          <Target size={16} />
          Central Focus
        </SectionTitle>
        <NodeItem>
          <NodeIcon type={labels[0]}>
            {getNodeIcon(labels)}
          </NodeIcon>
          <NodeName>{node.name}</NodeName>
          <NodeType>{labels.join(', ')}</NodeType>
        </NodeItem>
      </ScopeSection>
    );
  };

  const renderConnectedNodes = () => {
    if (!contextData?.connected_nodes || contextData.connected_nodes.length === 0) {
      return null;
    }

    // Group nodes by type
    const nodesByType = contextData.connected_nodes.reduce((acc, node) => {
      const type = node.labels?.[0] || 'Unknown';
      if (!acc[type]) acc[type] = [];
      acc[type].push(node);
      return acc;
    }, {});

    return (
      <ScopeSection>
        <SectionTitle>
          <Database size={16} />
          Connected Entities ({contextData.connected_nodes.length})
        </SectionTitle>
        
        {Object.entries(nodesByType).map(([type, nodes]) => (
          <div key={type} style={{ marginBottom: '1rem' }}>
            <div style={{ 
              fontSize: '0.8rem', 
              color: '#666', 
              marginBottom: '0.5rem',
              fontWeight: '500'
            }}>
              {type} ({nodes.length})
            </div>
            <NodesList>
              {nodes.slice(0, 6).map((node, index) => (
                <NodeItem key={index}>
                  <NodeIcon type={type}>
                    {getNodeIcon(node.labels)}
                  </NodeIcon>
                  <NodeName>{node.name || 'Unnamed'}</NodeName>
                  <NodeType>{type}</NodeType>
                </NodeItem>
              ))}
            </NodesList>
            {nodes.length > 6 && (
              <div style={{ 
                fontSize: '0.75rem', 
                color: '#666', 
                marginTop: '0.5rem',
                textAlign: 'center'
              }}>
                ... and {nodes.length - 6} more {type.toLowerCase()} entities
              </div>
            )}
          </div>
        ))}
      </ScopeSection>
    );
  };

  const renderStats = () => {
    if (!contextData) return null;

    return (
      <StatsGrid>
        <StatItem>
          <StatValue>{contextData.total_nodes || 0}</StatValue>
          <StatLabel>Total Nodes</StatLabel>
        </StatItem>
        
        <StatItem>
          <StatValue>{context?.scopeDepth || 2}</StatValue>
          <StatLabel>Scope Depth</StatLabel>
        </StatItem>
        
        <StatItem>
          <StatValue>{contextData.connected_nodes?.length || 0}</StatValue>
          <StatLabel>Connections</StatLabel>
        </StatItem>
        
        <StatItem>
          <StatValue>{mode === 'scoped' ? 'Focused' : 'Global'}</StatValue>
          <StatLabel>AI Mode</StatLabel>
        </StatItem>
      </StatsGrid>
    );
  };

  return (
    <ContextContainer>
      <ContextHeader 
        expanded={expanded}
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <ContextTitle>
            <Eye size={16} />
            AI Context Scope
          </ContextTitle>
          <ContextSummary>
            <ModeIndicator scoped={mode === 'scoped'}>
              {mode === 'scoped' ? <Target size={14} /> : <MapPin size={14} />}
              {getContextSummary()}
            </ModeIndicator>
          </ContextSummary>
        </div>
        
        <ExpandButton onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </ExpandButton>
      </ContextHeader>

      {expanded && (
        <ContextDetails>
          {mode === 'scoped' && contextData ? (
            <>
              {renderCentralNode()}
              {renderConnectedNodes()}
              {renderStats()}
            </>
          ) : (
            <div style={{ 
              textAlign: 'center', 
              padding: '1rem',
              color: '#666',
              fontSize: '0.9rem'
            }}>
              {mode === 'global' ? 
                'AI has access to all available data sources without specific contextual focus.' :
                'No specific navigation context set. Switch to an area or entity view to enable scoped AI responses.'
              }
            </div>
          )}
        </ContextDetails>
      )}
    </ContextContainer>
  );
};

export default ContextVisualization;