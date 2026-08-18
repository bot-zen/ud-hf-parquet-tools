#!/usr/bin/env python3
"""Tests for CoNLL-U reconstruction functions."""

from io import StringIO

# Import from pre-loaded module (via conftest.py)
from ud_template import example_to_conllu, write_conllu


class TestExampleToConllu:
    """Test example_to_conllu() function."""

    def test_simple_sentence(self):
        """Simple sentence should be reconstructed correctly."""
        example = {
            "sent_id": "test-001",
            "text": "Hello world.",
            "comments": [],
            "tokens": ["Hello", "world", "."],
            "lemmas": ["hello", "world", "."],
            "upos": ["INTJ", "NOUN", "PUNCT"],
            "xpos": [None, None, None],
            "feats": [None, None, None],
            "head": [0, 1, 1],
            "deprel": ["root", "vocative", "punct"],
            "deps": [None, None, None],
            "misc": [None, None, None],
            "mwt": [],
            "empty_nodes": [],
        }

        result = example_to_conllu(example)

        assert "# sent_id = test-001" in result
        assert "# text = Hello world." in result
        assert "1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\t_" in result
        assert "2\tworld\tworld\tNOUN\t_\t_\t1\tvocative\t_\t_" in result
        assert "3\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_" in result
        assert result.endswith("\n")  # Should end with blank line

    def test_sentence_with_mwt(self):
        """Sentence with MWT should reconstruct MWT line before tokens."""
        example = {
            "sent_id": "test-002",
            "text": "Je l'ai vu.",
            "comments": [],
            "tokens": ["l'", "ai", "vu"],
            "lemmas": ["le", "avoir", "voir"],
            "upos": ["DET", "AUX", "VERB"],
            "xpos": [None, None, None],
            "feats": [None, None, None],
            "head": [2, 3, 0],
            "deprel": ["det", "aux", "root"],
            "deps": [None, None, None],
            "misc": ["SpaceAfter=No", None, None],
            "mwt": [{"id": "1-2", "form": "l'ai", "feats": None, "misc": None}],
            "empty_nodes": [],
        }

        result = example_to_conllu(example)

        # MWT line should appear before token lines
        lines = result.split("\n")
        mwt_line_idx = None
        token1_line_idx = None

        for i, line in enumerate(lines):
            if line.startswith("1-2\t"):
                mwt_line_idx = i
            if line.startswith("1\tl'\t"):
                token1_line_idx = i

        assert mwt_line_idx is not None, "MWT line not found"
        assert token1_line_idx is not None, "Token line not found"
        assert mwt_line_idx < token1_line_idx, "MWT line should come before token line"

    def test_sentence_with_empty_node(self):
        """Sentence with empty node should reconstruct empty node after token."""
        example = {
            "sent_id": "test-003",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": ["NOUN"],
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [
                {
                    "id": "1.1",
                    "form": "is",
                    "lemma": "be",
                    "upos": "AUX",
                    "xpos": "_",
                    "feats": "_",
                    "head": "1",
                    "deprel": "cop",
                    "deps": "_",
                    "misc": "_",
                }
            ],
        }

        result = example_to_conllu(example)

        # Empty node line should appear after token line
        lines = result.split("\n")
        token_line_idx = None
        empty_node_line_idx = None

        for i, line in enumerate(lines):
            if line.startswith("1\tTest\t"):
                token_line_idx = i
            if line.startswith("1.1\t"):
                empty_node_line_idx = i

        assert token_line_idx is not None, "Token line not found"
        assert empty_node_line_idx is not None, "Empty node line not found"
        assert empty_node_line_idx > token_line_idx, "Empty node should come after token"

    def test_sentence_with_comments(self):
        """Sentence with comments should reconstruct comments before sent_id."""
        example = {
            "sent_id": "test-004",
            "text": "Test",
            "comments": ["newdoc id = doc1", "newpar id = par1"],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": ["NOUN"],
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [],
        }

        result = example_to_conllu(example)

        lines = result.split("\n")

        # Comments should appear before sent_id
        assert "# newdoc id = doc1" in result
        assert "# newpar id = par1" in result

        # Check order
        newdoc_idx = None
        newpar_idx = None
        sent_id_idx = None

        for i, line in enumerate(lines):
            if "newdoc id = doc1" in line:
                newdoc_idx = i
            if "newpar id = par1" in line:
                newpar_idx = i
            if "sent_id = test-004" in line:
                sent_id_idx = i

        assert newdoc_idx < newpar_idx < sent_id_idx

    def test_optional_fields_with_values(self):
        """Optional fields with values should be reconstructed correctly."""
        example = {
            "sent_id": "test-005",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": ["NOUN"],
            "xpos": ["NN"],
            "feats": ["Number=Sing"],
            "head": [0],
            "deprel": ["root"],
            "deps": ["4:nsubj"],
            "misc": ["SpaceAfter=No"],
            "mwt": [],
            "empty_nodes": [],
        }

        result = example_to_conllu(example)

        assert "1\tTest\ttest\tNOUN\tNN\tNumber=Sing\t0\troot\t4:nsubj\tSpaceAfter=No" in result

    def test_blank_line_at_end(self):
        """Reconstructed output should end with exactly one blank line."""
        example = {
            "sent_id": "test-006",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": ["NOUN"],
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [],
        }

        result = example_to_conllu(example)

        # Should end with one blank line (two newlines at end)
        assert result.endswith("\n\n")
        assert not result.endswith("\n\n\n")

    def test_legacy_classlabel_upos_reconstruction(self):
        """Old parquet outputs with ClassLabel UPOS indices should still reconstruct."""
        example = {
            "sent_id": "test-007",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": [0],
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [],
        }

        result = example_to_conllu(example, upos_names=["NOUN"])

        assert "1\tTest\ttest\tNOUN\t_\t_\t0\troot\t_\t_" in result


