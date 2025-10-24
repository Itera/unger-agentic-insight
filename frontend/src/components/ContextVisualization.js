import React, { useState } from 'react';
import { Eye, Target, MapPin, Database, Activity, Settings, Box, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from './ui/badge';

const getNodeIconBg = (type) => {
  switch(type) {
    case 'AssetArea': return 'bg-purple-600';
    case 'Equipment': return 'bg-red-600';
    case 'Sensor': return 'bg-teal-600';
    default: return 'bg-indigo-600';
  }
};

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
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-stone-900 mb-2 flex items-center gap-2">
          <Target size={16} />
          Central Focus
        </h4>
        <div className="flex items-center gap-2 p-2 bg-stone-50 rounded-md text-sm">
          <div className={`flex items-center justify-center w-5 h-5 rounded text-white shrink-0 ${getNodeIconBg(labels[0])}`}>
            {getNodeIcon(labels)}
          </div>
          <span className="font-medium text-stone-900 flex-1">{node.name}</span>
          <Badge variant="secondary" className="text-xs">{labels.join(', ')}</Badge>
        </div>
      </div>
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
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-stone-900 mb-2 flex items-center gap-2">
          <Database size={16} />
          Connected Entities ({contextData.connected_nodes.length})
        </h4>
        
        {Object.entries(nodesByType).map(([type, nodes]) => (
          <div key={type} className="mb-4">
            <div className="text-xs text-stone-600 mb-2 font-medium">
              {type} ({nodes.length})
            </div>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-2">
              {nodes.slice(0, 6).map((node, index) => {
                const getDisplayName = (node) => {
                  return node.name || node.properties?.equipment_name || node.properties?.tag || 'Unnamed';
                };
                
                const getDisplayInfo = (node) => {
                  if (type === 'Sensor' && node.properties?.unit) {
                    return `${type} (${node.properties.unit})`;
                  }
                  if (type === 'Equipment' && node.properties?.equipment_type) {
                    return `${node.properties.equipment_type}`;
                  }
                  return type;
                };
                
                return (
                  <div key={index} className="flex items-center gap-2 p-2 bg-stone-50 rounded-md text-sm">
                    <div className={`flex items-center justify-center w-5 h-5 rounded text-white shrink-0 ${getNodeIconBg(type)}`}>
                      {getNodeIcon(node.labels)}
                    </div>
                    <span className="font-medium text-stone-900 flex-1">{getDisplayName(node)}</span>
                    <Badge variant="secondary" className="text-xs">{getDisplayInfo(node)}</Badge>
                  </div>
                );
              })}
            </div>
            {nodes.length > 6 && (
              <div className="text-xs text-stone-600 mt-2 text-center">
                ... and {nodes.length - 6} more {type.toLowerCase()} entities
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderStats = () => {
    if (!contextData) return null;

    return (
      <div className="grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-3 mt-4 p-4 bg-indigo-50 rounded-lg">
        <div className="text-center">
          <div className="text-xl font-bold text-indigo-600 mb-1">{contextData.total_nodes || 0}</div>
          <div className="text-xs text-stone-600 uppercase tracking-wide">Total Nodes</div>
        </div>
        
        <div className="text-center">
          <div className="text-xl font-bold text-indigo-600 mb-1">{context?.scopeDepth || 2}</div>
          <div className="text-xs text-stone-600 uppercase tracking-wide">Scope Depth</div>
        </div>
        
        <div className="text-center">
          <div className="text-xl font-bold text-indigo-600 mb-1">{contextData.connected_nodes?.length || 0}</div>
          <div className="text-xs text-stone-600 uppercase tracking-wide">Connections</div>
        </div>
        
        <div className="text-center">
          <div className="text-xl font-bold text-indigo-600 mb-1">{mode === 'scoped' ? 'Focused' : 'Global'}</div>
          <div className="text-xs text-stone-600 uppercase tracking-wide">AI Mode</div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/95 backdrop-blur-md rounded-xl p-4 mb-4 border border-indigo-200">
      <div 
        className={`flex items-center justify-between ${expanded ? 'mb-4' : ''} cursor-pointer p-2 rounded-lg transition-colors hover:bg-indigo-50`}
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <div className="flex items-center gap-2 font-semibold text-stone-900">
            <Eye size={16} />
            AI Context Scope
          </div>
          <div className="flex items-center gap-3 text-sm text-stone-600 mt-1">
            <div className={`flex items-center gap-2 ${mode === 'scoped' ? 'text-indigo-600 font-semibold' : ''}`}>
              {mode === 'scoped' ? <Target size={14} /> : <MapPin size={14} />}
              {getContextSummary()}
            </div>
          </div>
        </div>
        
        <button 
          className="bg-transparent border-none text-indigo-600 cursor-pointer p-1 rounded flex items-center transition-colors hover:bg-indigo-100"
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="animate-in fade-in-50 slide-in-from-top-2 duration-300">
          {mode === 'scoped' && contextData ? (
            <>
              {renderCentralNode()}
              {renderConnectedNodes()}
              {renderStats()}
            </>
          ) : (
            <div className="text-center p-4 text-stone-600 text-sm">
              {mode === 'global' ? 
                'AI has access to all available data sources without specific contextual focus.' :
                'No specific navigation context set. Switch to an area or entity view to enable scoped AI responses.'
              }
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContextVisualization;
