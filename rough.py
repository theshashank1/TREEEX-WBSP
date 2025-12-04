import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import create_engine

load_dotenv()

db_user = os.environ.get("POSTGRES_USER")
db_password = os.environ.get("POSTGRES_PASSWORD")
db_host = os.environ.get("POSTGRES_HOST")
db_port = os.environ.get("POSTGRES_PORT")
db_name = os.environ.get("POSTGRES_DB")

# URL encode password
from urllib.parse import quote

db_password = quote(db_password)

connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

engine = create_engine(connection_string, echo=True)


async def test_db():
    try:
        with engine.connect() as conn:
            # Wrap SQL string in text()
            result = conn.execute(text("SELECT 1;"))
            return f"DB Connected! Result: {result.fetchone()}, at conection string: {connection_string}"
    except Exception as e:
        return f"Database connection failed: {e}, {connection_string}"


# FastAPI example
from fastapi import FastAPI

app = FastAPI()


@app.get("/test-db")
async def test_db_route():
    return {"message": await test_db()}


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
