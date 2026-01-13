#!/usr/bin/env python3
"""Tests for round-trip validation (CoNLL-U -> Parquet -> CoNLL-U)."""

# Import from pre-loaded modules (via conftest.py)
from generate_parquet import extract_examples_from_conllu
from ud_template import example_to_conllu


class TestRoundTrip:
    """Test that data can be round-tripped 100% verbatim."""

    def normalize_conllu(self, text: str) -> str:
        """Normalize CoNLL-U for comparison (strip blank lines at end)."""
        lines = text.strip().split("\n")
        # Remove trailing empty lines
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines) + "\n"

    def test_simple_sentence_roundtrip(self, tmp_path):
        """Simple sentence should round-trip verbatim."""
        original = """# sent_id = test-001
# text = Hello world.
1	Hello	hello	INTJ	_	_	0	root	_	_
2	world	world	NOUN	_	_	1	vocative	_	_
3	.	.	PUNCT	_	_	1	punct	_	_

"""
        # Write original
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        # Extract
        examples = extract_examples_from_conllu(str(test_file))
        assert len(examples) == 1

        # Reconstruct
        reconstructed = example_to_conllu(examples[0])

        # Compare (normalize for comparison)
        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)

    def test_mwt_roundtrip(self, tmp_path):
        """Sentence with MWT should round-trip verbatim."""
        original = """# sent_id = test-002
# text = Je l'ai vu.
1-2	l'ai	_	_	_	_	_	_	_	_
1	l'	le	DET	_	_	2	det	_	SpaceAfter=No
2	ai	avoir	AUX	_	_	3	aux	_	_
3	vu	voir	VERB	_	_	0	root	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        examples = extract_examples_from_conllu(str(test_file))
        reconstructed = example_to_conllu(examples[0])

        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)

    def test_empty_node_roundtrip(self, tmp_path):
        """Sentence with empty node should round-trip verbatim."""
        original = """# sent_id = test-003
# text = Test
1	Test	test	NOUN	_	_	0	root	_	_
1.1	is	be	AUX	_	_	1	cop	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        examples = extract_examples_from_conllu(str(test_file))
        reconstructed = example_to_conllu(examples[0])

        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)

    def test_metadata_roundtrip(self, tmp_path):
        """Sentence with metadata comments should round-trip verbatim."""
        original = """# newdoc id = doc1
# newpar id = par1
# sent_id = test-004
# text = Test
1	Test	test	NOUN	_	_	0	root	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        examples = extract_examples_from_conllu(str(test_file))
        reconstructed = example_to_conllu(examples[0])

        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)

    def test_optional_fields_roundtrip(self, tmp_path):
        """Sentence with all optional fields should round-trip verbatim."""
        original = """# sent_id = test-005
# text = Test
1	Test	test	NOUN	NN	Number=Sing	0	root	4:nsubj	SpaceAfter=No

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        examples = extract_examples_from_conllu(str(test_file))
        reconstructed = example_to_conllu(examples[0])

        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)

    def test_complex_roundtrip(self, tmp_path):
        """Complex sentence with MWT, empty nodes, and metadata should round-trip."""
        original = """# newdoc id = doc1
# sent_id = test-006
# text = Je l'ai vu.
1-2	l'ai	_	_	_	_	_	_	_	_
1	l'	le	DET	_	_	2	det	_	SpaceAfter=No
2	ai	avoir	AUX	_	_	3	aux	_	_
2.1	été	être	AUX	_	_	2	aux	_	_
3	vu	voir	VERB	VBN	Number=Sing	0	root	4:nsubj	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        examples = extract_examples_from_conllu(str(test_file))
        reconstructed = example_to_conllu(examples[0])

        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)

    def test_multiple_sentences_roundtrip(self, tmp_path):
        """Multiple sentences should each round-trip correctly."""
        original = """# sent_id = 1
# text = First.
1	First	first	ADJ	_	_	0	root	_	SpaceAfter=No
2	.	.	PUNCT	_	_	1	punct	_	_

# sent_id = 2
# text = Second.
1	Second	second	ADJ	_	_	0	root	_	SpaceAfter=No
2	.	.	PUNCT	_	_	1	punct	_	_

"""
        test_file = tmp_path / "test.conllu"
        test_file.write_text(original)

        examples = extract_examples_from_conllu(str(test_file))
        assert len(examples) == 2

        # Reconstruct both
        reconstructed = ""
        for example in examples:
            reconstructed += example_to_conllu(example)  # Already ends with \n\n

        # Compare (should match original)
        assert self.normalize_conllu(original) == self.normalize_conllu(reconstructed)
