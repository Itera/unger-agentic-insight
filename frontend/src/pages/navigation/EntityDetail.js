import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Activity, Settings, Database, Play, Box } from 'lucide-react';
import Breadcrumb from '../../components/Breadcrumb';
import WorkOrdersSection from '../../components/WorkOrdersSection';
import { Button } from '../../components/ui/button';
import { Card, CardHeader, CardContent, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';

const getEntityIconBg = (type) => {
  switch(type) {
    case 'Equipment': return 'bg-orange-600'; // Orange for equipment
    case 'Sensor': return 'bg-emerald-700'; // Green for sensors
    case 'Tank': return 'bg-cyan-600'; // Cyan for tanks
    case 'ProcessStep': return 'bg-green-600'; // Green for process steps
    case 'AssetArea': return 'bg-purple-600'; // Purple for areas
    default: return 'bg-stone-600'; // Grey default
  }
};

const EntityDetail = () => {
  const { entityType, entityId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [entityData, setEntityData] = useState(null);
  const [connectedEntities, setConnectedEntities] = useState({});
  const [stats, setStats] = useState({});
  const [plantName, setPlantName] = useState(null);
  const [areaName, setAreaName] = useState(null);

  useEffect(() => {
    const fetchEntityDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch entity details and connected entities
        const [entityResponse, connectedResponse] = await Promise.all([
          fetch(`/api/entities/${entityType}/${encodeURIComponent(entityId)}`),
          fetch(`/api/entities/${entityType}/${encodeURIComponent(entityId)}/connected`)
        ]);

        if (!entityResponse.ok || !connectedResponse.ok) {
          throw new Error('Failed to fetch entity data');
        }

        const entity = await entityResponse.json();
        const connected = await connectedResponse.json();
        
        setEntityData(entity);
        setConnectedEntities(connected);
        
        // Extract context from entity properties
        if (entity.properties?.plant_name) {
          setPlantName(entity.properties.plant_name);
        }
        if (entity.properties?.area_code) {
          setAreaName(entity.properties.area_code);
        }
        
        // Calculate stats
        const totalConnected = Object.values(connected).reduce((sum, arr) => sum + arr.length, 0);
        const entityCounts = Object.entries(connected).reduce((acc, [type, items]) => {
          acc[type] = items.length;
          return acc;
        }, {});
        
        setStats({
          totalConnected,
          ...entityCounts
        });
        
      } catch (err) {
        console.error('Error fetching entity details:', err);
        setError('Failed to load entity details');
      } finally {
        setLoading(false);
      }
    };

    if (entityType && entityId) {
      fetchEntityDetail();
    }
  }, [entityType, entityId]);

  const getEntityIcon = (type) => {
    switch (type) {
      case 'Equipment': return <Settings />;
      case 'Sensor': return <Activity />;
      case 'Tank': return <Database />;
      case 'ProcessStep': return <Play />;
      case 'AssetArea': return <MapPin />;
      default: return <Box />;
    }
  };

  const handleEntityClick = (entity, type) => {
    console.log(`Clicked ${type}:`, entity);
    // Navigate to the clicked entity's detail page  
    // Try multiple possible identifiers from both top level and properties
    const entityId = entity.id || 
                     entity.name || 
                     entity.equipment_id || 
                     entity.tag ||
                     entity.properties?.equipment_id ||
                     entity.properties?.equipment_name ||
                     entity.properties?.tag ||
                     entity.properties?.name;
    
    if (entityId) {
      console.log(`Navigating to: /navigate/entity/${type}/${entityId}`);
      navigate(`/navigate/entity/${type}/${encodeURIComponent(entityId)}`);
    } else {
      console.warn('No valid ID found for entity:', entity);
    }
  };

  const handleBack = () => {
    navigate(-1); // Go back to previous page
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-16 text-stone-700 text-lg">
        <Activity className="animate-spin mr-2" size={24} />
        Loading entity details...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center p-16 text-stone-700 text-center">
        <h2 className="text-xl font-semibold mb-2">Error Loading Entity</h2>
        <p className="mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  // Build breadcrumb items
  const breadcrumbItems = [];
  if (plantName) {
    breadcrumbItems.push({
      label: plantName,
      path: '/navigate',
      isActive: false
    });
  }
  if (areaName) {
    breadcrumbItems.push({
      label: areaName,
      path: `/navigate/area/${encodeURIComponent(areaName)}`,
      isActive: false
    });
  }
  breadcrumbItems.push({
    label: entityData?.properties?.equipment_name || entityData?.properties?.tag || entityId,
    path: `/navigate/entity/${entityType}/${encodeURIComponent(entityId)}`,
    isActive: true
  });

  return (
    <div className="w-full">
      <Breadcrumb items={breadcrumbItems} />
      
      <div className="flex items-center gap-4 mb-8">
        <Button variant="outline" onClick={handleBack} className="gap-2">
          <ArrowLeft size={20} />
          Back
        </Button>
        <div className={`flex items-center justify-center w-10 h-10 rounded-lg text-white ${getEntityIconBg(entityType)}`}>
          {getEntityIcon(entityType)}
        </div>
        <div>
          <h1 className="text-3xl font-bold text-stone-900 tracking-tight">
            {entityData?.name || 
             entityData?.properties?.equipment_name ||
             entityData?.properties?.tag ||
             entityData?.properties?.name ||
             entityId}
          </h1>
          {entityData?.description && (
            <p className="text-stone-500 mt-1">{entityData.description}</p>
          )}
        </div>
      </div>

      <div className="grid gap-6">
        {/* Entity Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Entity Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                <div className="flex justify-between py-2 border-b border-stone-200 last:border-0">
                  <span className="font-medium text-stone-600">Type:</span>
                  <span className="font-mono text-sm bg-stone-100 px-2 py-1 rounded">{entityType}</span>
                </div>
                {entityData?.labels && entityData.labels.length > 0 && (
                  <div className="flex justify-between py-2 border-b border-stone-200 last:border-0">
                    <span className="font-medium text-stone-600">Labels:</span>
                    <span className="font-mono text-sm bg-stone-100 px-2 py-1 rounded">{entityData.labels.join(', ')}</span>
                  </div>
                )}
                {entityData?.id && (
                  <div className="flex justify-between py-2 border-b border-stone-200 last:border-0">
                    <span className="font-medium text-stone-600">ID:</span>
                    <span className="font-mono text-sm bg-stone-100 px-2 py-1 rounded">{entityData.id}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          
          {entityData?.properties && Object.keys(entityData.properties).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 max-h-96 overflow-y-auto">
                  {Object.entries(entityData.properties).map(([key, value]) => (
                    <div key={key} className="flex justify-between py-2 border-b border-stone-200 last:border-0">
                      <span className="font-medium text-stone-600">{key}:</span>
                      <span className="font-mono text-sm bg-stone-100 px-2 py-1 rounded break-all max-w-xs">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Connected Entities Stats */}
        {stats.totalConnected > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card className="bg-primary/10 border-primary/20">
              <CardContent className="pt-6 text-center">
                <div className="text-3xl font-bold text-primary mb-2">{stats.totalConnected || 0}</div>
                <div className="text-sm font-medium text-stone-700">Total Connected Entities</div>
              </CardContent>
            </Card>
            {Object.entries(stats).map(([key, value]) => {
              if (key === 'totalConnected') return null;
              return (
                <Card key={key} className="bg-primary/10 border-primary/20">
                  <CardContent className="pt-6 text-center">
                    <div className="text-3xl font-bold text-primary mb-2">{value}</div>
                    <div className="text-sm font-medium text-stone-700">Connected {key}</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Connected Entities */}
        {Object.entries(connectedEntities).map(([connectedType, entities]) => {
          if (!entities || entities.length === 0) return null;
          
          return (
            <Card key={connectedType}>
              <CardHeader className="border-b border-border">
                <div className="flex items-center gap-3">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-lg text-white ${getEntityIconBg(connectedType)}`}>
                    {getEntityIcon(connectedType)}
                  </div>
                  <CardTitle>Connected {connectedType} <Badge variant="outline" className="ml-2">{entities.length}</Badge></CardTitle>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {entities.map((entity, index) => {
                    const entityKey = entity.id || entity.name || `${connectedType}_${index}`;
                    return (
                      <div 
                        key={entityKey}
                        onClick={() => handleEntityClick(entity, connectedType)}
                        className="bg-stone-50 border border-stone-200 rounded-xl p-4 transition-all cursor-pointer hover:bg-white hover:shadow-md hover:-translate-y-0.5"
                      >
                        <div className="flex items-center gap-3 mb-3">
                          <div className={`flex items-center justify-center w-7 h-7 rounded-md text-white ${getEntityIconBg(connectedType)}`}>
                            {getEntityIcon(connectedType)}
                          </div>
                          <h3 className="text-base font-medium text-stone-900 flex-1">
                            {entity.name || 
                             entity.properties?.equipment_name || 
                             entity.properties?.tag || 
                             entity.properties?.name ||
                             entity.id || 
                             'Unknown'}
                          </h3>
                        </div>
                        
                        {entity.description && (
                          <p className="text-stone-600 text-sm leading-relaxed mb-2">{entity.description}</p>
                        )}
                        
                        <div className="flex gap-2 mt-2 flex-wrap">
                          {entity.relationship_type && (
                            <Badge variant="secondary" className="bg-green-100 text-green-800 hover:bg-green-200">
                              {entity.relationship_type}
                            </Badge>
                          )}
                          {entity.properties && Object.entries(entity.properties).slice(0, 3).map(([key, value]) => (
                            <Badge key={key} variant="secondary">
                              {key}: {typeof value === 'object' ? 'Object' : String(value).slice(0, 20)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          );
        })}
        
        {Object.keys(connectedEntities).length === 0 && (
          <Card>
            <CardHeader className="border-b border-border">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 bg-stone-400 rounded-lg text-white">
                  <Box />
                </div>
                <CardTitle>No Connected Entities</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <p className="text-stone-600 text-center py-8">
                No connected entities found for this {entityType.toLowerCase()}.
              </p>
            </CardContent>
          </Card>
        )}
        
        {/* Work Orders Section - Show for sensors, equipment, and some other entity types */}
        {(entityType === 'Sensor' || entityType === 'Equipment Sensors' || entityType === 'Area Sensors' || entityType === 'Equipment') && (
          <WorkOrdersSection 
            entityType={entityType} 
            entityName={entityData?.name || 
                       entityData?.properties?.tag ||
                       entityData?.properties?.name ||
                       entityId}
            areaName={areaName}
          />
        )}
      </div>
    </div>
  );
};

export default EntityDetail;