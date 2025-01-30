import requests
from typing import TypedDict
import logging
from create_idiom_dataset.utils import filter_and_normalize_idiom_df
from tqdm import tqdm
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class UntranslatedIdiom(TypedDict):
    source_idiom: str
    source_lang: str
    target_lang: str


def get_translation(source_idiom: str, source_lang: str, target_lang: str) -> str:
    payload = {"q": source_idiom, "langpair": f"{source_lang}|{target_lang}"}
    url = "https://apertium.org/apy/translate"

    response = requests.get(url, params=payload)
    if response.ok:
        return response.json()["responseData"]["translatedText"]
    else:
        logger.warning("Couldn't get translation for idiom %s", source_idiom)
        logger.warning(response)
        return ""


def get_idiom_translations(
    idiom_df: pd.DataFrame,
    save_every: int,
    special_chars: list[str],
    min_num_words: int,
    translated_idioms_file: Path,
) -> pd.DataFrame:
    translation_missing = idiom_df[idiom_df.idiom.isnull()]
    logger.debug(
        "Total number of idioms: %s Number of idioms missing translation: %s",
        len(idiom_df),
        len(translation_missing),
    )
    every = 0
    for tup in tqdm(translation_missing.itertuples(), total=len(translation_missing)):
        target_idiom = get_translation(
            source_idiom=tup.source_idiom,
            source_lang=tup.source_language,
            target_lang=tup.language,
        )
        idiom_df.at[tup.Index, "idiom"] = target_idiom

        every += 1
        if every % save_every == 0:
            logger.debug("Saving idiom_df to file %s", translated_idioms_file)
            idiom_df.to_csv(translated_idioms_file, index=False)

    idiom_df.to_csv(translated_idioms_file, index=False)

    logger.info("Filtering and normalizing translated idioms")
    # Filter and normalize the translated idioms
    idiom_df = filter_and_normalize_idiom_df(
        idiom_df=idiom_df,
        special_chars=special_chars,
        min_num_words=min_num_words,
    )

    return idiom_df
