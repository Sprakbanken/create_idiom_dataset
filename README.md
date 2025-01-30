# Create idiom dataset 

This repository contains code to create a frequency curated idiom dataset from a collection of idiom books

## Setup and install
You can easily install with pdm like this:
```bash
pdm install
```

Or with python >= 3.12, venv and pip like this: 
```bash
python3 -m venv venv
. venv/bin/activate
pip install .
```

## Run create_idiom_dataset script
With pdm:
```bash
pdm run python -m create_idiom_dataset <path-to-idiom-collection> <path-to-output-dataset>
```

```bash
python3 -m create_idiom_dataset <path-to-idiom-collection> <path-to-output-dataset>
```

Run with --help flag to see other argument options


## Data sources for Norwegian idiom dataset
TBA