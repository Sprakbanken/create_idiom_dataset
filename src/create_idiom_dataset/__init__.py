from argparse import ArgumentParser
from pathlib import Path
import logging
from create_idiom_dataset.utils import setup_logging
from create_idiom_dataset.read_idiom_collection import idiom_colletion_to_df
from create_idiom_dataset.frequency_curation import get_idiom_frequencies
from create_idiom_dataset.translation import get_idiom_translations
from create_idiom_dataset.idiom_graphs import write_sequence_graphs
from create_idiom_dataset.idiom_completion_task import idiom_df_to_idiom_completion_task
from datasets import load_dataset
import pandas as pd

logger = logging.getLogger(__name__)

DATASETS_README_INFO = """
---
configs:
- config_name: default
  data_files:
  - split: test
    path: "data.jsonl"
- config_name: include_translated_idioms
  data_files:
  - split: test
    path: "original_and_translated_data.jsonl"
---
"""


def get_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "idiom_collection_dir",
        type=Path,
        help="Path to directory where idiom collection is stored",
    )
    parser.add_argument(
        "dataset_output_dir", type=Path, help="Path to output directory"
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["nob", "nno"],
        help="Languages to create dataset for (assuming idiom_collection_dir contains subdirectories for each language)",
    )

    parser.add_argument(
        "--special_chars",
        nargs="+",
        default=["(", "/", "*"],
        help="Filter out idioms that contain these characters",
    )
    parser.add_argument(
        "--min_num_words", type=int, default=3, help="Minimum number of words in idiom"
    )
    parser.add_argument(
        "--min_frequency", type=int, default=100, help="Minimum frequency"
    )
    parser.add_argument(
        "--save_every",
        type=int,
        default=100,
        metavar="N",
        help="How often to save while fetching idiom frequencies (save every N idioms) (it takes a while)",
    )
    parser.add_argument(
        "--collection_idioms_csv",
        type=Path,
        help="Path to csv file to store all idioms from idiom collection",
        default="data/collection_idioms.csv",
    )
    parser.add_argument(
        "--idiom_freq_file",
        type=Path,
        help="Path to idiom frequency file",
        default="data/idiom_frequencies.csv",
    )
    parser.add_argument(
        "--filtered_idioms_file",
        type=Path,
        help="Path to final filtered idioms file",
        default="data/filtered_idioms.csv",
    )
    parser.add_argument(
        "--translated_idioms_file",
        type=Path,
        help="Path to translated idioms file (csv with idiom, language, source_idiom, source_language)",
        default="data/translated_idioms.csv",
    )
    parser.add_argument(
        "--translated_idiom_freq_file",
        type=Path,
        help="Path to translated idiom frequency file",
        default="data/translated_idiom_frequencies.csv",
    )
    parser.add_argument(
        "--filtered_translated_idioms_file",
        type=Path,
        help="Path to final filtered translated idioms file",
        default="data/filtered_translated_idioms.csv",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If set, overwrite existing files (else use existing files)",
    )
    parser.add_argument(
        "-ll",
        "--log_level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set log level",
    )
    return parser


def read_and_filter_idiom_collection(args):
    if args.overwrite or not args.collection_idioms_csv.exists():
        logger.info("Reading idiom collection")
        dfs = []

        for target_lang in args.languages:
            lang_idiom_dir = args.idiom_collection_dir / target_lang
            if not lang_idiom_dir.exists():
                logger.error("Language directory %s does not exist", lang_idiom_dir)
                exit(1)
            logger.info("Reading idioms from %s", lang_idiom_dir)
            idiom_df = idiom_colletion_to_df(
                lang_idiom_dir,
                special_chars=args.special_chars,
                min_num_words=args.min_num_words,
            )
            idiom_df["language"] = target_lang
            logger.debug("Number of idioms in %s: %s", target_lang, len(idiom_df))
            dfs.append(idiom_df)

        idiom_df = pd.concat(dfs)
        logger.debug("Saving idioms to %s", args.collection_idioms_csv)
        idiom_df.to_csv(args.collection_idioms_csv, index=False)
    else:
        logger.debug("Reading existing idiom collection csv file")
        idiom_df = pd.read_csv(args.collection_idioms_csv)

    logger.info("Getting frequency in online library for idioms")
    if args.overwrite or not args.idiom_freq_file.exists():
        logger.debug("Creating new idiom frequency dataframe")
        idiom_frequency_df = pd.DataFrame(
            {
                "idiom": idiom_df.idiom.unique(),
                "frequency": [None] * len(idiom_df.idiom.unique()),
            }
        )
    else:
        logger.debug("Reading existing idiom frequency dataframe")
        idiom_frequency_df = pd.read_csv(args.idiom_freq_file)

    idiom_frequency_df = get_idiom_frequencies(
        idiom_frequency_df, args.save_every, args.idiom_freq_file
    )

    idiom_df["frequency"] = idiom_df["idiom"].map(
        idiom_frequency_df.set_index("idiom").frequency
    )

    # Filter idioms based on frequency
    idiom_df = idiom_df[idiom_df.frequency >= args.min_frequency]
    idiom_df = idiom_df.reset_index(drop=True)

    logger.info(
        "Number of idioms with frequency >= %s: %s",
        args.min_frequency,
        len(idiom_df),
    )

    idiom_df.to_csv(args.filtered_idioms_file, index=False)


