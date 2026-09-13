import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# --------------------------------------------------
# MySQL connection settings
# --------------------------------------------------

MYSQL_USER = "root"
MYSQL_PASSWORD = "Yasasvi@20"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DATABASE = "healthcare_claims"

# Safely creates the connection URL even if the
# password contains special characters like @, #, %, :
connection_url = URL.create(
    "mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DATABASE
)

engine = create_engine(connection_url)

# --------------------------------------------------
# Synthea dataset folder
# --------------------------------------------------

DATA_DIR = Path("synthea_data")

# --------------------------------------------------
# Tables we want to load
# --------------------------------------------------

tables = {
    "patients": "patients.csv",
    "organizations": "organizations.csv",
    "providers": "providers.csv",
    "payers": "payers.csv",
    "encounters": "encounters.csv",
    "procedures": "procedures.csv",
    "claims": "claims.csv",
    "claims_transactions": "claims_transactions.csv",
}

# --------------------------------------------------
# Load CSV files into MySQL
# --------------------------------------------------

print("Starting Synthea data load...")

for table_name, filename in tables.items():

    file_path = DATA_DIR / filename

    if not file_path.exists():
        print(f"\nERROR: File not found: {file_path}")
        continue

    print(f"\nLoading {filename}...")

    try:
        df = pd.read_csv(file_path)

        # Convert all column names to lowercase
        # Makes SQL queries easier later
        df.columns = [column.lower() for column in df.columns]

        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=1000
        )

        print(
            f"{table_name} loaded successfully "
            f"({len(df)} rows)"
        )

    except Exception as error:
        print(f"ERROR loading {filename}:")
        print(error)

print("\nFinished loading Synthea data.")