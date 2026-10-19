
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent

# Local development only.
# Do not include .env files in the production image.
load_dotenv(BASE_DIR / ".env")

CLOUD_MODE = os.getenv("CLOUD_MODE", "false").lower() == "true"
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "healthcare_claims")

if CLOUD_MODE:
    from google.cloud import secretmanager
    from google.cloud.sql.connector import Connector, IPTypes

    PROJECT_ID = "mediclaim-509016"
    INSTANCE_CONNECTION_NAME = (
        "mediclaim-509016:us-central1:mediclaim-mysql"
    )
    SECRET_ID = "mediclaim-db-password"

    # Authenticate using Application Default Credentials.
    # On the VM, these come from the attached service account.
    secret_client = secretmanager.SecretManagerServiceClient()

    secret_name = (
        f"projects/{PROJECT_ID}/secrets/"
        f"{SECRET_ID}/versions/latest"
    )

    response = secret_client.access_secret_version(
        request={"name": secret_name}
    )

    db_password = response.payload.data.decode("utf-8")

    # The connector handles authenticated TLS.
    # PRIVATE ensures the database's private IP is used.
    connector = Connector(refresh_strategy="lazy")

    def get_connection():
        return connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pymysql",
            user="mediclaim_runtime",
            password=db_password,
            db=MYSQL_DATABASE,
            ip_type=IPTypes.PRIVATE,
        )

    engine = create_engine(
        "mysql+pymysql://",
        creator=get_connection,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

else:
    # Preserve the existing local MySQL configuration.
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

    connection_url = URL.create(
        "mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DATABASE,
    )

    engine = create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

def close_database():
    """Release database connections and connector resources."""
    engine.dispose()

    if CLOUD_MODE:
        connector.close()