---
task_categories:
- text-generation
- fill-mask
language:
- 'no'
- nb
- nn
pretty_name: Norwegian Idioms
size_categories:
- 1K<n<10K
license: cc0-1.0
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
# Norwegian idioms

⚠️ Note: This dataset was recently updated: some idioms contained OCR errors which have been fixed, and the value "both" har been removed from the language column. If an idiom exists in both languages, there will be a row with the idiom for each language. In addition, translated idioms have been added (optional) ⚠️

This is a dataset that consists of 3553 Norwegian idioms and phrases that appear more than 100 times in the [online library](https://www.nb.no/search) of the National Library of Norway.  
There are 3472 Bokmål idioms and 89 Nynorsk idioms. 

To improve the Bokmål/Nynorsk imbalance, we have automatically translated all idioms that exist in one language and not in the other with [apertium](https://apertium.org). These have again been filtered on frequency in the online library. Including the translated idioms, there are 4600 unique idioms; 3502 Bokmål idioms and 1707 Nynorsk idioms. 

## Idiom completion as an NLP task
The idioms are split into idiom starts (the first N-1 words) and accepted completions (a list of possible last words to complete the idiom). Of the 3259 rows, there are 154 where there are more than one accepted completion.  

This dataset can be used to measure a generative language models' ability to complete well known idioms, or as a masked language modelling task. 

### Using the dataset 
Loading the dataset with original idioms only:
```python
from datasets import load_dataset

ds = load_dataset("Sprakbanken/Norwegian_idioms", split="test")
```

Loading the dataset with translated idioms included:
```python
from datasets import load_dataset

ds = load_dataset("Sprakbanken/Norwegian_idioms", split="test", name="include_translated_idioms")
```


## Idiom frequencies
`idiom_freqs/idiom_frequencies.csv` contain the idiom, language code and frequency in the online library for all the original idioms  
`idiom_freqs/translated_idiom_frequencies.csv` contain the idiom, language code, frequency in the online library, source idiom and source language code for all the translated idioms

## Idiom graphs
There is considerable linguistic overlap between the idioms. For example, though there are 3553 unique idioms, there are only 803 unique starter words.  

We have arranged the idioms as trees, where the roots are the start words, and the idioms are found by following a path from a root node to a leaf node.  
Example: 
```json
"alt": {
    "er": {
        "bare": {
            "fryd": {
                "og": {
                    "gammen": {}
                }
            }
        },
        "klappet": {
            "og": {
                "klart": {}
            }
        },
        "såre": {
            "vel": {}
        }
    },
    "går": {
        "sin": {
            "vante": {
                "gang": {}
            }
        }
    },
}
```
Here is a tree where "alt" is the root, the idioms "alt er bare fryd og gammen", "alt er klappet og klart", "alt er såre vel" and "alt går sin vante gang" can be found by traversing the tree.  
These trees can be found in `idiom_graphs/`.  

There are also flat versions of the trees (where consecutive nodes/words with only one child are merged into word sequences)

Example:
```json
"alt": {
    "er": {
        "bare fryd og gammen": "",
        "klappet og klart": "",
        "såre vel": ""
    },
    "går sin vante gang": "",
}
```