import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { Upload, Search, Database } from 'lucide-react';

const NavContainer = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
`;

const NavLinks = styled.div`
  display: flex;
  gap: 2rem;
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  text-decoration: none;
  color: ${props => props.active ? '#fff' : '#666'};
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent'};
  transition: all 0.3s ease;
  font-weight: 500;

  &:hover {
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(102, 126, 234, 0.1)'};
    color: ${props => props.active ? '#fff' : '#667eea'};
    transform: translateY(-2px);
  }
`;

const Navbar = () => {
  const location = useLocation();

  return (
    <NavContainer>
      <Logo>
        <Database size={24} />
        Agentic Insight
      </Logo>
      <NavLinks>
        <NavLink 
          to="/import" 
          active={location.pathname === '/import' ? 1 : 0}
        >
          <Upload size={18} />
          Import Data
        </NavLink>
        <NavLink 
          to="/query" 
          active={location.pathname === '/query' ? 1 : 0}
        >
          <Search size={18} />
          Query Data
        </NavLink>
      </NavLinks>
    </NavContainer>
  );
};

export default Navbar;