import logging
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger(__name__)


def get_frequency(idiom: str):
    payload = {"q": f'"{idiom}"'}
    url = "https://api.nb.no/catalog/v1/items"

    response = requests.get(url, params=payload)
    if response.ok:
        return response.json()["page"]["totalElements"]
    else:
        logger.warning(response)
        return None


def get_idiom_frequencies(
    idiom_df: pd.DataFrame, save_every: int, frequency_file: Path
) -> pd.DataFrame:
    freq_missing = idiom_df[idiom_df.frequency.isnull()]
    logger.debug(
        "Total number of idioms: %s Number of idioms missing frequency: %s",
        len(idiom_df),
        len(freq_missing),
    )
    every = 0
    for tup in tqdm(freq_missing.itertuples(), total=len(freq_missing)):
        frequency = get_frequency(tup.idiom)
        idiom_df.at[tup.Index, "frequency"] = frequency

        every += 1
        if every % save_every == 0:
            logger.debug("Saving idiom_df to file")
            idiom_df.to_csv(frequency_file, index=False)
    idiom_df.to_csv(frequency_file, index=False)
    return idiom_df
