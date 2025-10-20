import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { ChevronRight, Home } from 'lucide-react';

const BreadcrumbContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 0;
  margin-bottom: 1rem;
  font-size: 0.9rem;
`;

const BreadcrumbItem = styled.button`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: ${props => props.isActive ? 'white' : 'rgba(255, 255, 255, 0.7)'};
  cursor: ${props => props.isActive ? 'default' : 'pointer'};
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: ${props => props.isActive ? '600' : '400'};

  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }

  &:disabled {
    cursor: default;
  }
`;

const Separator = styled(ChevronRight)`
  color: rgba(255, 255, 255, 0.5);
  width: 16px;
  height: 16px;
`;

const HomeIcon = styled(Home)`
  width: 16px;
  height: 16px;
  margin-right: 0.25rem;
`;

const Breadcrumb = ({ items = [] }) => {
  const navigate = useNavigate();

  const handleItemClick = (item) => {
    if (item.path && !item.isActive) {
      navigate(item.path);
    }
  };

  // Always start with home
  const allItems = [
    {
      label: 'Plants',
      path: '/navigate',
      icon: <HomeIcon />,
      isActive: false
    },
    ...items
  ];

  return (
    <BreadcrumbContainer>
      {allItems.map((item, index) => (
        <React.Fragment key={index}>
          <BreadcrumbItem
            isActive={item.isActive}
            disabled={item.isActive}
            onClick={() => handleItemClick(item)}
          >
            {item.icon}
            {item.label}
          </BreadcrumbItem>
          
          {index < allItems.length - 1 && <Separator />}
        </React.Fragment>
      ))}
    </BreadcrumbContainer>
  );
};

export default Breadcrumb;