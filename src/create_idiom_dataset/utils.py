import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import logging
from nb_tokenizer import tokenize
import sys

logger = logging.getLogger(__name__)


def setup_logging(log_level: str, source_script: str):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_filename = log_dir / f"{current_time}_{source_script}.log"

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(stream=sys.stdout),
        ],
    )


def clean_ocr(token: str) -> str:
    """Replace common OCR mistakes with correct tokens"""

    match token:
        case "seiv":
            return "selv"
        case "stjemesmeli":
            return "stjernsmell"
        case "papirkvem":
            return "papirkvern"

    if token.startswith("bame") or token.endswith("bam"):
        return token.replace("bam", "barn")
    if "stjeme" in token or "fjeme" in token or "hjeme" in token:
        return token.replace("eme", "erne")
    if token.startswith("bjøme") or token.startswith("øme"):
        return token.replace("øme", "ørne")
    return token


def comma_normalize(sentence: str) -> str:
    """Put a space before all tokens except commas and replace common OCR errors"""
    tokens = tokenize(sentence)
    s = ""
    for t in tokens:
        if t == ",":
            s += t
        else:
            s += " " + clean_ocr(t)
    if s[0] == " ":
        return s[1:]
    return s


def normalize_idiom_df(idiom_df: pd.DataFrame) -> pd.DataFrame:
    logger.debug("Unique idioms before normalization %s", len(idiom_df.idiom.unique()))
    # strip whitespace
    idiom_df["idiom"] = idiom_df.idiom.apply(lambda x: x.strip())

    # decapitalize first letter
    idiom_df["idiom"] = idiom_df.idiom.apply(lambda idiom: idiom[0].lower() + idiom[1:])

    # comma normalize
    idiom_df["idiom"] = idiom_df.idiom.apply(comma_normalize)

    logger.debug("Unique idioms after normalization %s", len(idiom_df.idiom.unique()))

    idiom_df = idiom_df.drop_duplicates()
    logger.debug("Idiom dataframe length after dropping duplicates %s", len(idiom_df))
    return idiom_df


def filter_idiom_df(
    idiom_df: pd.DataFrame,
    special_chars: list[str],
    min_num_words: int,
) -> pd.DataFrame:
    logger.debug(
        "Idiom dataframe length before special character filtering %s", len(idiom_df)
    )
    # remove idioms with special characters
    idiom_df = idiom_df[
        idiom_df.idiom.apply(lambda x: all([char not in x for char in special_chars]))
    ]
    logger.debug(
        "Idiom dataframe length after special character filtering %s", len(idiom_df)
    )

    # remove idioms with less than min_num_words
    idiom_df = idiom_df[
        idiom_df.idiom.apply(lambda x: len(x.split(" ")) >= min_num_words)
    ]
    logger.debug("Idiom dataframe length after length filtering %s", len(idiom_df))

    idiom_df = idiom_df.drop_duplicates()
    logger.debug("Idiom dataframe length after dropping duplicates %s", len(idiom_df))
    return idiom_df


def filter_and_normalize_idiom_df(
    idiom_df: pd.DataFrame, special_chars: list[str], min_num_words: int
) -> pd.DataFrame:
    idiom_df = filter_idiom_df(
        idiom_df=idiom_df,
        special_chars=special_chars,
        min_num_words=min_num_words,
    )
    idiom_df = normalize_idiom_df(idiom_df=idiom_df)
    return idiom_df
