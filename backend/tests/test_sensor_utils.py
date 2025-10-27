"""
Tests for sensor utility functions.
"""

import pytest
from services.sensor_utils import transform_sensor_to_asset_name, extract_sensor_base_name


class TestSensorNameTransformation:
    """Test cases for sensor name transformation functions."""
    
    def test_transform_sensor_to_asset_name_basic(self):
        """Test basic sensor name transformation."""
        # Test the example from the specification
        sensor_name = "4038LI329.DACA.PV"
        expected = "740-38-LI-329"
        result = transform_sensor_to_asset_name(sensor_name)
        assert result == expected
    
    def test_transform_sensor_to_asset_name_variations(self):
        """Test various sensor name formats."""
        test_cases = [
            ("4038LI329.DACA.PV", "740-38-LI-329"),
            ("1234TI567.SOME.VALUE", "712-34-TI-567"),
            ("9876PI123.OTHER.TAG", "798-76-PI-123"),
            ("5050LIC999.CTRL.SP", "750-50-LIC-999"),
        ]
        
        for sensor_name, expected in test_cases:
            result = transform_sensor_to_asset_name(sensor_name)
            assert result == expected, f"Failed for {sensor_name}: expected {expected}, got {result}"
    
    def test_transform_invalid_sensor_names(self):
        """Test invalid sensor name formats."""
        invalid_names = [
            "invalid",
            "123.DACA.PV",  # Too short
            "12345LI329.DACA.PV",  # Too many initial digits
            "40LI329.DACA.PV",  # Too few initial digits
            "4038329.DACA.PV",  # Missing letters
            "4038LI.DACA.PV",  # Missing final numbers
        ]
        
        for invalid_name in invalid_names:
            result = transform_sensor_to_asset_name(invalid_name)
            assert result is None, f"Should return None for invalid name: {invalid_name}"
    
    def test_extract_sensor_base_name(self):
        """Test extracting base sensor name."""
        test_cases = [
            ("4038LI329.DACA.PV", "4038LI329"),
            ("1234TI567.SOME.VALUE", "1234TI567"),
            ("simple_name", "simple_name"),
            ("name.with.dots", "name"),
        ]
        
        for full_name, expected_base in test_cases:
            result = extract_sensor_base_name(full_name)
            assert result == expected_base, f"Failed for {full_name}: expected {expected_base}, got {result}"


if __name__ == "__main__":
    pytest.main([__file__])