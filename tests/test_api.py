import pytest
import pandas as pd

from src import MovieStorage
import main


def test_movies_persist(client, test_storage, uploaded_movies):
    new_storage = MovieStorage(test_storage.db_path)

    df = new_storage.get()
    assert len(df) == 20
    assert list(df.columns) == [
        "title", "release_year", "rating", "genre"
    ]

    expected = pd.read_csv("fixtures/sample_movies.csv")
    assert list(df["title"]) == list(expected["title"])
    assert new_storage.count_movies() == 20

    stored = new_storage.select_columns(["title"], limit=100)
    response = client.get("/movies", params={"limit": 100})

    assert response.status_code == 200
    assert [row["id"] for row in stored] == list(range(1, 21))
    assert [row["id"] for row in response.json()["data"]] == list(range(1, 21))


def test_cache_and_processing(client, uploaded_movies, processing_body):
    response = client.get("/movies", params={"limit": 100})
    assert response.status_code == 200
    assert main.cache.get(100) == response.json()

    small_response = client.get("/movies", params={"limit": 1})
    assert small_response.status_code == 200
    assert main.cache.get(1) == small_response.json()

    repeat = client.get("/movies", params={"limit": 100})
    assert repeat.json() == response.json()

    processed = client.post("/movies/process", json=processing_body)
    assert processed.status_code == 200
    report = processed.json()

    assert report["validation_rows_removed"] == 0
    assert report["cleaning_report"]["rows_before"] == 20
    assert report["cleaning_report"]["rows_after"] == 16

    assert main.cache.get(100) is None
    assert main.cache.get(1) is None

    updated = client.get("/movies", params={"limit": 100})
    assert updated.status_code == 200
    assert updated.json()["total_rows"] == 16

    rows = updated.json()["data"]
    assert [row["title"] for row in rows] == [
        f"Movie {chr(65 + i)}" for i in range(16)
    ]
    assert [row["id"] for row in rows] == list(range(1, 17))
    assert main.cache.get(100) == updated.json()


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    first = client.get("/movies", params={"limit": 100})
    assert first.status_code == 200

    def fail_if_called(*args, **kwargs):
        pytest.fail("Database should not be called on cache hit")

    monkeypatch.setattr(
        main.storage, "select_columns", fail_if_called
    )
    monkeypatch.setattr(
        main.storage, "count_movies", fail_if_called
    )

    second = client.get("/movies", params={"limit": 100})
    assert second.status_code == 200
    assert second.json() == first.json()
