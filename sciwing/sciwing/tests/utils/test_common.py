import sciwing.constants as constants
from sciwing.utils.common import *
import pytest
import pathlib
from sciwing.engine.engine import Engine

FILES = constants.FILES
PATHS = constants.PATHS

SECTLABEL_FILENAME = FILES["SECT_LABEL_FILE"]
GENERIC_SECTION_TRAIN_FILE = FILES["GENERIC_SECTION_TRAIN_FILE"]
PARSCIT_TRAIN_FILE = FILES["PARSCIT_TRAIN_FILE"]
CORA_FILE = FILES["CORA_FILE"]
DATA_DIR = PATHS["DATA_DIR"]


@pytest.fixture
def get_generic_sect_json():
    generic_sect_json = convert_generic_sect_to_json(GENERIC_SECTION_TRAIN_FILE)
    return generic_sect_json


@pytest.fixture
def get_conll_lines():
    citation_strings = convert_parscit_to_conll(pathlib.Path(PARSCIT_TRAIN_FILE))
    return citation_strings


class TestCommon:
    """
    1. Test to make sure the dicts are full
    2. Test to count the number of files - 40 papers
    """

    def test_text_not_empty(self):
        output_json = convert_sectlabel_to_json(SECTLABEL_FILENAME)
        output = output_json["parse_sect"]

        text = [bool(each_line["text"]) for each_line in output]
        assert all(text)

    def test_label_not_empty(self):
        output_json = convert_sectlabel_to_json(SECTLABEL_FILENAME)
        output = output_json["parse_sect"]

        labels = [bool(each_line["label"]) for each_line in output]
        assert all(labels)

    def test_filecount(self):
        output_json = convert_sectlabel_to_json(SECTLABEL_FILENAME)
        output = output_json["parse_sect"]

        file_numbers = [each_line["file_no"] for each_line in output]
        file_numbers = set(file_numbers)
        assert len(file_numbers) == 40  # number of files expected

    def test_sectlabel_sciwing_clf_format_lines_labels_not_empty(self, tmp_path):
        tmp_dir = tmp_path / "temp"
        tmp_dir.mkdir()
        try:
            convert_sectlabel_to_sciwing_clf_format(SECTLABEL_FILENAME, tmp_dir)
            with open(tmp_dir / "sectLabel.train", "r") as fp:
                for line in fp:
                    text, label = line.split("###")
                    assert text.strip() != ""
                    assert label.strip() != ""
        except:
            pytest.fail(
                "Failed to write SectLabel file in Sciwing classification format"
            )

    def test_genericsect_sciwing_clf_format_lines_labels_not_empty(self, tmp_path):
        tmp_dir = tmp_path / "temp"
        tmp_dir.mkdir()

        try:
            convert_generic_sect_to_sciwing_clf_format(
                GENERIC_SECTION_TRAIN_FILE, tmp_dir
            )
            with open(tmp_dir / "genericSect.train", "r") as fp:
                for line in fp:
                    text, label = line.split("###")
                    assert bool(text.strip())
                    assert bool(label.strip())

            with open(tmp_dir / "genericSect.dev", "r") as fp:
                for line in fp:
                    text, label = line.split("###")
                    assert bool(text.strip())
                    assert bool(label.strip())

            with open(tmp_dir / "genericSect.test", "r") as fp:
                for line in fp:
                    text, label = line.split("###")
                    assert bool(text.strip())
                    assert bool(label.strip())
        except:
            pytest.fail(
                f"Failed to write GenericSect file in SciWING classification format"
            )

    @pytest.mark.parametrize("random_state", [1729, None])
    def test_stratified_split_returns_right_split(self, random_state):
        lines = ["a"] * 100
        labels = ["label"] * 100

        (
            (train_lines, train_labels),
            (dev_lines, dev_labels),
            (test_lines, test_labels),
        ) = get_train_dev_test_stratified_split(
            lines=lines, labels=labels, random_state=random_state
        )

        assert len(train_lines) == len(train_labels) == 80
        assert len(dev_lines) == len(dev_labels) == 10
        assert len(test_lines) == len(test_labels) == 10

    def test_merge_dictionaries_empty(self):
        a = {}
        b = {"a": 0, "b": 1}
        a_b = merge_dictionaries_with_sum(a, b)
        expected = {"a": 0, "b": 1}
        assert a_b == expected

    def test_merge_dictionaries_one_zero(self):
        a = {"a": 0}
        b = {"a": 0, "b": 1}
        a_b = merge_dictionaries_with_sum(a, b)
        expected = {"a": 0, "b": 1}
        assert a_b == expected

    def test_merge_two_full_dictionaries(self):
        a = {"a": 1, "b": 2}
        b = {"a": 2, "b": 4, "c": 0}
        expected = {"a": 3, "b": 6, "c": 0}
        a_b = merge_dictionaries_with_sum(a, b)
        assert a_b == expected

    def test_pack_to_length_text_lower(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 10
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=False,
        )
        assert (
            tokenized_text_padded
            == ["i", "am", "going", "to", "write", "tests"] + ["<PAD>"] * 4
        )

    def test_pack_to_length_text_higher(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 3
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=False,
        )
        assert tokenized_text_padded == ["i", "am", "going"]

    def test_pack_to_length_text_equal(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 6
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=False,
        )
        assert tokenized_text_padded == tokenized_text

    def test_pack_to_length_text_lower_with_start_end_token(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 10
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=True,
            start_token="<SOS>",
            end_token="<EOS>",
        )
        assert (
            tokenized_text_padded
            == ["<SOS>", "i", "am", "going", "to", "write", "tests", "<EOS>"]
            + ["<PAD>"] * 2
        )

    def test_pack_to_length_text_higher_with_start_end_token(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 3
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=True,
            start_token="<SOS>",
            end_token="<EOS>",
        )
        assert tokenized_text_padded == ["<SOS>", "i", "<EOS>"]

    def test_pack_to_length_text_equal_with_start_end_token(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 6
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=True,
            start_token="<SOS>",
            end_token="<EOS>",
        )
        assert tokenized_text_padded == ["<SOS>", "i", "am", "going", "to", "<EOS>"]

    def test_pack_to_length_max_length_lt_2_add_start_end_token(self):
        tokenized_text = ["i", "am", "going", "to", "write", "tests"]
        length = 2
        tokenized_text_padded = pack_to_length(
            tokenized_text=tokenized_text,
            max_length=length,
            pad_token="<PAD>",
            add_start_end_token=True,
            start_token="<SOS>",
            end_token="<EOS>",
        )

        assert tokenized_text_padded == ["<SOS>", "<EOS>"]

    def test_convert_generic_sect_non_empty(self, get_generic_sect_json):
        """
        Make sure that the generic section header has both header and label filled
        """
        generic_sect_json = get_generic_sect_json
        lines = generic_sect_json["generic_sect"]
        for line in lines:
            header = line["header"]
            label = line["label"]
            assert bool(header.strip())
            assert bool(label.strip())

    def test_generic_sect_num_headers(self, get_generic_sect_json):
        generic_sect_json = get_generic_sect_json
        lines = generic_sect_json["generic_sect"]
        count = [line["line_no"] for line in lines]

        # TODO: remove -209 if you get proper train data. The keyword category is missing
        assert len(set(count)) == 2366 - (209)

    def test_generic_sect_num_papers(self, get_generic_sect_json):
        generic_sect_json = get_generic_sect_json
        lines = generic_sect_json["generic_sect"]
        file_nos = [line["file_no"] for line in lines]
        assert len(set(file_nos)) == 211

    def test_generic_sect_label_counts(self, get_generic_sect_json):
        generic_sect_json = get_generic_sect_json
        lines = generic_sect_json["generic_sect"]
        abstract_lines = filter(lambda line: line["label"] == "abstract", lines)
        categories_lines = filter(
            lambda line: line["label"] == "categories-and-subject-descriptors", lines
        )
        general_terms_lines = filter(
            lambda line: line["label"] == "general-terms", lines
        )
        keywords_lines = filter(lambda line: line["label"] == "keywords", lines)
        introduction_lines = filter(lambda line: line["label"] == "introduction", lines)
        background_lines = filter(lambda line: line["label"] == "background", lines)
        related_work_lines = filter(
            lambda line: line["label"] == "related-works", lines
        )
        methodology_lines = filter(lambda line: line["label"] == "method", lines)
        evaluation_lines = filter(lambda line: line["label"] == "evaluation", lines)
        discussion_lines = filter(lambda line: line["label"] == "discussions", lines)
        conclusion_lines = filter(lambda line: line["label"] == "conclusions", lines)
        ack_lines = filter(lambda line: line["label"] == "acknowledgments", lines)
        ref_lines = filter(lambda line: line["label"] == "references", lines)

        assert len(list(abstract_lines)) == 210
        assert len(list(categories_lines)) == 165
        assert len(list(general_terms_lines)) == 142
        assert len(list(introduction_lines)) == 210
        assert len(list(background_lines)) == 28
        assert len(list(related_work_lines)) == 105
        assert len(list(methodology_lines)) == 608
        assert len(list(evaluation_lines)) == 151
        assert len(list(discussion_lines)) == 36
        assert len(list(conclusion_lines)) == 189
        assert len(list(ack_lines)) == 102
        assert len(list(ref_lines)) == 211

        # TODO: There are no keyword lines in the file.
        assert len(list(keywords_lines)) == 0

    def test_convert_parscit_to_conll_format_gets_data(self, get_conll_lines):
        citations = get_conll_lines
        lines = [bool(citation["citation_string"].strip()) for citation in citations]
        assert sum(lines) > 0

    def test_convert_parscit_conll_has_4_columns(self, get_conll_lines):
        citations = get_conll_lines
        lines = []
        for citation in citations:
            lines.extend(citation["word_tags"])
        assert all([len(line.split()) == 4 for line in lines])

    def test_cora_has_500_citations(self):
        citations = convert_parscit_to_conll(pathlib.Path(CORA_FILE))
        assert len(citations) == 500

    def test_cora_write_file_works(self):
        cora_path = pathlib.Path(DATA_DIR, "test_cora_conll_write.txt")
        try:
            write_cora_to_conll_file(cora_path)
        except:
            pytest.fail("Failed to write cora file to conll format")
        else:
            cora_path.unlink()

    def test_parscit_train_write_file_works(self):
        parscit_train_path = pathlib.Path(DATA_DIR, "test_parscit_conll_write.txt")

        try:
            write_parscit_to_conll_file(parscit_train_path)
        except:
            pytest.fail("Failed to write parscit train conll format file")
        else:
            parscit_train_path.unlink()

    def test_parscit_sciwing_seqlabel_format_works(self, tmp_path):
        tmp_dir = tmp_path / "temp"
        tmp_dir.mkdir()

        try:
            convert_parscit_to_sciwing_seqlabel_format(
                parscit_train_filepath=PARSCIT_TRAIN_FILE, output_dir=tmp_dir
            )
            with open(tmp_dir / "parscit.train") as fp:
                for line in fp:
                    word_tags = line.split()
                    for word_tag in word_tags:
                        word, tag = word_tag.split("###")
                        assert bool(word.strip())
                        assert bool(tag.split())
        except:
            pytest.fail(
                f"SciWING parscit sequential labelling formatting does not work"
            )

    @pytest.mark.parametrize(
        "classname, modulename", [(Engine.__name__, Engine.__module__)]
    )
    def test_create_class(self, classname, modulename):
        cls = create_class(classname, modulename)
        assert cls.__name__ == classname
        assert cls.__module__ == modulename

    def test_create_class_raises_module_not_found_error(self):
        with pytest.raises(ModuleNotFoundError):
            create_class("dummy", "dummy")

    def test_create_class_raises_class_not_found_error(self):
        with pytest.raises(AttributeError):
            create_class(classname="dummy", module_name=Engine.__module__)
