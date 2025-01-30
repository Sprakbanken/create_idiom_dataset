from collections import defaultdict
from pathlib import Path
from nb_tokenizer import tokenize
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


def create_sequence_graph(tokenized_idioms: list[list[str]]) -> dict[str, str]:
    sequence_graph = defaultdict(dict)

    for sentence in tokenized_idioms:
        prev_dict = sequence_graph
        for i, word in enumerate(sentence):
            if word not in prev_dict:
                prev_dict[word] = {}
            prev_dict = prev_dict[word]
    return sequence_graph


def flatten_sequence_graph(d: dict) -> dict | str:
    """Flattens sequence graph by concatenating sequences of parent + single child node tokens."""
    if d == {}:
        return ""

    flat_dict = {}
    for k, v in d.items():
        flat_v = flatten_sequence_graph(v)
        if type(flat_v) is str:
            if flat_v:
                flat_dict[f"{k} {flat_v}"] = ""
            else:
                flat_dict[k] = ""
        elif len(flat_v) == 1:
            flat_v_k = list(flat_v.keys())[0]
            flat_dict[f"{k} {flat_v_k}"] = flat_v[flat_v_k]
        else:
            flat_dict[k] = flat_v
    return flat_dict


def write_sequence_graphs(
    graph_dir: Path, idiom_df: pd.DataFrame, filename_prefix: str
):
    tokenized_idioms = [tokenize(e) for e in idiom_df.idiom]

    logger.info("Number of %s idioms: %s", filename_prefix, len(tokenized_idioms))

    sequence_graph = create_sequence_graph(tokenized_idioms=tokenized_idioms)
    flat_sequence_graph = flatten_sequence_graph(sequence_graph)

    logger.info(
        "Number of sequence graphs (i.e unique idiom starts): %s", len(sequence_graph)
    )

    with open(graph_dir / f"{filename_prefix}_idioms_sequence_graph.json", "w+") as f:
        json.dump(sequence_graph, f, ensure_ascii=False, indent=4)

    with open(
        graph_dir / f"{filename_prefix}_idioms_flat_sequence_graph.json", "w+"
    ) as f:
        json.dump(flat_sequence_graph, f, ensure_ascii=False, indent=4)
