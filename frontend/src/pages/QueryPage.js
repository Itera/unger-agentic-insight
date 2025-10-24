import React, { useState } from 'react';
import axios from 'axios';
import { Send, Brain, Clock, Database, BarChart3, MapPin, Target } from 'lucide-react';
import { useNavigationContext } from '../contexts/NavigationContext';
import ContextVisualization from '../components/ContextVisualization';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';

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
        <div className="bg-stone-100 rounded-lg p-6 mt-4 border border-stone-200">
          <h4 className="mb-4 text-stone-800 font-semibold">Data Visualization</h4>
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
                  stroke={['#047857', '#10b981', '#f59e0b'][index]} 
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="max-w-7xl mx-auto p-8">
      <h1 className="text-4xl font-bold text-stone-900 text-center mb-12 tracking-tight">
        AI-Powered Industrial Insights
      </h1>
      
      {/* Context Visualization */}
      <ContextVisualization 
        context={getChatContext()}
        contextData={contextData || (response?.context_used)}
        mode={chatMode}
        isVisible={true}
      />
      
      <Card className="mb-8">
        <CardContent className="pt-6">
          <div className="flex gap-4 mb-4">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about your industrial data... \nExamples:\n• What are the temperature trends for zone 75-12?\n• Show me sensors with quality issues\n• Analyze tank levels over the last 24 hours\n• Which equipment needs maintenance attention?"
              className="flex-1 p-4 border-2 border-stone-200 rounded-lg text-base resize-vertical min-h-[100px] transition-all focus:outline-none focus:border-primary-700 focus:ring-2 focus:ring-primary-700/20 placeholder:text-stone-500"
            />
            <Button 
              onClick={handleSubmit} 
              disabled={loading || !query.trim()}
              className="bg-primary-700 hover:bg-primary-800 text-white font-semibold min-h-[100px] px-8 flex flex-col items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Brain className="animate-spin" size={20} />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Send size={20} />
                  <span>Ask AI</span>
                </>
              )}
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Checkbox
                id="useAdx"
                checked={useAdx}
                onCheckedChange={setUseAdx}
              />
              <Label htmlFor="useAdx" className="text-stone-700 font-medium cursor-pointer">
                Use Azure Data Explorer (when configured)
              </Label>
            </div>
            
            {/* Context Mode Toggle */}
            <div className="flex items-center gap-2">
              <Checkbox
                id="chatMode"
                checked={chatMode === 'scoped'}
                onCheckedChange={toggleChatMode}
              />
              <Label htmlFor="chatMode" className="text-stone-700 font-medium cursor-pointer">
                Scoped Chat Mode
              </Label>
            </div>
            
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-stone-600">
                {useAdx ? <Database size={16} /> : <BarChart3 size={16} />}
                <span>{useAdx ? 'ADX Mode' : 'Local Database Mode'}</span>
              </div>
              
              {/* Context Indicator */}
              <div className={`flex items-center gap-2 ${
                chatMode === 'scoped' && hasActiveContext ? 'text-primary-700' : 'text-stone-600'
              }`}>
                {chatMode === 'scoped' ? <Target size={16} /> : <MapPin size={16} />}
                <span>
                  {chatMode === 'scoped' && hasActiveContext ? `Scoped: ${getContextSummary()}` : 
                   chatMode === 'scoped' ? 'Scoped: No Context' : 'Global Mode'}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {response && (
        <Card className="mb-8">
          <CardHeader className="border-b border-stone-200">
            <div className="flex items-center gap-4">
              <Brain size={24} className="text-primary-700" />
              <div>
                <CardTitle className="text-stone-800">AI Analysis Result</CardTitle>
                <div className="flex items-center gap-4 mt-2 text-sm text-stone-500">
                  <span className="flex items-center gap-1">
                    <Clock size={14} />
                    {new Date(response.timestamp).toLocaleString()}
                  </span>
                  <span>Source: {response.source.toUpperCase()}</span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="leading-relaxed text-stone-900 whitespace-pre-wrap mb-4">
              {response.response}
            </div>

            {response.data && response.data.length > 0 && (
              <>
                {renderDataVisualization(response.data)}
                
                <div className="overflow-x-auto mt-4">
                  <h4 className="mb-4 text-stone-800 font-semibold">
                    Query Results ({response.data.length} rows)
                  </h4>
                  <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow">
                    <thead>
                      <tr>
                        {Object.keys(response.data[0]).map(key => (
                          <th key={key} className="bg-primary-700 text-white px-4 py-3 text-left font-semibold">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {response.data.slice(0, 50).map((row, index) => (
                        <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-stone-50'}>
                          {Object.values(row).map((value, cellIndex) => (
                            <td key={cellIndex} className="px-4 py-3 border-b border-stone-200 text-stone-700">
                              {typeof value === 'number' ? value.toLocaleString() : String(value)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {response.data.length > 50 && (
                    <div className="mt-4 text-stone-500 text-center">
                      Showing first 50 rows of {response.data.length} total results
                    </div>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          <h3 className="mb-4 text-stone-800 font-semibold">Try These Example Queries</h3>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example, index) => (
              <Button
                key={index}
                variant="outline"
                onClick={() => setExampleQuery(example)}
                className="bg-primary-50 border-primary-700 text-primary-800 hover:bg-primary-700 hover:text-white rounded-full transition-all"
              >
                {example}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QueryPage;