class TestWriteConllu:
    """Test write_conllu() function."""

    def test_write_to_stdout(self, capsys):
        """Writing to stdout should work correctly."""

        # Create mock dataset
        class MockDataset:
            def __init__(self, examples):
                self.examples = examples
                self.features = {
                    "upos": type(
                        "ClassLabel",
                        (),
                        {
                            "names": [
                                "NOUN",
                                "PUNCT",
                                "ADP",
                                "NUM",
                                "SYM",
                                "SCONJ",
                                "ADJ",
                                "PART",
                                "DET",
                                "CCONJ",
                                "PROPN",
                                "PRON",
                                "X",
                                "_",
                                "ADV",
                                "INTJ",
                                "VERB",
                                "AUX",
                            ]
                        },
                    )()
                }

            def __iter__(self):
                return iter(self.examples)

        example = {
            "sent_id": "test-001",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": [0],  # NOUN
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [],
        }

        dataset = MockDataset([example])
        write_conllu(dataset, "-")

        captured = capsys.readouterr()
        assert "# sent_id = test-001" in captured.out
        assert "# text = Test" in captured.out

    def test_write_to_file(self, tmp_path):
        """Writing to file should work correctly."""

        class MockDataset:
            def __init__(self, examples):
                self.examples = examples
                self.features = {
                    "upos": type(
                        "ClassLabel",
                        (),
                        {
                            "names": [
                                "NOUN",
                                "PUNCT",
                                "ADP",
                                "NUM",
                                "SYM",
                                "SCONJ",
                                "ADJ",
                                "PART",
                                "DET",
                                "CCONJ",
                                "PROPN",
                                "PRON",
                                "X",
                                "_",
                                "ADV",
                                "INTJ",
                                "VERB",
                                "AUX",
                            ]
                        },
                    )()
                }

            def __iter__(self):
                return iter(self.examples)

        example = {
            "sent_id": "test-001",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": [0],
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [],
        }

        dataset = MockDataset([example])
        output_file = tmp_path / "output.conllu"

        write_conllu(dataset, str(output_file))

        content = output_file.read_text()
        assert "# sent_id = test-001" in content
        assert "# text = Test" in content

    def test_write_to_buffer(self):
        """Writing to buffer should work correctly."""

        class MockDataset:
            def __init__(self, examples):
                self.examples = examples
                self.features = {
                    "upos": type(
                        "ClassLabel",
                        (),
                        {
                            "names": [
                                "NOUN",
                                "PUNCT",
                                "ADP",
                                "NUM",
                                "SYM",
                                "SCONJ",
                                "ADJ",
                                "PART",
                                "DET",
                                "CCONJ",
                                "PROPN",
                                "PRON",
                                "X",
                                "_",
                                "ADV",
                                "INTJ",
                                "VERB",
                                "AUX",
                            ]
                        },
                    )()
                }

            def __iter__(self):
                return iter(self.examples)

        example = {
            "sent_id": "test-001",
            "text": "Test",
            "comments": [],
            "tokens": ["Test"],
            "lemmas": ["test"],
            "upos": [0],
            "xpos": [None],
            "feats": [None],
            "head": [0],
            "deprel": ["root"],
            "deps": [None],
            "misc": [None],
            "mwt": [],
            "empty_nodes": [],
        }

        dataset = MockDataset([example])
        buffer = StringIO()

        write_conllu(dataset, buffer)

        content = buffer.getvalue()
        assert "# sent_id = test-001" in content
        assert "# text = Test" in content
