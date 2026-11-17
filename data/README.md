# Data directory

`raw/` and `processed/` are git-ignored. Download the clean NHANES CSVs and
dictionaries from Kaggle into `raw/` with:

```bash
pip install -r requirements.txt
python scripts/download_kaggle_dataset.py
```

The script skips files that already exist. Pass `--overwrite` to replace them.
It downloads the latest version of
[NHANES 1988-2018](https://www.kaggle.com/datasets/nguyenvy/nhanes-19882018).
The selected files are `chemicals_clean.csv`, `comments_clean.csv`,
`demographics_clean.csv`, `dietary_clean.csv`, `medications_clean.csv`,
`mortality_clean.csv`, `occupation_clean.csv`, `questionnaire_clean.csv`,
`response_clean.csv`, `weights_clean.csv`, `dictionary_drug_codes.csv`,
`dictionary_harmonized_categories.csv`, and `dictionary_nhanes.csv`.
Record the Kaggle dataset version and download date here and in the Phase 2
`readme.txt` after downloading.
