import logging
from pathlib import Path
from create_idiom_dataset.utils import filter_and_normalize_idiom_df
import pandas as pd

logger = logging.getLogger(__name__)


def idiom_colletion_to_df(
    idiom_collection: Path, special_chars: list[str], min_num_words: int
) -> pd.DataFrame:
    idioms = [
        idiom
        for book in idiom_collection.iterdir()
        for idiom in book.read_text().split("\n")
    ]
    idiom_df = pd.DataFrame({"idiom": idioms})

    return filter_and_normalize_idiom_df(
        idiom_df=idiom_df,
        special_chars=special_chars,
        min_num_words=min_num_words,
    )
