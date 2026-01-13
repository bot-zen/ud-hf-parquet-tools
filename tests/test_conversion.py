#!/usr/bin/env python3
"""Tests for CoNLL-U conversion functions."""

# Import from pre-loaded module (via conftest.py)
from generate_parquet import conllu_dict_to_string, conllu_optional_field


class TestConlluDictToString:
    """Test conllu_dict_to_string() function."""

    def test_none_input(self):
        """None input should return underscore."""
        assert conllu_dict_to_string(None) == "_"

    def test_empty_dict(self):
        """Empty dict should return underscore."""
        assert conllu_dict_to_string({}) == "_"

    def test_single_item_dict(self):
        """Single item dict should be converted to Key=Value format."""
        assert conllu_dict_to_string({"Number": "Sing"}) == "Number=Sing"

    def test_multiple_items_dict(self):
        """Multiple items should preserve order and be joined with pipe."""
        from collections import OrderedDict

        result = conllu_dict_to_string(OrderedDict([("Number", "Sing"), ("Case", "Nom"), ("Gender", "Masc")]))
        assert result == "Number=Sing|Case=Nom|Gender=Masc"

    def test_string_input(self):
        """String input should be returned as-is."""
        assert conllu_dict_to_string("Number=Sing") == "Number=Sing"

    def test_none_string(self):
        """String 'None' should be converted to underscore."""
        assert conllu_dict_to_string("None") == "_"


class TestConlluOptionalField:
    """Test conllu_optional_field() function."""

    def test_none_input(self):
        """None input should return None."""
        assert conllu_optional_field(None) is None

    def test_empty_dict(self):
        """Empty dict should return None."""
        assert conllu_optional_field({}) is None

    def test_underscore_string(self):
        """Underscore string should return None."""
        assert conllu_optional_field("_") is None

    def test_empty_string(self):
        """Empty string should return None."""
        assert conllu_optional_field("") is None

    def test_none_string(self):
        """String 'None' should return None."""
        assert conllu_optional_field("None") is None

    def test_single_item_dict(self):
        """Single item dict should be converted to Key=Value format."""
        assert conllu_optional_field({"Number": "Sing"}) == "Number=Sing"

    def test_multiple_items_dict(self):
        """Multiple items should preserve order and be joined with pipe."""
        from collections import OrderedDict

        result = conllu_optional_field(OrderedDict([("Number", "Sing"), ("Case", "Nom")]))
        assert result == "Number=Sing|Case=Nom"

    def test_valid_string(self):
        """Valid string should be returned as-is."""
        assert conllu_optional_field("Number=Sing") == "Number=Sing"

    def test_valid_xpos(self):
        """Valid XPOS tag should be returned as-is."""
        assert conllu_optional_field("NNP") == "NNP"

    def test_feats_example(self):
        """Real-world FEATS example."""
        from collections import OrderedDict

        feats_dict = OrderedDict(
            [
                ("Case", "Nom"),
                ("Gender", "Masc"),
                ("Number", "Sing"),
                ("Person", "3"),
            ]
        )
        result = conllu_optional_field(feats_dict)
        assert result == "Case=Nom|Gender=Masc|Number=Sing|Person=3"

    def test_misc_example(self):
        """Real-world MISC example."""
        from collections import OrderedDict

        misc_dict = OrderedDict([("SpaceAfter", "No"), ("Translit", "abc")])
        result = conllu_optional_field(misc_dict)
        assert result == "SpaceAfter=No|Translit=abc"
