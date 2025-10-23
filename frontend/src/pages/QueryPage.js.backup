import React, { useState } from 'react';
import axios from 'axios';
import styled from 'styled-components';
import { Send, Brain, Clock, Database, BarChart3, MapPin, Target } from 'lucide-react';
import { useNavigationContext } from '../contexts/NavigationContext';
import ContextVisualization from '../components/ContextVisualization';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const PageContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 3rem 2rem;
`;

const Title = styled.h1`
  color: #1c1917;
  text-align: center;
  margin-bottom: 3rem;
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
`;

const QuerySection = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
  border: 1px solid #e7e5e4;
`;

const InputContainer = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const QueryInput = styled.textarea`
  flex: 1;
  padding: 1rem;
  border: 2px solid #e7e5e4;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: #1c1917;

  &:focus {
    outline: none;
    border-color: #047857;
    box-shadow: 0 0 0 3px rgba(4, 120, 87, 0.1);
  }

  &::placeholder {
    color: #78716c;
  }
`;

const SendButton = styled.button`
  background: #047857;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-family: inherit;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 100px;

  &:hover {
    background: #065f46;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(4, 120, 87, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const OptionsContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 1rem;
`;

const ToggleContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const Toggle = styled.input`
  width: 20px;
  height: 20px;
  cursor: pointer;
`;

const ToggleLabel = styled.label`
  color: #44403c;
  font-weight: 500;
  cursor: pointer;
`;

const ResponseSection = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
  border: 1px solid #e7e5e4;
  margin-bottom: 2rem;
`;

const ResponseHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e7e5e4;
`;

const ResponseText = styled.div`
  line-height: 1.6;
  color: #1c1917;
  white-space: pre-wrap;
  margin-bottom: 1rem;
`;

const DataVisualization = styled.div`
  background: #f5f5f4;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1rem;
  border: 1px solid #e7e5e4;
`;

const DataTable = styled.div`
  overflow-x: auto;
  margin-top: 1rem;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const TableHeader = styled.th`
  background: #047857;
  color: white;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
`;

const TableCell = styled.td`
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e7e5e4;
  color: #44403c;
`;

const TableRow = styled.tr`
  &:nth-child(even) {
    background: #f5f5f4;
  }
`;

const LoadingSpinner = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #047857;
`;

const ExampleQueries = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
  border: 1px solid #e7e5e4;
`;

const ExampleButton = styled.button`
  background: rgba(4, 120, 87, 0.1);
  border: 1px solid #047857;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 24px;
  cursor: pointer;
  margin: 0.5rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.9rem;
  font-family: inherit;
  font-weight: 500;

  &:hover {
    background: #047857;
    color: white;
    transform: translateY(-1px);
  }
