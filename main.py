
import io
import json
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from src import (
    HealthResponse,
    ProcessConfig,
    MovieStorage,
    MovieCache,
    MovieUploadInfo,
    MovieDataResponse,
    MovieProcessingReport,
    setup_logging,
    log_requests,
)
from src.storage import MOVIE_COLUMNS
from data_pipeline import (
    create_cleaning_report,
    process_data,
    validate_dataframe,
)

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Movie API", version="1.0.0")
app.middleware("http")(log_requests)

storage = MovieStorage()
cache = MovieCache()


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    extension = Path(file.filename or "").suffix.lower()

    if extension != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    contents = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or unreadable CSV file"
        )

    if len(df.columns) != len(MOVIE_COLUMNS) or set(df.columns) != set(MOVIE_COLUMNS):
        raise HTTPException(
            status_code=400,
            detail="Invalid movie columns"
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain at least one movie"
        )

    df = df[MOVIE_COLUMNS]
    storage.save(df)
    cache.invalidate()

    logger.info(
        "Uploaded movies: filename=%s, rows=%s",
        file.filename, len(df)
    )

    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
    }



@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    cached = cache.get(limit)

    if cached is not None:
        logger.info("Cache hit for movies: limit=%s", limit)
        return cached

    records = storage.select_columns(MOVIE_COLUMNS, limit)
    total = storage.count_movies()

    response = {
        "data": records,
        "total_rows": total,
    }

    cache.set(limit, response)

    logger.info("Retrieved movies: returned_rows=%s", len(records))
    return response


@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1),
):
    try:
        records = storage.query_movies(columns, min_rating, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    logger.info(
        "Queried movies: columns=%s, min_rating=%s, returned_rows=%s",
        columns, min_rating, len(records)
    )

    return records


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    df = storage.get()

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="No movies to process"
        )

    config_dict = config.model_dump()

    for column in config.validation.numeric_columns:
        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Numeric column not found: {column}"
            )

    try:
        validated_df = validate_dataframe(
            df,
            config.validation.required_columns,
            config.validation.numeric_columns
        )

        validation_rows_removed = len(df) - len(validated_df)
        validated_copy = validated_df.copy()

        processed_df = process_data(validated_df, config_dict)

        cleaning_report = create_cleaning_report(
            validated_copy, processed_df
        )

    except ValueError as error:
        logger.warning("Processing failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error))

    storage.save(processed_df)
    cache.invalidate()

    logger.info(
        "Processed movies: validation_removed=%s, rows_before=%s, rows_after=%s",
        validation_rows_removed,
        len(validated_copy),
        len(processed_df)
    )

    return {
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report,
    }
