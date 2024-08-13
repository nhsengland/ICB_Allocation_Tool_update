
# Tests for functions in utils will be written here
import pytest
from utils import excel_round

def test_excel_round():
    # Test basic rounding with default precision (0.01)
    assert excel_round(2.675) == 2.68, "Failed to round 2.675 to 2.68"
    assert excel_round(2.5) == 2.5, "Failed to round 2.5 to 2.5"
    assert excel_round(1.234567, 0.01) == 1.23, "Failed to round 1.234567 to 1.23"
    
    # Test rounding to different precisions
    assert excel_round(2.675, 0.1) == 2.7, "Failed to round 2.675 to 2.7"
    assert excel_round(1.234567, 0.001) == 1.235, "Failed to round 1.234567 to 1.235"
    assert excel_round(1.234567, 0.0001) == 1.2346, "Failed to round 1.234567 to 1.2346"
    
    # Test negative numbers
    assert excel_round(-2.675) == -2.68, "Failed to round -2.675 to -2.67"
    assert excel_round(-2.5) == -2.5, "Failed to round -2.5 to -2.5"
    assert excel_round(-1.234567, 0.01) == -1.23, "Failed to round -1.234567 to -1.23"
    
    # Test rounding with zero precision
    assert excel_round(2.675, 1) == 3.0, "Failed to round 2.675 to 3"
    assert excel_round(2.5, 1) == 3.0, "Failed to round 2.5 to 3"
    assert excel_round(1.234567, 1) == 1.0, "Failed to round 1.234567 to 1"
    
    # Test large numbers
    assert excel_round(123456789.555, 0.01) == 123456789.56, "Failed to round 123456789.555 to 123456789.56"
    assert excel_round(-123456789.555, 0.01) == -123456789.56, "Failed to round -123456789.555 to -123456789.55"
    
    # Test small numbers
    assert excel_round(0.00056789, 0.00001) == 0.00057, "Failed to round 0.00056789 to 0.00057"
    assert excel_round(-0.00056789, 0.00001) == -0.00057, "Failed to round -0.00056789 to -0.00057"
    
    # Test rounding with negative precision
    assert excel_round(12345, 100) == 12300, "Failed to round 12345 to 12300"
    assert excel_round(-12345, 100) == -12300, "Failed to round -12345 to -12300"
    
    # Test rounding halfway cases
    assert excel_round(0.5, 1) == 1.0, "Failed to round 0.5 to 1"
    assert excel_round(-0.5, 1) == -1.0, "Failed to round -0.5 to -1"
    assert excel_round(2.675, 0.01) == 2.68, "Failed to round 2.675 to 2.68"

    # Test exceptions
    assert excel_round('string', 0.01) == 'string', "Failed to handle string input"
    assert excel_round(None, 0.01) == None, "Failed to handle None input"
    assert excel_round({}, 0.01) == {}, "Failed to handle dict input"
    assert excel_round([], 0.01) == [], "Failed to handle list input"