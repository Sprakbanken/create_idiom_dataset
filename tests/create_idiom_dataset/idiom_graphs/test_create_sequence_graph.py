from create_idiom_dataset.idiom_graphs import create_sequence_graph
import pytest


def test_empty_token_sequence_creates_empty_graph():
    tokenized_idioms = [[]]
    sequence_graph = create_sequence_graph(tokenized_idioms)
    assert sequence_graph == {}


@pytest.mark.parametrize(
    "tokenized_idioms", [[[""]], [["hei", "på", "deg"]], [["gurglegurle"]]]
)
def test_single_tokenlist_creates_single_root_graph(tokenized_idioms):
    assert len(create_sequence_graph(tokenized_idioms)) == 1


@pytest.mark.parametrize(
    "tokenized_idioms",
    [
        [["hei"], ["ho"]],
        [["hei"], ["hoi"], ["ho"]],
        [["hei", "hei", "hallo"], ["ho", "ho", "hoi"], ["hoi"]],
    ],
)
def test_tokenlists_without_overlap_creates_separate_graphs(tokenized_idioms):
    sequence_graph = create_sequence_graph(tokenized_idioms)
    assert len(sequence_graph) == len(tokenized_idioms)


@pytest.mark.parametrize(
    "tokenized_idioms, expected",
    [
        (  # TODO: maybe look into how to mark that idiom can end with 'hei'
            [["hei", "på", "deg"], ["hei"]],
            {"hei": {"på": {"deg": {}}}},
        ),
        ([["du", "da"], ["du", "du"]], {"du": {"da": {}, "du": {}}}),
    ],
)
def test_tokenlists_with_overlap_create_single_graph(tokenized_idioms, expected):
    assert create_sequence_graph(tokenized_idioms) == expected


@pytest.mark.parametrize(
    "tokenized_idioms, expected",
    [
        (
            [["snerk", "og", "herk"], ["satan", "og"], ["satan", "au"]],
            {"snerk": {"og": {"herk": {}}}, "satan": {"og": {}, "au": {}}},
        ),
        (
            [
                ["snerk", "og", "herk"],
                ["satan", "og", "julebrus"],
                ["satan", "au"],
                ["satan", "og", "au"],
            ],
            {
                "snerk": {"og": {"herk": {}}},
                "satan": {"og": {"julebrus": {}, "au": {}}, "au": {}},
            },
        ),
    ],
)
def test_tokenlists_with_and_without_overlap_create_multiple_graphs(
    tokenized_idioms, expected
):
    assert create_sequence_graph(tokenized_idioms) == expected
