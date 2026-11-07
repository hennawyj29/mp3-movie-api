import logging
import sqlite3
import pandas as pd
from .database import get_connection, initialize_database

logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]

class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)

    def save(self, df):
        """Replace all movie rows in one transaction."""
        # TODO: Convert missing values to Python None for SQL NULL.
        # DELETE the old rows, then INSERT all rows from df.
        # Commit only after all inserts succeed; roll back on SQLite errors.
        # Close the connection in finally. Log the saved row count at DEBUG.
        pass

    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""
        # TODO: SELECT the four fields, fetch rows, and create the DataFrame.
        # Return a DataFrame with columns=MOVIE_COLUMNS,
        # so the column names are preserved even when the query returns no rows.
        pass

    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")
        
        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")
            
        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        try:
            # TODO: SELECT selected_columns from movies, ordered by id.
            # Use a placeholder for limit; fetch the rows.
            # Return a list of dictionaries and log at DEBUG.
            pass
        finally:
            connection.close()

    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        pass

    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""
        # TODO: validate columns as in select_columns().
        # SELECT id plus those columns and filter by minimum rating.
        # Sort by rating DESC then id ASC, and apply limit.
        # Return dictionaries and log the selected columns and row count at DEBUG.
        pass