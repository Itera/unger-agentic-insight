import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { ArrowLeft, MapPin, Activity, AlertCircle } from 'lucide-react';

const DetailContainer = styled.div`
  width: 100%;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: white;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
`;

const Title = styled.h1`
  font-size: 2rem;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`;

const ContentPlaceholder = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  color: #666;
`;

const LoadingState = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem;
  color: white;
  font-size: 1.1rem;
`;

const AreaDetail = () => {
  const { areaId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const handleBack = () => {
    navigate('/navigate');
  };

  if (loading) {
    return (
      <LoadingState>
        <Activity className="animate-spin" size={24} style={{ marginRight: '0.5rem' }} />
        Loading area details...
      </LoadingState>
    );
  }

  return (
    <DetailContainer>
      <Header>
        <BackButton onClick={handleBack}>
          <ArrowLeft size={20} />
          Back to Overview
        </BackButton>
        <MapPin size={24} color="white" />
        <Title>Area {decodeURIComponent(areaId)}</Title>
      </Header>

      <ContentPlaceholder>
        <h3>Area Detail View Coming Soon</h3>
        <p>This will show equipment, sensors, and connected entities for area {decodeURIComponent(areaId)}</p>
        <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#999' }}>
          Will be implemented in the next user stories (US-005, US-006)
        </p>
      </ContentPlaceholder>
    </DetailContainer>
  );
};

export default AreaDetail;