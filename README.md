# Agentic Insight - Industrial Data Analytics POC

A proof-of-concept application that integrates OpenAI agents with Azure Data Explorer (ADX) through Model Context Protocol (MCP) to provide AI-powered insights from industrial sensor data.

## Features

- 🤖 **AI-Powered Analysis**: Uses OpenAI GPT-4 to analyze industrial data and provide actionable insights
- 📊 **Data Import**: Upload and process CSV files containing HMI sensor data, tag configurations, and measurements  
- 🔍 **Natural Language Queries**: Ask questions about your data in plain English
- 📈 **Data Visualization**: Interactive charts and tables for time-series data
- 🏗️ **Dual Data Sources**: Support for both local PostgreSQL database and Azure Data Explorer
- 🐳 **Containerized**: Full Docker setup for easy deployment
- 🎨 **Sleek UI**: Modern, responsive React frontend

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │  ADX MCP    │    │   Database  │
│   (React)   │◄──►│  (FastAPI)  │◄──►│  Service    │◄──►│(PostgreSQL) │
│             │    │             │    │             │    │   /ADX      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │   OpenAI    │
                   │   GPT-4     │
                   └─────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- (Optional) Azure Data Explorer cluster with credentials

### Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd unger-agentic-insight
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and optional ADX credentials
   ```

3. **Start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - ADX MCP Service: http://localhost:8001

## Usage

### Data Import

1. Navigate to the **Import Data** page
2. Drag and drop or select CSV files with your industrial data
3. Supported formats:
   - HMI sensor data (timestamp, name, value, unit, quality)
   - Tag configurations (record ID, name, description, limits)
   - Itera measurements (time-series sensor readings)

### AI Query Interface

1. Go to the **Query Data** page
2. Type your question in natural language, such as:
   - "What are the highest sensor values in the last week?"
   - "Show me temperature trends for zone 75-12"
   - "Which sensors have quality issues?"
   - "Identify anomalies in tank level measurements"
3. Choose between local database or ADX mode
4. View AI analysis, data visualizations, and detailed results

## Example Queries

- **Operational**: "Which equipment needs maintenance attention based on sensor readings?"
- **Trend Analysis**: "Show me temperature trends for the last 24 hours"
- **Quality Control**: "Find sensors with bad quality indicators"
- **Anomaly Detection**: "Identify unusual patterns in pressure measurements"
- **Asset Management**: "List all tags configured for temperature monitoring"

## Data Sources

The application processes three types of CSV data found in your project root:

1. **sample_data.csv**: HMI sensor readings with timestamps and quality indicators
2. **TagConfigFormTo_Itera.csv**: Industrial tag configurations with descriptions and limits
3. **itera_data.csv**: Time-series measurements from various LI sensors

## Services

### Frontend (React)
- Modern, responsive UI with sleek design
- File upload with drag-and-drop
- Interactive data visualization
- Real-time AI query interface

### Backend (FastAPI)
- CSV data processing and import
- OpenAI GPT-4 integration for natural language processing
- Database operations and query execution
- RESTful API endpoints

### ADX MCP Service
- Model Context Protocol implementation
- Azure Data Explorer connectivity
- KQL query execution
- Schema introspection

### Database (PostgreSQL)
- Industrial data storage
- Import tracking
- Query result caching

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional - for Azure Data Explorer
ADX_CLUSTER_URL=https://your-cluster.kusto.windows.net
ADX_DATABASE=your_database
ADX_CLIENT_ID=your_client_id
ADX_CLIENT_SECRET=your_client_secret
ADX_TENANT_ID=your_tenant_id
```

### Development

For development, you can run services individually:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend  
cd frontend
npm install
npm start

# ADX MCP Service
cd adx-mcp
pip install -r requirements.txt
python main.py
```

## API Endpoints

- `POST /import-csv` - Upload CSV data
- `POST /query` - Process natural language queries
- `GET /health` - Health check
- `GET /tables` - List available tables
- `GET /import-status` - View import statistics

## Troubleshooting

### Common Issues

1. **OpenAI API errors**: Ensure your API key is valid and has sufficient credits
2. **Database connection**: Check PostgreSQL is running and accessible
3. **File upload issues**: Verify CSV format matches expected schema
4. **ADX connectivity**: Confirm Azure credentials and network access

### Logs

View service logs:
```bash
docker-compose logs frontend
docker-compose logs backend
docker-compose logs adx-mcp
docker-compose logs database
```

## Development Notes

This is a proof-of-concept application focusing on core functionality:
- No authentication/authorization
- Limited error handling
- Basic data validation
- Development-focused logging

For production use, consider adding:
- User authentication
- Input validation and sanitization
- Comprehensive error handling
- Monitoring and alerting
- Data backup and recovery
- Security hardening

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational and evaluation purposes.