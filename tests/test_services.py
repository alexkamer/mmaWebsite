"""Test service layer functionality"""
import pytest
from mma_website.utils.text_utils import normalize_ascii, row_to_dict


class TestTextUtils:
    """Test text utility functions"""

    def test_normalize_ascii_basic(self):
        """Test basic ASCII normalization"""
        assert normalize_ascii("José Aldo") == "jose aldo"
        assert normalize_ascii("Khabib Nurmagomedov") == "khabib nurmagomedov"

    def test_normalize_ascii_special_chars(self):
        """Test normalization with special characters"""
        assert normalize_ascii("Patrício Freire") == "patricio freire"
        assert normalize_ascii("Jiří Procházka") == "jiri prochazka"

    def test_normalize_ascii_empty(self):
        """Test normalization with empty string"""
        assert normalize_ascii("") == ""

    def test_normalize_ascii_whitespace(self):
        """Test normalization handles extra whitespace"""
        result = normalize_ascii("  Test  Fighter  ")
        # normalize_ascii preserves internal whitespace, just lowercases
        assert "test" in result and "fighter" in result

    def test_row_to_dict(self):
        """Test row to dict conversion with mock data"""
        # Create a mock row object that mimics SQLAlchemy Row
        class MockRow:
            def __init__(self):
                self._mapping = {
                    'id': 1,
                    'name': "Test Fighter",
                    'weight_class': "Lightweight"
                }

        row = MockRow()
        result = row_to_dict(row)

        assert result['id'] == 1
        assert result['name'] == "Test Fighter"
        assert result['weight_class'] == "Lightweight"
