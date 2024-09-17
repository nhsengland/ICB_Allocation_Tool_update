
# Tests for functions in utils will be written here
import pytest
from utils import excel_round
@pytest.mark.parametrize("value, precision, expected", [
    # Basic rounding with default precision
    (2.675, 0.01, 2.68),
    (2.5, 0.01, 2.5),
    (1.234567, 0.01, 1.23),

    # Rounding to different precisions
    (2.675, 0.1, 2.7),
    (1.234567, 0.001, 1.235),
    (1.234567, 0.0001, 1.2346),

    # Negative numbers
    (-2.675, 0.01, -2.68),
    (-2.5, 0.01, -2.5),
    (-1.234567, 0.01, -1.23),

    # Rounding with zero precision
    (2.675, 1, 3.0),
    (2.5, 1, 3.0),
    (1.234567, 1, 1.0),

    # Large numbers
    (123456789.555, 0.01, 123456789.56),
    (-123456789.555, 0.01, -123456789.56),

    # Small numbers
    (0.00056789, 0.00001, 0.00057),
    (-0.00056789, 0.00001, -0.00057),

    # Rounding with negative precision
    (12345, 100, 12300),
    (-12345, 100, -12300),

    # Halfway cases
    (0.5, 1, 1.0),
    (-0.5, 1, -1.0),
    (2.675, 0.01, 2.68),
])
def test_excel_round(value, precision, expected):
    assert excel_round(value, precision) == expected

@pytest.mark.parametrize("value, precision, expected", [
    # Test exceptions
    ('string', 0.01, 'string'),
    (None, 0.01, None),
    ({}, 0.01, {}),
    ([], 0.01, []),
])
def test_excel_round_exceptions(value, precision, expected):
    result = excel_round(value, precision)
    assert result == expected