`;

const QueryPage = () => {
  const { getChatContext, hasActiveContext, getContextSummary, chatMode, toggleChatMode } = useNavigationContext();
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useAdx, setUseAdx] = useState(false);
  const [contextData, setContextData] = useState(null);

  // Fetch context data when chat context changes
  React.useEffect(() => {
    const fetchContextData = async () => {
      const chatContext = getChatContext();
      if (chatMode === 'scoped' && chatContext && chatContext.nodeName) {
        try {
          const response = await axios.get(
            `/api/graph/context/${chatContext.nodeType}/${encodeURIComponent(chatContext.nodeName)}`
          );
          setContextData(response.data);
        } catch (error) {
          console.error('Failed to fetch context data:', error);
          setContextData(null);
        }
      } else {
        setContextData(null);
      }
    };
    
    fetchContextData();
  }, [getChatContext, chatMode]);

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const chatContext = getChatContext();
      const isContextual = chatMode === 'scoped' && chatContext;
      
      const endpoint = isContextual ? '/query/contextual' : '/query';
      const requestData = {
        query: query.trim(),
        use_adx: useAdx,
        ...(isContextual && { context: chatContext })
      };
      
      const result = await axios.post(endpoint, requestData);
      setResponse(result.data);
    } catch (error) {
      console.error('Query failed:', error);
      setResponse({
        query,
        response: `Error: ${error.response?.data?.detail || error.message}`,
        data: null,
        source: useAdx ? 'adx' : 'local',
        timestamp: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  const setExampleQuery = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  const exampleQueries = [
    "What are the highest sensor values in the last week?",
    "Show me temperature trends for the HMI sensors",
    "Which sensors have quality issues?",
    "What's the average scan frequency for active tags?",
    "Identify any anomalies in the Itera measurement data",
    "Show tank level measurements over time",
    "Which tags are configured for temperature monitoring?",
    "What are the operational limits for pressure sensors?"
  ];

  const renderDataVisualization = (data) => {
    if (!data || !Array.isArray(data) || data.length === 0) return null;

    // Check if data contains time series information
    const timeKeys = ['timestamp', 'time', 'created_at'];
    const timeKey = Object.keys(data[0]).find(key => 
      timeKeys.some(tk => key.toLowerCase().includes(tk))
    );

    const numericKeys = Object.keys(data[0]).filter(key => 
      typeof data[0][key] === 'number' || !isNaN(parseFloat(data[0][key]))
    );

    if (timeKey && numericKeys.length > 0) {
      // Render chart for time series data
      const chartData = data.map(item => ({
        time: new Date(item[timeKey]).toLocaleDateString(),
        ...numericKeys.reduce((acc, key) => {
          acc[key] = parseFloat(item[key]) || 0;
          return acc;
        }, {})
      }));

      return (
        <DataVisualization>
          <h4 style={{ marginBottom: '1rem', color: '#374151' }}>Data Visualization</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              {numericKeys.slice(0, 3).map((key, index) => (
                <Line 
                  key={key} 
                  type="monotone" 
                  dataKey={key} 
                  stroke={['#667eea', '#22c55e', '#f59e0b'][index]} 
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </DataVisualization>
      );
    }

    return null;
  };

  return (
    <PageContainer>
      <Title>AI-Powered Industrial Insights</Title>
      
      {/* Context Visualization */}
      <ContextVisualization 
        context={getChatContext()}
        contextData={contextData || (response?.context_used)}
        mode={chatMode}
        isVisible={true}
      />
      
      <QuerySection>
        <InputContainer>
          <QueryInput
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your industrial data... 
Examples:
• What are the temperature trends for zone 75-12?
• Show me sensors with quality issues
• Analyze tank levels over the last 24 hours
• Which equipment needs maintenance attention?"
          />
          <SendButton 
            onClick={handleSubmit} 
            disabled={loading || !query.trim()}
          >
            {loading ? (
              <>
                <Brain className="animate-spin" size={20} />
                Analyzing...
              </>
            ) : (
              <>
                <Send size={20} />
                Ask AI
              </>
            )}
          </SendButton>
        </InputContainer>

        <OptionsContainer>
          <ToggleContainer>
            <Toggle
              type="checkbox"
              id="useAdx"
              checked={useAdx}
              onChange={(e) => setUseAdx(e.target.checked)}
            />
            <ToggleLabel htmlFor="useAdx">
              Use Azure Data Explorer (when configured)
            </ToggleLabel>
          </ToggleContainer>
          
          {/* Context Mode Toggle */}
          <ToggleContainer>
            <Toggle
              type="checkbox"
              id="chatMode"
              checked={chatMode === 'scoped'}
              onChange={toggleChatMode}
            />
            <ToggleLabel htmlFor="chatMode">
              Scoped Chat Mode
            </ToggleLabel>
          </ToggleContainer>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.9rem' }}>
            <div style={{ color: '#666' }}>
              {useAdx ? <Database size={16} /> : <BarChart3 size={16} />}
              {useAdx ? ' ADX Mode' : ' Local Database Mode'}
            </div>
            
            {/* Context Indicator */}
            <div style={{ color: chatMode === 'scoped' && hasActiveContext ? '#667eea' : '#666' }}>
              {chatMode === 'scoped' ? <Target size={16} /> : <MapPin size={16} />}
              {chatMode === 'scoped' && hasActiveContext ? ` Scoped: ${getContextSummary()}` : 
               chatMode === 'scoped' ? ' Scoped: No Context' : ' Global Mode'}
            </div>
          </div>
        </OptionsContainer>
      </QuerySection>

      {response && (
        <ResponseSection>
          <ResponseHeader>
            <Brain size={24} color="#667eea" />
            <div>
              <h3 style={{ margin: 0, color: '#374151' }}>AI Analysis Result</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem', fontSize: '0.9rem', color: '#6b7280' }}>
                <span>
                  <Clock size={14} style={{ marginRight: '0.25rem' }} />
                  {new Date(response.timestamp).toLocaleString()}
                </span>
                <span>Source: {response.source.toUpperCase()}</span>
              </div>
            </div>
          </ResponseHeader>

          <ResponseText>{response.response}</ResponseText>

          {response.data && response.data.length > 0 && (
            <>
              {renderDataVisualization(response.data)}
              
              <DataTable>
                <h4 style={{ marginBottom: '1rem', color: '#374151' }}>
                  Query Results ({response.data.length} rows)
                </h4>
                <Table>
                  <thead>
                    <tr>
                      {Object.keys(response.data[0]).map(key => (
                        <TableHeader key={key}>{key}</TableHeader>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {response.data.slice(0, 50).map((row, index) => (
                      <TableRow key={index}>
                        {Object.values(row).map((value, cellIndex) => (
                          <TableCell key={cellIndex}>
                            {typeof value === 'number' ? value.toLocaleString() : String(value)}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </tbody>
                </Table>
                {response.data.length > 50 && (
                  <div style={{ marginTop: '1rem', color: '#6b7280', textAlign: 'center' }}>
                    Showing first 50 rows of {response.data.length} total results
                  </div>
                )}
              </DataTable>
            </>
          )}
        </ResponseSection>
      )}

      <ExampleQueries>
        <h3 style={{ marginBottom: '1rem', color: '#374151' }}>Try These Example Queries</h3>
        <div>
          {exampleQueries.map((example, index) => (
            <ExampleButton 
              key={index}
              onClick={() => setExampleQuery(example)}
            >
              {example}
            </ExampleButton>
          ))}
        </div>
      </ExampleQueries>
    </PageContainer>
  );
};

export default QueryPage;