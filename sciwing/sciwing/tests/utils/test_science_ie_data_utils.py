import sciwing.constants as constants
import pytest
from sciwing.utils.science_ie_data_utils import ScienceIEDataUtils
import pathlib
from collections import Counter
import spacy

FILES = constants.FILES
SCIENCE_IE_TRAIN_FOLDER = FILES["SCIENCE_IE_TRAIN_FOLDER"]


@pytest.fixture
def setup_science_ie_train_data_utils():
    utils = ScienceIEDataUtils(pathlib.Path(SCIENCE_IE_TRAIN_FOLDER))
    return utils


class TestScienceIEDataUtils:
    def test_file_ids_different(self, setup_science_ie_train_data_utils):
        utils = setup_science_ie_train_data_utils
        file_ids = utils.get_file_ids()
        counter_file_ids = Counter(file_ids)
        assert all([count == 1 for count in counter_file_ids.values()])

    def test_all_text_read(self, setup_science_ie_train_data_utils):
        utils = setup_science_ie_train_data_utils
        file_ids = utils.get_file_ids()
        for file_id in file_ids:
            text = utils.get_text_from_fileid(file_id)
            assert len(text) > 0

    @pytest.mark.parametrize("entity_type", ["Task", "Process", "Material"])
    def test_get_annotations_for_entity(
        self, setup_science_ie_train_data_utils, entity_type
    ):
        utils = setup_science_ie_train_data_utils
        file_ids = utils.get_file_ids()

        for file_id in file_ids:
            annotations = utils._get_annotations_for_entity(
                file_id=file_id, entity=entity_type
            )
            assert all([len(annotation["words"]) > 0 for annotation in annotations])

    @pytest.mark.parametrize("entity_type", ["Task", "Process", "Material"])
    def test_annotation_id_starts_with_t(
        self, setup_science_ie_train_data_utils, entity_type
    ):
        utils = setup_science_ie_train_data_utils
        file_ids = utils.get_file_ids()

        for file_id in file_ids:
            annotations = utils._get_annotations_for_entity(
                file_id=file_id, entity=entity_type
            )
            assert all(
                [
                    annotation["entity_number"].startswith("T")
                    for annotation in annotations
                ]
            )

    @pytest.mark.parametrize(
        "text, annotations, expected_lines",
        [
            (
                "word",
                [{"start": 0, "end": 4, "tag": "Process"}],
                ["word U-Process U-Process U-Process"],
            ),
            (
                "word word",
                [{"start": 0, "end": 4, "tag": "Process"}],
                [
                    "word U-Process U-Process U-Process",
                    "word O-Process O-Process O-Process",
                ],
            ),
            (
                "word. word",
                [{"start": 0, "end": 5, "tag": "Process"}],
                [
                    "word B-Process B-Process B-Process",
                    ". L-Process L-Process L-Process",
                    "word O-Process O-Process O-Process",
                ],
            ),
            (
                "word word",
                [{"start": 0, "end": 9, "tag": "Process"}],
                [
                    "word B-Process B-Process B-Process",
                    "word L-Process L-Process L-Process",
                ],
            ),
            (
                "word. word",
                [{"start": 0, "end": 10, "tag": "Process"}],
                [
                    "word B-Process B-Process B-Process",
                    ". I-Process I-Process I-Process",
                    "word L-Process L-Process L-Process",
                ],
            ),
            (
                "word. word word",
                [{"start": 0, "end": 10, "tag": "Process"}],
                [
                    "word B-Process B-Process B-Process",
                    ". I-Process I-Process I-Process",
                    "word L-Process L-Process L-Process",
                    "word O-Process O-Process O-Process",
                ],
            ),
            (
                "(word) word word",
                [{"start": 1, "end": 5, "tag": "Process"}],
                [
                    "( O-Process O-Process O-Process",
                    "word U-Process U-Process U-Process",
                    ") O-Process O-Process O-Process",
                    "word O-Process O-Process O-Process",
                    "word O-Process O-Process O-Process",
                ],
            ),
            (
                "(word) word word",
                [{"start": 1, "end": 16, "tag": "Process"}],
                [
                    "( O-Process O-Process O-Process",
                    "word B-Process B-Process B-Process",
                    ") I-Process I-Process I-Process",
                    "word I-Process I-Process I-Process",
                    "word L-Process L-Process L-Process",
                ],
            ),
            (
                "word word word",
                [],
                [
                    "word O-Process O-Process O-Process",
                    "word O-Process O-Process O-Process",
                    "word O-Process O-Process O-Process",
                ],
            ),
            (
                "Poor oxidation behavior",
                [{"start": 5, "end": 14, "tag": "Process"}],
                [
                    "Poor O-Process O-Process O-Process",
                    "oxidation U-Process U-Process U-Process",
                    "behavior O-Process O-Process O-Process",
                ],
            ),
        ],
    )
    def test_private_get_bilou_lines_for_entity(
        self, setup_science_ie_train_data_utils, text, annotations, expected_lines
    ):
        utils = setup_science_ie_train_data_utils
        lines = utils._get_bilou_lines_for_entity(
            text=text, annotations=annotations, entity="Process"
        )
        for idx, line in enumerate(lines):
            assert line == expected_lines[idx]

    @pytest.mark.parametrize("entity_type", ["Task", "Process", "Material"])
    def test_get_bilou_lines_runs(self, setup_science_ie_train_data_utils, entity_type):
        utils = setup_science_ie_train_data_utils
        try:
            file_ids = utils.file_ids
            for file_id in file_ids:
                utils.get_bilou_lines_for_entity(file_id=file_id, entity=entity_type)
        except:
            pytest.fail("Failed to run bilou lines")

    # There are many anomalies in the files that are provided
    # Sometimes a huge set of words are marked Process
    # some subset of the set are again marked as process
    # These wont get tagged tewice by our system
    # the files that are tested here are manually tested for behavior
    # to automate the process I have included them here.
    @pytest.mark.parametrize("entity_type", ["Process"])
    @pytest.mark.parametrize("file_id", ["S0010938X1500195X"])
    def test_get_bilou_lines(
        self, setup_science_ie_train_data_utils, entity_type, file_id
    ):
        utils = setup_science_ie_train_data_utils

        # test whether all the annotations that you get for different file ids
        # are present as either U, B I or L tag

        annotations = utils._get_annotations_for_entity(
            file_id=file_id, entity=entity_type
        )
        bilou_lines = utils.get_bilou_lines_for_entity(
            file_id=file_id, entity=entity_type
        )
        nlp = spacy.load("en_core_web_sm")

        annotation_words = []
        for annotation in annotations:
            words = annotation["words"]
            words = words.strip()
            doc = nlp(words)
            words = [tok.text for tok in doc]
            annotation_words.extend(words)

        bilou_words_without_o = []
        for bilou_line in bilou_lines:
            word, _, _, tag = bilou_line.split()
            if not tag.startswith("O"):
                bilou_words_without_o.append(word)

        print(annotation_words)
        print(bilou_words_without_o)
        assert len(annotation_words) == len(bilou_words_without_o)

    @pytest.mark.parametrize("entity_type", ["Task", "Process", "Material"])
    def test_get_sentence_wise_bilou_lines_works(
        self, setup_science_ie_train_data_utils, entity_type
    ):
        utils = setup_science_ie_train_data_utils
        try:
            file_ids = utils.file_ids
            for file_id in file_ids:
                sentence_wise_bilou_lines = utils.get_sentence_wise_bilou_lines(
                    file_id=file_id, entity_type=entity_type
                )
        except:
            pytest.fail("Failed to run bilou lines")

    def test_write_ann_file_from_conll_file(
        self, tmpdir, setup_science_ie_train_data_utils
    ):
        utils = setup_science_ie_train_data_utils

        conll_lines = [
            "word B-Task B-Process B-Material",
            "word I-Task I-Process I-Material",
            "word L-Task L-Process L-Material",
        ]

        dummy_dir = tmpdir.mkdir("fake_dir")
        dummy_conll = dummy_dir.join("dummy.conll")
        dummy_ann = dummy_dir.join("dummy.ann")

        dummy_conll.write("\n".join(conll_lines))
        conll_filepath = pathlib.Path(dummy_conll)
        ann_filepath = pathlib.Path(dummy_ann)

        utils.write_ann_file_from_conll_file(
            conll_filepath=conll_filepath,
            ann_filepath=ann_filepath,
            text="word word word",
        )

        with open(ann_filepath) as fp:
            num_lines = sum([1 for line in fp])
            assert num_lines == 3
