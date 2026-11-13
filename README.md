# MP3 Movie API

For MP3, I continued working on my API from MP2 and added a few new features. I used SQLite to store movie data instead of keeping everything in memory. This allows the movies to stay saved even after restarting the API. I also added SQL queries so users can search for movies based on ratings and choose which columns they want to see. I kept the processing functions from MP2 to validate and clean the data. For Part 2, I added FakeRedis to cache movie results for 90 seconds. The cache also clears whenever movies are uploaded or processed so the results stay updated.

## How to Run

Start the API:
```
python -m uvicorn main:app --reload
```

Run the tests:
```
python -m pytest tests -v
```

## Example Processing Request

POST /movies/process

```json
{
  "validation": {
    "required_columns": ["title", "release_year", "rating", "genre"],
    "numeric_columns": ["release_year", "rating"]
  },
  "processing": {
    "remove_duplicates": true,
    "missing": {
      "enabled": true,
      "axis": "rows"
    },
    "outliers": {
      "enabled": true,
      "columns": ["rating"],
      "method": "iqr",
      "threshold": 1.5
    }
  }
}
```

Expected result: After processing the sample CSV, the number of movies goes from 20 to 16, with 0 rows removed during validation.