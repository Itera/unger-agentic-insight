import React, { useState, useEffect } from 'react';
import { Wrench, Calendar, AlertTriangle, ExternalLink, Clock, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardContent, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

const getStatusBadge = (status) => {
  switch (status) {
    case 8: return 'bg-green-100 text-green-800';
    case 7: return 'bg-yellow-100 text-yellow-800';
    case 1: return 'bg-red-100 text-red-800';
    default: return 'bg-stone-100 text-stone-800';
  }
};

const getPriorityBadge = (priority) => {
  switch (priority) {
    case 1: return 'bg-red-100 text-red-800';
    case 2: return 'bg-yellow-100 text-yellow-800';
    case 3: return 'bg-green-100 text-green-800';
    default: return 'bg-stone-100 text-stone-800';
  }
};

const WorkOrdersSection = ({ entityType, entityName, areaName }) => {
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchWorkOrders = async () => {
      try {
        setLoading(true);
        setError(null);

        let endpoint;
        if (entityType === 'Sensor' || entityType === 'Equipment Sensors' || entityType === 'Area Sensors') {
          // Fetch work orders for specific sensor (highest priority)
          endpoint = `/api/sensors/${encodeURIComponent(entityName)}/work-orders`;
        } else if (entityType === 'Equipment') {
          // Fetch work orders for all sensors connected to this equipment
          endpoint = `/api/equipment/${encodeURIComponent(entityName)}/work-orders`;
        } else if (entityType === 'AssetArea' || areaName) {
          // Fetch work orders for all sensors in the area (fallback)
          const areaToUse = areaName || entityName;
          endpoint = `/api/areas/${encodeURIComponent(areaToUse)}/work-orders`;
        } else {
          // For other entity types, we don't fetch work orders
          setLoading(false);
          return;
        }

        const response = await fetch(endpoint);
        if (!response.ok) {
          throw new Error('Failed to fetch work orders');
        }

        const data = await response.json();
        setWorkOrders(data.work_orders || []);

      } catch (err) {
        console.error('Error fetching work orders:', err);
        setError('Failed to load work orders');
      } finally {
        setLoading(false);
      }
    };

    if (entityName || areaName) {
      fetchWorkOrders();
    }
  }, [entityType, entityName, areaName]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 8: return 'Completed';
      case 7: return 'In Progress';
      case 1: return 'Open';
      default: return `Status ${status}`;
    }
  };

  const getPriorityText = (priority) => {
    switch (priority) {
      case 1: return 'High';
      case 2: return 'Medium';  
      case 3: return 'Low';
      default: return `Priority ${priority}`;
    }
  };

  const handleWorkOrderClick = (workOrder) => {
    if (workOrder.url) {
      window.open(workOrder.url, '_blank');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-lime-600 rounded-lg text-white">
              <Wrench />
            </div>
            <CardTitle>Work Orders</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex justify-center items-center p-8 text-stone-600">
            <Clock className="animate-spin mr-2" size={20} />
            Loading work orders...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-lime-600 rounded-lg text-white">
              <Wrench />
            </div>
            <CardTitle>Work Orders</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center p-8 text-red-600 text-center">
            <AlertTriangle size={24} className="mb-2" />
            <p>{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!workOrders || workOrders.length === 0) {
    return (
      <Card>
        <CardHeader className="border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-lime-600 rounded-lg text-white">
              <Wrench />
            </div>
            <CardTitle>Work Orders</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="text-center p-8 text-stone-600">
            <CheckCircle size={32} className="mx-auto mb-4 text-green-600" />
            <p>No work orders found for this {entityType === 'AssetArea' ? 'area' : 'sensor'}.</p>
            <p className="text-sm text-stone-400 mt-2">
              This indicates good maintenance status!
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="border-b border-border">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-lime-600 rounded-lg text-white">
            <Wrench />
          </div>
          <CardTitle>Work Orders ({workOrders.length})</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="grid gap-4">
          {workOrders.map((workOrder) => (
            <div 
              key={workOrder.id} 
              onClick={() => handleWorkOrderClick(workOrder)}
              className="bg-stone-50 border border-stone-200 rounded-xl p-5 transition-all cursor-pointer hover:bg-white hover:shadow-md hover:-translate-y-0.5"
            >
              <div className="flex justify-between items-start gap-4 mb-3">
                <div className="flex-1">
                  <div className="font-semibold text-stone-900 text-lg mb-1">
                    Work Order #{workOrder.nr}
                    {workOrder.sensor_name && (
                      <Badge variant="secondary" className="ml-2 bg-blue-50 text-blue-700">
                        {workOrder.sensor_name}
                      </Badge>
                    )}
                  </div>
                  <div className="text-stone-600 leading-relaxed mb-3">
                    {workOrder.short_description}
                    {workOrder.description && workOrder.description !== workOrder.short_description && (
                      <>
                        <br />
                        <span className="text-sm text-stone-500">
                          {workOrder.description}
                        </span>
                      </>
                    )}
                  </div>
                  
                  {workOrder.comment && (
                    <div className="text-stone-700 text-sm italic bg-stone-100 p-2 rounded-md mb-3">
                      "{workOrder.comment}"
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col gap-2 items-end">
                  <Badge className={getStatusBadge(workOrder.status)}>
                    {getStatusText(workOrder.status)}
                  </Badge>
                  <Badge className={getPriorityBadge(workOrder.priority)}>
                    {getPriorityText(workOrder.priority)}
                  </Badge>
                </div>
              </div>
              
              <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3 mt-4">
                <div className="flex items-center gap-2 text-stone-600 text-sm">
                  <Calendar size={16} />
                  Created: {formatDate(workOrder.created_at)}
                </div>
                <div className="flex items-center gap-2 text-stone-600 text-sm">
                  <Calendar size={16} />
                  From: {formatDate(workOrder.from_date)}
                </div>
                <div className="flex items-center gap-2 text-stone-600 text-sm">
                  <Calendar size={16} />
                  To: {formatDate(workOrder.to_date)}
                </div>
                {workOrder.finished_date && (
                  <div className="flex items-center gap-2 text-stone-600 text-sm">
                    <CheckCircle size={16} />
                    Finished: {formatDate(workOrder.finished_date)}
                  </div>
                )}
              </div>
              
              {workOrder.url && (
                <div className="mt-4 text-right">
                  <a 
                    href={workOrder.url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    onClick={(e) => e.stopPropagation()}
                    className="inline-flex items-center gap-2 px-3 py-2 bg-emerald-700 text-white no-underline rounded-md text-sm transition-colors hover:bg-emerald-800"
                  >
                    View Details <ExternalLink size={14} />
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default WorkOrdersSection;
