from collections import defaultdict
import pandas as pd
from nb_tokenizer import tokenize


def token_lists_to_idiom_completion_task(
    tokenized_idioms: list[list[str]],
) -> pd.DataFrame:
    """Create idiom completion task from tokenized_idioms"""
    first_last = defaultdict(list)
    completion_task_data = {}

    for e in tokenized_idioms:
        first_words = " ".join(e[:-1])
        last_word = e[-1]
        first_last[first_words].append(last_word)

    completion_task_data["idiom_start"] = first_last.keys()
    completion_task_data["accepted_completions"] = first_last.values()
    return pd.DataFrame(completion_task_data)


def idiom_df_to_idiom_completion_task(idiom_df: pd.DataFrame) -> pd.DataFrame:
    """Create idiom completion task from idiom_df"""

    dfs = []
    for language, df_ in idiom_df.groupby("language"):
        tokenized_idioms = [tokenize(e) for e in df_.idiom]
        completion_task_df = token_lists_to_idiom_completion_task(tokenized_idioms)
        completion_task_df["language"] = language
        dfs.append(completion_task_df)

    return pd.concat(dfs)
