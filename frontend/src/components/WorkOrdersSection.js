import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Wrench, Calendar, User, AlertTriangle, ExternalLink, Clock, CheckCircle } from 'lucide-react';

const Section = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin: 0;
`;

const SectionIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #ff8a65 0%, #ff7043 100%);
  border-radius: 8px;
  color: white;
`;

const WorkOrdersGrid = styled.div`
  display: grid;
  gap: 1rem;
`;

const WorkOrderCard = styled.div`
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 1.25rem;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    background: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
`;

const WorkOrderHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
`;

const WorkOrderMain = styled.div`
  flex: 1;
`;

const WorkOrderNumber = styled.div`
  font-weight: 600;
  color: #333;
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
`;

const WorkOrderDescription = styled.div`
  color: #666;
  line-height: 1.4;
  margin-bottom: 0.75rem;
`;

const WorkOrderComment = styled.div`
  color: #555;
  font-size: 0.9rem;
  font-style: italic;
  background: #f5f5f5;
  padding: 0.5rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
`;

const WorkOrderMeta = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-size: 0.9rem;
`;

const StatusBadge = styled.div`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background: ${props => {
    switch (props.status) {
      case 8: return '#d4edda'; // Completed - green
      case 7: return '#fff3cd'; // In progress - yellow  
      case 1: return '#f8d7da'; // Open - red
      default: return '#e9ecef'; // Unknown - gray
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 8: return '#155724';
      case 7: return '#856404';
      case 1: return '#721c24';
      default: return '#495057';
    }
  }};
`;

const PriorityBadge = styled.div`
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background: ${props => {
    switch (props.priority) {
      case 1: return '#f8d7da'; // High - red
      case 2: return '#fff3cd'; // Medium - yellow
      case 3: return '#d4edda'; // Low - green
      default: return '#e9ecef'; // Unknown - gray
    }
  }};
  color: ${props => {
    switch (props.priority) {
      case 1: return '#721c24';
      case 2: return '#856404';
      case 3: return '#155724';
      default: return '#495057';
    }
  }};
`;

const ExternalLinkButton = styled.a`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #667eea;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: background 0.3s ease;

  &:hover {
    background: #5a6fd8;
  }
`;

const LoadingState = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: #666;
`;

const ErrorState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: #dc3545;
  text-align: center;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 2rem;
  color: #666;
`;

const SensorTag = styled.span`
  background: #e7f3ff;
  color: #0066cc;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-right: 0.5rem;
`;

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
      <Section>
        <SectionHeader>
          <SectionIcon>
            <Wrench />
          </SectionIcon>
          <SectionTitle>Work Orders</SectionTitle>
        </SectionHeader>
        <LoadingState>
          <Clock className="animate-spin" size={20} style={{ marginRight: '0.5rem' }} />
          Loading work orders...
        </LoadingState>
      </Section>
    );
  }

  if (error) {
    return (
      <Section>
        <SectionHeader>
          <SectionIcon>
            <Wrench />
          </SectionIcon>
          <SectionTitle>Work Orders</SectionTitle>
        </SectionHeader>
        <ErrorState>
          <AlertTriangle size={24} style={{ marginBottom: '0.5rem' }} />
          <p>{error}</p>
        </ErrorState>
      </Section>
    );
  }

  if (!workOrders || workOrders.length === 0) {
    return (
      <Section>
        <SectionHeader>
          <SectionIcon>
            <Wrench />
          </SectionIcon>
          <SectionTitle>Work Orders</SectionTitle>
        </SectionHeader>
        <EmptyState>
          <CheckCircle size={32} color="#28a745" style={{ marginBottom: '1rem' }} />
          <p>No work orders found for this {entityType === 'AssetArea' ? 'area' : 'sensor'}.</p>
          <p style={{ fontSize: '0.9rem', color: '#999' }}>
            This indicates good maintenance status!
          </p>
        </EmptyState>
      </Section>
    );
  }

  return (
    <Section>
      <SectionHeader>
        <SectionIcon>
          <Wrench />
        </SectionIcon>
        <SectionTitle>Work Orders ({workOrders.length})</SectionTitle>
      </SectionHeader>
      
      <WorkOrdersGrid>
        {workOrders.map((workOrder) => (
          <WorkOrderCard key={workOrder.id} onClick={() => handleWorkOrderClick(workOrder)}>
            <WorkOrderHeader>
              <WorkOrderMain>
                <WorkOrderNumber>
                  Work Order #{workOrder.nr}
                  {workOrder.sensor_name && (
                    <SensorTag>{workOrder.sensor_name}</SensorTag>
                  )}
                </WorkOrderNumber>
                <WorkOrderDescription>
                  {workOrder.short_description}
                  {workOrder.description && workOrder.description !== workOrder.short_description && (
                    <>
                      <br />
                      <span style={{ fontSize: '0.9rem', color: '#777' }}>
                        {workOrder.description}
                      </span>
                    </>
                  )}
                </WorkOrderDescription>
                
                {workOrder.comment && (
                  <WorkOrderComment>
                    "{workOrder.comment}"
                  </WorkOrderComment>
                )}
              </WorkOrderMain>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
                <StatusBadge status={workOrder.status}>
                  {getStatusText(workOrder.status)}
                </StatusBadge>
                <PriorityBadge priority={workOrder.priority}>
                  {getPriorityText(workOrder.priority)}
                </PriorityBadge>
              </div>
            </WorkOrderHeader>
            
            <WorkOrderMeta>
              <MetaItem>
                <Calendar size={16} />
                Created: {formatDate(workOrder.created_at)}
              </MetaItem>
              <MetaItem>
                <Calendar size={16} />
                From: {formatDate(workOrder.from_date)}
              </MetaItem>
              <MetaItem>
                <Calendar size={16} />
                To: {formatDate(workOrder.to_date)}
              </MetaItem>
              {workOrder.finished_date && (
                <MetaItem>
                  <CheckCircle size={16} />
                  Finished: {formatDate(workOrder.finished_date)}
                </MetaItem>
              )}
            </WorkOrderMeta>
            
            {workOrder.url && (
              <div style={{ marginTop: '1rem', textAlign: 'right' }}>
                <ExternalLinkButton href={workOrder.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                  View Details <ExternalLink size={14} />
                </ExternalLinkButton>
              </div>
            )}
          </WorkOrderCard>
        ))}
      </WorkOrdersGrid>
    </Section>
  );
};

export default WorkOrdersSection;