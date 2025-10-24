# Neo4j Docker Integration

This project uses an external Neo4j Docker container for graph database operations.

## Prerequisites

Before running this application, ensure you have the external Neo4j Docker container running with the following configuration:

### Required Neo4j Container
- **Container name**: `unger-neo4j`
- **Network**: `unger-network`
- **Ports**: 7474 (web interface), 7687 (bolt protocol)
- **Database**: `assets`
- **Credentials**: `neo4j` / `neo4j1234`

### Docker Network Setup
The Neo4j container should be running on the `unger-network` Docker network. If the network doesn't exist, create it:

```bash
docker network create unger-network
```

## Starting the Neo4j Container

If you have the external Neo4j setup from the Unger-Graph project, ensure it's running:

```bash
# Check if the container is running
docker ps | grep unger-neo4j

# If not running, start it
docker start unger-neo4j
```

## Application Configuration

The application is configured to connect to Neo4j using:
- **URI**: `neo4j://unger-neo4j:7687` (from Docker containers)
- **URI**: `neo4j://localhost:7687` (from host machine)
- **Username**: `neo4j`
- **Password**: `neo4j1234`
- **Database**: `assets`

## Verification

To verify the connection is working:

1. Start the Neo4j container (if not already running)
2. Run the connection test:
   ```bash
   python backend/test_graph_connection.py
   ```
3. Check the Neo4j web interface at http://localhost:7474

## Troubleshooting

### Connection Issues
- Ensure the Neo4j container is running and accessible
- Verify the `unger-network` exists and both containers are connected to it
- Check that ports 7474 and 7687 are not blocked

### Database Not Found
- Verify the database name is set to `assets`
- Check that the Neo4j instance has the correct database created

### Authentication Issues
- Confirm credentials: `neo4j` / `neo4j1234`
- Reset Neo4j password if needed through the web interface

## Migration from Neo4j Desktop

If migrating from Neo4j Desktop:
1. Export your data from Neo4j Desktop
2. Import into the Docker Neo4j instance
3. Update your local `.env` file with the Docker configuration
4. Test the connection using the verification steps above