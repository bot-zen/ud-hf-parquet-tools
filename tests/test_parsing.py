#!/usr/bin/env python3
"""Tests for CoNLL-U parsing helper functions."""

import pytest

# Import from pre-loaded module (via conftest.py)
from ud_template import parse_feats, parse_deps, parse_misc


class TestParseFeats:
    """Test parse_feats() function."""

    def test_none_input(self):
        """None input should return empty dict."""
        assert parse_feats(None) == {}

    def test_empty_string(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            parse_feats("")

    def test_single_feature(self):
        """Single feature should be parsed correctly."""
        assert parse_feats("Number=Sing") == {"Number": "Sing"}

    def test_multiple_features(self):
        """Multiple features should be parsed correctly."""
        result = parse_feats("Number=Sing|Case=Nom|Gender=Masc")
        assert result == {"Number": "Sing", "Case": "Nom", "Gender": "Masc"}

    def test_feature_with_multiple_values(self):
        """Features with comma-separated values should be preserved."""
        result = parse_feats("NumType=Card,Ord")
        assert result == {"NumType": "Card,Ord"}

    def test_empty_feature_value(self):
        """Empty feature values should be preserved."""
        result = parse_feats("Gender=")
        assert result == {"Gender": ""}


class TestParseDeps:
    """Test parse_deps() function."""

    def test_none_input(self):
        """None input should return empty dict."""
        assert parse_deps(None) == {}

    def test_empty_string(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            parse_deps("")

    def test_single_dep(self):
        """Single dependency should be parsed correctly."""
        assert parse_deps("4:nmod") == {"4": "nmod"}

    def test_multiple_deps(self):
        """Multiple dependencies should be parsed correctly."""
        result = parse_deps("2:nsubj|4:conj")
        assert result == {"2": "nsubj", "4": "conj"}

    def test_enhanced_deps(self):
        """Enhanced dependencies with subtypes should be parsed correctly."""
        result = parse_deps("3:nmod:poss|5:obl:tmod")
        assert result == {"3": "nmod:poss", "5": "obl:tmod"}


class TestParseMisc:
    """Test parse_misc() function."""

    def test_none_input(self):
        """None input should return empty dict."""
        assert parse_misc(None) == {}

    def test_empty_string(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            parse_misc("")

    def test_single_misc(self):
        """Single MISC attribute should be parsed correctly."""
        assert parse_misc("SpaceAfter=No") == {"SpaceAfter": "No"}

    def test_multiple_misc(self):
        """Multiple MISC attributes should be parsed correctly."""
        result = parse_misc("SpaceAfter=No|Translit=abc")
        assert result == {"SpaceAfter": "No", "Translit": "abc"}

    def test_misc_with_special_chars(self):
        """MISC with special characters should be parsed correctly."""
        result = parse_misc("OrigForm=don't|Translit=don%27t")
        assert result == {"OrigForm": "don't", "Translit": "don%27t"}
