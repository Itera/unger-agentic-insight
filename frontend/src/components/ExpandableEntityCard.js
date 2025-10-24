import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Settings, Activity, Cpu, Zap, Database, Play, Box, Tag, AlertCircle, MapPin } from 'lucide-react';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const getEntityIconBg = (type) => {
  switch(type) {
    case 'Equipment': return 'bg-[#F5A676]';
    case 'Sensor': return 'bg-emerald-700';
    case 'Equipment Sensors': return 'bg-emerald-600';
    case 'Area Sensors': return 'bg-[#F5A676]';
    case 'AssetArea': return 'bg-emerald-800';
    case 'Tank': return 'bg-cyan-600';
    case 'ProcessStep': return 'bg-green-600';
    default: return 'bg-emerald-700';
  }
};

const ExpandableEntityCard = ({ entity, entityType, onNavigate }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getEntityIcon = (type) => {
    switch (type) {
      case 'Equipment': return <Settings size={16} />;
      case 'Sensor': return <Activity size={16} />;
      case 'Equipment Sensors': return <Cpu size={16} />;
      case 'Area Sensors': return <Zap size={16} />;
      case 'AssetArea': return <MapPin size={16} />;
      case 'Tank': return <Database size={16} />;
      case 'ProcessStep': return <Play size={16} />;
      default: return <Box size={16} />;
    }
  };

  const getEntityName = (entity) => {
    return entity.name || 
           entity.properties?.equipment_name || 
           entity.properties?.tag || 
           entity.properties?.name ||
           entity.description ||
           entity.id || 
           'Unknown';
  };

  const getEntityDescription = (entity) => {
    let description = entity.description || entity.properties?.description;
    
    // Add unit information for sensors
    if (entityType === 'Sensor' && entity.properties?.unit) {
      description = `${description || 'Sensor'} (${entity.properties.unit})`;
    }
    
    // Add equipment type for equipment
    if (entityType === 'Equipment' && entity.properties?.equipment_type) {
      description = `${description || 'Equipment'} - ${entity.properties.equipment_type}`;
    }
    
    return description || `${entityType} entity`;
  };

  const formatPropertyValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      // Handle Neo4j DateTime objects
      if (value._DateTime__date) {
        const date = value._DateTime__date;
        const time = value._DateTime__time;
        return `${date._Date__year}-${String(date._Date__month).padStart(2, '0')}-${String(date._Date__day).padStart(2, '0')} ${String(time._Time__hour).padStart(2, '0')}:${String(time._Time__minute).padStart(2, '0')}`;
      }
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const handleCardClick = (e) => {
    e.preventDefault();
    setIsExpanded(!isExpanded);
  };

  const handleNavigateClick = (e) => {
    e.stopPropagation();
    if (onNavigate) {
      const entityId = entity.id || 
                       entity.name || 
                       entity.equipment_id || 
                       entity.tag ||
                       entity.properties?.equipment_id ||
                       entity.properties?.equipment_name ||
                       entity.properties?.tag ||
                       entity.properties?.name;
      
      if (entityId) {
        onNavigate(entity, entityType, entityId);
      }
    }
  };

  return (
    <Card className="cursor-pointer transition-all hover:bg-stone-50 hover:shadow-md hover:-translate-y-0.5 hover:border-emerald-700" onClick={handleCardClick}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3 w-full">
          <div className={`flex items-center justify-center w-7 h-7 rounded-md text-white shrink-0 ${getEntityIconBg(entityType)}`}>
            {getEntityIcon(entityType)}
          </div>
          <div className="flex-1 flex flex-col gap-1">
            <h3 className="text-base font-semibold text-stone-900 m-0 leading-tight">{getEntityName(entity)}</h3>
            <p className="text-stone-500 text-sm leading-snug m-0">{getEntityDescription(entity)}</p>
          </div>
          <button 
            className="bg-transparent border-none text-stone-500 cursor-pointer p-1 rounded flex items-center justify-center transition-all hover:bg-emerald-700/10 hover:text-emerald-700"
            onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="mt-4 pt-4 border-t border-stone-200 animate-in fade-in-50 slide-in-from-top-2 duration-300">
          {/* Key Information for Sensors and Equipment */}
          {(entityType === 'Sensor' || entityType === 'Equipment') && entity.properties && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-stone-900 mb-2 flex items-center gap-2">
                <Activity size={14} />
                Key Information
              </h4>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-2">
                {/* Sensor-specific key info */}
                {entityType === 'Sensor' && (
                  <>
                    {entity.properties.unit && (
                      <div className="flex flex-col bg-stone-100 p-2 rounded-md">
                        <span className="text-xs text-stone-500 font-medium capitalize">Unit</span>
                        <span className="text-sm text-stone-900 font-semibold text-blue-600">{entity.properties.unit}</span>
                      </div>
                    )}
                    {entity.properties.sensor_type_code && (
                      <div className="flex flex-col bg-stone-100 p-2 rounded-md">
                        <span className="text-xs text-stone-500 font-medium capitalize">Type</span>
                        <span className="text-sm text-stone-900">{entity.properties.sensor_type_code}</span>
                      </div>
                    )}
                    {entity.properties.classification && (
                      <div className="flex flex-col bg-stone-100 p-2 rounded-md">
                        <span className="text-xs text-stone-500 font-medium capitalize">Classification</span>
                        <span className="text-sm text-stone-900">{entity.properties.classification}</span>
                      </div>
                    )}
                  </>
                )}
                {/* Equipment-specific key info */}
                {entityType === 'Equipment' && (
                  <>
                    {entity.properties.equipment_type && (
                      <div className="flex flex-col bg-stone-100 p-2 rounded-md">
                        <span className="text-xs text-stone-500 font-medium capitalize">Equipment Type</span>
                        <span className="text-sm text-stone-900 font-semibold text-red-600">{entity.properties.equipment_type}</span>
                      </div>
                    )}
                    {entity.properties.sensor_count && (
                      <div className="flex flex-col bg-stone-100 p-2 rounded-md">
                        <span className="text-xs text-stone-500 font-medium capitalize">Sensor Count</span>
                        <span className="text-sm text-stone-900 font-semibold text-emerald-600">{entity.properties.sensor_count}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
              {/* Source tags for equipment */}
              {entityType === 'Equipment' && entity.properties.source_tags && (
                <div className="mt-3">
                  <span className="text-xs text-stone-500 font-medium capitalize">Source Tags</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {entity.properties.source_tags.split(',').map((tag, index) => (
                      <Badge key={index} variant="secondary">
                        {tag.trim()}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* All Entity Properties */}
          {entity.properties && Object.keys(entity.properties).length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-stone-900 mb-2 flex items-center gap-2">
                <Tag size={14} />
                All Properties
              </h4>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-2">
                {Object.entries(entity.properties).map(([key, value]) => (
                  <div key={key} className="flex flex-col bg-stone-100 p-2 rounded-md">
                    <span className="text-xs text-stone-500 font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="text-sm text-stone-900 break-words">{formatPropertyValue(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entity Labels */}
          {entity.labels && entity.labels.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-stone-900 mb-2 flex items-center gap-2">
                <AlertCircle size={14} />
                Labels
              </h4>
              <div className="flex flex-wrap gap-2">
                {entity.labels.map((label, index) => (
                  <Badge key={index} variant="secondary">{label}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-4">
            <Button onClick={handleNavigateClick} size="sm">
              View Details
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export default ExpandableEntityCard;