def translate_and_filter_idioms(args):
    idiom_df = pd.read_csv(args.filtered_idioms_file)

    if args.overwrite or not args.translated_idioms_file.exists():
        idioms_to_translate = {
            "source_idiom": [],
            "source_language": [],
            "language": [],
        }

        for idiom, df_ in idiom_df.groupby("idiom"):
            if len(df_) < len(args.languages):
                lang_list = df_.language.tolist()
                source_lang = lang_list[0]
                for lang in args.languages:
                    if lang not in lang_list:
                        idioms_to_translate["source_idiom"].append(idiom)
                        idioms_to_translate["source_language"].append(source_lang)
                        idioms_to_translate["language"].append(lang)

        translated_idioms_df = pd.DataFrame(idioms_to_translate)
        translated_idioms_df["idiom"] = [None] * len(translated_idioms_df)

    else:
        logger.debug("Reading existing translated idioms file")
        translated_idioms_df = pd.read_csv(args.translated_idioms_file)

    translated_idioms_df = get_idiom_translations(
        translated_idioms_df,
        save_every=args.save_every,
        translated_idioms_file=args.translated_idioms_file,
        min_num_words=args.min_num_words,
        special_chars=args.special_chars,
    )

    logger.info("Getting frequency in online library for translated idioms")
    if args.overwrite or not args.translated_idiom_freq_file.exists():
        logger.debug("Creating new translated idiom frequency dataframe")

        translated_idiom_frequency_df = pd.DataFrame(
            {
                "idiom": translated_idioms_df.idiom.unique(),
                "frequency": [None] * len(translated_idioms_df.idiom.unique()),
            }
        )

        logger.debug("Number of unique idioms %s", len(translated_idiom_frequency_df))

        if args.idiom_freq_file.exists():
            logger.debug("Reading existing idiom frequency dataframe")
            idiom_frequency_df = pd.read_csv(args.idiom_freq_file)

            # Set frequency if idiom is in idiom_frequency_df
            translated_idiom_frequency_df["frequency"] = (
                translated_idiom_frequency_df.idiom.map(
                    idiom_frequency_df.set_index("idiom").frequency
                )
            )
    else:
        logger.debug("Reading existing translated idiom frequency dataframe")
        translated_idiom_frequency_df = pd.read_csv(args.translated_idiom_freq_file)

    translated_idiom_frequency_df = get_idiom_frequencies(
        translated_idiom_frequency_df, args.save_every, args.translated_idiom_freq_file
    )

    translated_idioms_df["frequency"] = translated_idioms_df.idiom.map(
        translated_idiom_frequency_df.set_index("idiom").frequency
    )

    # Filter idioms based on frequency
    translated_idioms_df = translated_idioms_df[
        translated_idioms_df.frequency >= args.min_frequency
    ]
    translated_idioms_df = translated_idioms_df.reset_index(drop=True)

    logger.info(
        "Number of translated idioms with frequency >= %s: %s",
        args.min_frequency,
        len(translated_idioms_df),
    )

    translated_idioms_df.to_csv(args.filtered_translated_idioms_file, index=False)


