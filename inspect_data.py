import pandas as pd
from pathlib import Path

data_folder = Path("synthea_data")

files = [
    "patients.csv",
    "encounters.csv",
    "organizations.csv",
    "providers.csv",
    "payers.csv",
    "claims.csv",
    "claims_transactions.csv",
    "conditions.csv",
    "medications.csv",
    "procedures.csv"
]

for filename in files:
    path = data_folder / filename

    df = pd.read_csv(path)

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Column names:")
    print(list(df.columns))