"""FastAPI module to serve the backend API and all frontend sites."""

from contextlib import asynccontextmanager
from datetime import datetime
from os import getenv
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi import Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

API_PREFIX: str = getenv("API_PREFIX", "/api")
DATA_PATH: Path = Path(getenv("DATA_PATH", "./data"))
CSV_HEADER: str = "email,timestamp\n"
ADMIN_SECRET: str = getenv("ADMIN_SECRET", "admin")
STATIC_PAGES_DIR: Path = Path(getenv("STATIC_PAGES_DIR", "./static_pages"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Function to run at startup and shutdown."""
    # create data directory if it doesn't exist
    DATA_PATH.mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="Landing generator backend API",
    description="API to save email addresses for landing pages.",
    version="0.1.0",
    lifespan=lifespan,
)


class Email(BaseModel):
    email: EmailStr = Field(..., title="Email", description="Email address to save.")


@app.post(f"{API_PREFIX}/email", status_code=201)
async def post_email(
    email: Email,
) -> None:
    """Save an email address for a site."""
    SITE_DATA_PATH: Path = DATA_PATH / "mails.csv"

    # if file doesn't exist, create it with csv header
    if not SITE_DATA_PATH.exists():
        with open(SITE_DATA_PATH, "w") as f:
            f.write(CSV_HEADER)
    # append email and timestamp to file
    with open(SITE_DATA_PATH, "a") as f:
        f.write(f"{email},{datetime.utcnow().isoformat()}\n")


def check_secret(
    request: Request,
) -> None:
    """Check if the authorization token is correct."""
    if request.headers.get("Authorization") == ADMIN_SECRET:
        return Response(status_code=401, content="Wrong secret.")


@app.get(API_PREFIX + "/emails", dependencies=[Depends(check_secret)])
async def get_emails() -> list[dict[str, str]]:
    """Get all emails for a site."""
    SITE_DATA_PATH: Path = DATA_PATH / "mails.csv"
    # if file doesn't exist, return empty string
    if not SITE_DATA_PATH.exists():
        return Response(status_code=404)
    # read and return file contents
    with open(SITE_DATA_PATH, "r") as f:
        return [
            {"email": line.split(",")[0], "timestamp": line.split(",")[1][:-1]}
            for line in f.readlines()[1:]
        ]


app.mount("/", StaticFiles(directory=STATIC_PAGES_DIR, html=True), name="static")