def write_all_sequence_graphs(
    idiom_df: pd.DataFrame, translated_idiom_df: pd.DataFrame, dataset_output_dir: Path
):
    graph_dir = dataset_output_dir / "idiom_graphs"
    graph_dir.mkdir(parents=True, exist_ok=True)

    for lang, df_ in idiom_df.groupby("language"):
        write_sequence_graphs(
            graph_dir=graph_dir,
            idiom_df=df_,
            filename_prefix=f"{lang}",
        )
    for lang, df_ in translated_idiom_df.groupby("language"):
        write_sequence_graphs(
            graph_dir=graph_dir,
            idiom_df=df_,
            filename_prefix=f"translated_{lang}",
        )


def write_frequency_files(idiom_df, translated_idiom_df, dataset_output_dir):
    freq_dir = dataset_output_dir / "idiom_freqs"
    freq_dir.mkdir(exist_ok=True)
    idiom_df[["idiom", "language", "frequency"]].to_csv(
        freq_dir / "idiom_frequencies.csv", index=False
    )
    translated_idiom_df[
        ["idiom", "language", "frequency", "source_idiom", "source_language"]
    ].to_csv(freq_dir / "translated_idiom_frequencies.csv", index=False)


def create_idiom_dataset():
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.log_level, "create_idiom_dataset")
    logger.info("Arguments: %s", args)

    if not args.filtered_idioms_file.exists() or args.overwrite:
        logger.info("Reading and filtering idiom collection")
        read_and_filter_idiom_collection(args)
    else:
        logger.info("Reading existing filtered idioms file")

    idiom_df = pd.read_csv(args.filtered_idioms_file)
    logger.info("Number of idioms: %s", len(idiom_df))
    for lang, df_ in idiom_df.groupby("language"):
        logger.info("Number of %s idioms: %s", lang, len(df_))

    if not args.filtered_translated_idioms_file.exists() or args.overwrite:
        logger.info("Translating idioms (and filtering translated idioms)")
        translate_and_filter_idioms(args)
    else:
        logger.info("Reading existing filtered translated idioms file")

    translated_idiom_df = pd.read_csv(args.filtered_translated_idioms_file)
    logger.info("Number of translated idioms: %s", len(translated_idiom_df))
    for lang, df_ in translated_idiom_df.groupby("language"):
        logger.info("Number of %s translated idioms: %s", lang, len(df_))

    logger.info("Creating sequence graphs")
    write_all_sequence_graphs(
        idiom_df=idiom_df,
        translated_idiom_df=translated_idiom_df,
        dataset_output_dir=args.dataset_output_dir,
    )

    logger.info("Write frequency files")
    write_frequency_files(
        idiom_df=idiom_df,
        translated_idiom_df=translated_idiom_df,
        dataset_output_dir=args.dataset_output_dir,
    )

    logger.info("Creating idiom completion task")
    idiom_comp_task_df = idiom_df_to_idiom_completion_task(idiom_df=idiom_df)
    idiom_comp_task_df.to_json(
        args.dataset_output_dir / "data.jsonl", lines=True, orient="records"
    )
    logger.debug(
        "Number of idioms in idiom completion task: %s", len(idiom_comp_task_df)
    )

    logger.info("Creating original + translated idiom completion task")
    all_df = pd.concat(
        [idiom_df[["idiom", "language"]], translated_idiom_df[["idiom", "language"]]]
    ).drop_duplicates()

    all_idiom_comp_task_df = idiom_df_to_idiom_completion_task(idiom_df=all_df)
    all_idiom_comp_task_df.to_json(
        args.dataset_output_dir / "original_and_translated_data.jsonl",
        lines=True,
        orient="records",
    )

    logger.debug(
        "Number of idioms in original + translated idiom completion task: %s",
        len(all_idiom_comp_task_df),
    )

    with open(args.dataset_output_dir / "README.md", "w") as f:
        f.write(DATASETS_README_INFO)

    ds = load_dataset(str(args.dataset_output_dir), split="test")
    assert ds.num_rows == len(idiom_comp_task_df)

    ds = load_dataset(
        str(args.dataset_output_dir), split="test", name="include_translated_idioms"
    )
    assert ds.num_rows == len(all_idiom_comp_task_df)

    logger.info("Done! Created dataset at %s", args.dataset_output_dir)
