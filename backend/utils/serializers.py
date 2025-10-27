"""
Data serialization utilities

Helper functions for converting Neo4j data types to JSON-serializable formats.
"""


def serialize_neo4j_data(data):
    """
    Convert Neo4j data types to JSON-serializable formats
    
    Args:
        data: Neo4j data (dict, list, or Neo4j object)
        
    Returns:
        JSON-serializable version of the data
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = serialize_neo4j_data(value)
        return result
    elif isinstance(data, list):
        return [serialize_neo4j_data(item) for item in data]
    elif hasattr(data, '_DateTime__date') and hasattr(data, '_DateTime__time'):
        # Handle Neo4j DateTime objects
        try:
            # Convert to ISO format string
            date_part = data._DateTime__date
            time_part = data._DateTime__time
            # Create a simple datetime string
            return f"{date_part._Date__year:04d}-{date_part._Date__month:02d}-{date_part._Date__day:02d}T{time_part._Time__hour:02d}:{time_part._Time__minute:02d}:{time_part._Time__second:02d}Z"
        except:
            return str(data)
    elif hasattr(data, '__dict__'):
        # Handle other Neo4j objects
        return str(data)
    else:
        return data
