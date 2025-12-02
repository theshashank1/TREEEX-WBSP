import os
from urllib.parse import quote
from dotenv import load_dotenv

from fastapi import FastAPI
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

load_dotenv()

# -----------------------
# Environment variables
# -----------------------
db_user = os.environ.get("POSTGRES_USER")
db_password = quote(os.environ.get("POSTGRES_PASSWORD"))  # URL-encode
db_host = os.environ.get("POSTGRES_HOST")
db_port = os.environ.get("POSTGRES_PORT")
db_name = os.environ.get("POSTGRES_DB")

# -----------------------
# Async Engine + Session
# -----------------------
DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI()

# -----------------------
# Test DB endpoint
# -----------------------
async def test_db_async():
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            return f"DB Connected! Result: {result.fetchone()}"
    except Exception as e:
        return f"Database connection failed: {e}"

@app.get("/test-db")
async def test_db_route():
    message = await test_db_async()
    return {"message": message}

@app.get("/")
def read_root():
    return {"Hello": "World"}

# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
