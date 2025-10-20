"""
Utility functions for sensor name transformation and maintenance API operations.
"""

import re
from typing import Optional


def transform_sensor_to_asset_name(sensor_name: str) -> Optional[str]:
    """
    Transform sensor name format to asset name format.
    
    Example: 4038LI329.DACA.PV -> 740-38-LI-329
    Pattern: Add '7' at start, then format as '700-00-Letters-000'
    
    Args:
        sensor_name: Sensor name in format like '4038LI329.DACA.PV'
        
    Returns:
        Asset name in format like '740-38-LI-329' or None if invalid format
    """
    # Extract the base part before the first dot
    base_name = sensor_name.split('.')[0]
    
    # Use regex to match pattern: numbers + letters + numbers
    # Example: 4038LI329 -> groups: ('40', '38', 'LI', '329')
    pattern = r'^(\d{2})(\d{2})([A-Z]+)(\d+)$'
    match = re.match(pattern, base_name)
    
    if not match:
        return None
    
    first_two, second_two, letters, last_numbers = match.groups()
    
    # Format: 7 + first_two + - + second_two + - + letters + - + last_numbers
    asset_name = f"7{first_two}-{second_two}-{letters}-{last_numbers}"
    
    return asset_name


def extract_sensor_base_name(sensor_name: str) -> str:
    """
    Extract the base sensor name from full sensor identifier.
    
    Args:
        sensor_name: Full sensor name like '4038LI329.DACA.PV'
        
    Returns:
        Base sensor name like '4038LI329'
    """
    return sensor_name.split('.')[0]