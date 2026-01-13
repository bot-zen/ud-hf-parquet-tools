#!/usr/bin/env python3
"""Tests for CoNLL-U extraction logic (MWT, empty nodes, metadata)."""


# Import from pre-loaded module (via conftest.py)
from generate_parquet import extract_examples_from_conllu


class TestMWTDetection:
    """Test Multi-Word Token detection."""

    def test_mwt_detection(self, tmp_path):
        """MWTs should be detected correctly."""
        conllu_content = """# sent_id = 1
# text = Je l'ai vu.
1-2	l'ai	_	_	_	_	_	_	_	_
1	l'	le	DET	_	_	2	det	_	SpaceAfter=No
2	ai	avoir	AUX	_	_	3	aux	_	_
3	vu	voir	VERB	_	_	0	root	_	SpacesAfter=\\n

"""
        # Write to temp file
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        # Extract examples
        examples = extract_examples_from_conllu(str(test_file))

        assert len(examples) == 1
        example = examples[0]

        # Check MWT
        assert len(example["mwt"]) == 1
        mwt = example["mwt"][0]
        assert mwt["id"] == "1-2"
        assert mwt["form"] == "l'ai"
        assert mwt["feats"] is None
        assert mwt["misc"] is None

        # Check tokens (should NOT include MWT form)
        assert example["tokens"] == ["l'", "ai", "vu"]

    def test_mwt_with_feats(self, tmp_path):
        """MWT with FEATS field (Typo=Yes) should be preserved."""
        conllu_content = """# sent_id = 1
# text = Test
1-2	dont	_	_	_	Typo=Yes	_	_	_	_
1	do	do	VERB	_	_	0	root	_	_
2	n't	not	PART	_	_	1	advmod	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        mwt = examples[0]["mwt"][0]

        assert mwt["feats"] == "Typo=Yes"


class TestEmptyNodeDetection:
    """Test empty node detection."""

    def test_empty_node_detection(self, tmp_path):
        """Empty nodes should be detected correctly."""
        conllu_content = """# sent_id = 1
# text = Test
1	Test	test	NOUN	_	_	0	root	_	_
1.1	is	be	AUX	_	_	1	cop	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))

        assert len(examples) == 1
        example = examples[0]

        # Check empty node
        assert len(example["empty_nodes"]) == 1
        empty_node = example["empty_nodes"][0]
        assert empty_node["id"] == "1.1"
        assert empty_node["form"] == "is"
        assert empty_node["lemma"] == "be"
        assert empty_node["upos"] == "AUX"
        assert empty_node["deprel"] == "cop"

        # Check tokens (should NOT include empty node)
        assert example["tokens"] == ["Test"]

    def test_mwt_and_empty_node_distinction(self, tmp_path):
        """MWTs and empty nodes should not be confused."""
        conllu_content = """# sent_id = 1
# text = Je l'ai vu.
1-2	l'ai	_	_	_	_	_	_	_	_
1	l'	le	DET	_	_	2	det	_	_
2	ai	avoir	AUX	_	_	0	root	_	_
2.1	été	être	AUX	_	_	2	aux	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        # Should have exactly 1 MWT
        assert len(example["mwt"]) == 1
        assert example["mwt"][0]["id"] == "1-2"

        # Should have exactly 1 empty node
        assert len(example["empty_nodes"]) == 1
        assert example["empty_nodes"][0]["id"] == "2.1"

        # Tokens should only be syntactic words
        assert example["tokens"] == ["l'", "ai"]


class TestMetadataExtraction:
    """Test metadata extraction (sent_id, text, comments)."""

    def test_sent_id_and_text(self, tmp_path):
        """sent_id and text should be extracted correctly."""
        conllu_content = """# sent_id = test-001
# text = Hello world.
1	Hello	hello	INTJ	_	_	0	root	_	_
2	world	world	NOUN	_	_	1	vocative	_	SpaceAfter=No
3	.	.	PUNCT	_	_	1	punct	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        assert example["sent_id"] == "test-001"
        assert example["text"] == "Hello world."

    def test_comments_extraction(self, tmp_path):
        """Other metadata should be stored in comments."""
        conllu_content = """# newdoc id = doc1
# newpar id = par1
# sent_id = test-001
# text = Hello world.
1	Hello	hello	INTJ	_	_	0	root	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        assert example["sent_id"] == "test-001"
        assert example["text"] == "Hello world."
        assert "newdoc id = doc1" in example["comments"]
        assert "newpar id = par1" in example["comments"]

    def test_missing_text_reconstruction(self, tmp_path):
        """Missing text should be reconstructed from tokens."""
        conllu_content = """# sent_id = test-001
1	Hello	hello	INTJ	_	_	0	root	_	_
2	world	world	NOUN	_	_	1	vocative	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        assert example["text"] == "Hello world"

    def test_missing_sent_id_uses_index(self, tmp_path):
        """Missing sent_id should use sentence index."""
        conllu_content = """# text = First
1	First	first	ADJ	_	_	0	root	_	_

# text = Second
1	Second	second	ADJ	_	_	0	root	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))

        assert examples[0]["sent_id"] == "0"
        assert examples[1]["sent_id"] == "1"


class TestOptionalFieldHandling:
    """Test that optional fields are stored correctly (None vs string)."""

    def test_optional_fields_none(self, tmp_path):
        """Unspecified optional fields should be None."""
        conllu_content = """# sent_id = 1
# text = Test
1	Test	test	NOUN	_	_	0	root	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        # Optional fields should be None
        assert example["xpos"][0] is None
        assert example["feats"][0] is None
        assert example["deps"][0] is None
        assert example["misc"][0] is None

    def test_optional_fields_specified(self, tmp_path):
        """Specified optional fields should be strings."""
        conllu_content = """# sent_id = 1
# text = Test
1	Test	test	NOUN	NN	Number=Sing	0	root	4:nsubj	SpaceAfter=No

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        # Optional fields should be strings
        assert example["xpos"][0] == "NN"
        assert example["feats"][0] == "Number=Sing"
        assert example["deps"][0] == "4:nsubj"  # DEPS uses colon, not equals
        assert example["misc"][0] == "SpaceAfter=No"

    def test_required_fields_always_string(self, tmp_path):
        """Required fields should always be strings, never None."""
        conllu_content = """# sent_id = 1
# text = Test
1	Test	test	NOUN	_	_	0	root	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(conllu_content)

        examples = extract_examples_from_conllu(str(test_file))
        example = examples[0]

        # Required fields should be strings
        assert example["tokens"][0] == "Test"
        assert example["lemmas"][0] == "test"
        assert example["upos"][0] == "NOUN"
        assert example["head"][0] == "0"
        assert example["deprel"][0] == "root"
