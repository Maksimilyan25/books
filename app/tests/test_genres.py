from uuid import uuid4


def test_get_genres_empty(client):
    response = client.get("/api/v1/genres/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_create_genre(client):
    genre_data = {
        "name": "Фантастика"
    }
    response = client.post("/api/v1/genres/", json=genre_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == genre_data["name"]
    assert "id" in data


def test_get_genre_by_id(client):
    genre_data = {
        "name": "Детектив"
    }
    create_response = client.post("/api/v1/genres/", json=genre_data)
    assert create_response.status_code == 201
    created_genre = create_response.json()
    genre_id = created_genre["id"]

    response = client.get(f"/api/v1/genres/{genre_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == genre_id
    assert data["name"] == genre_data["name"]


def test_get_genre_not_found(client):
    non_existent_id = uuid4()
    response = client.get(f"/api/v1/genres/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Жанр не найден"


def test_delete_genre(client):
    genre_data = {
        "name": "Ужасы"
    }
    create_response = client.post("/api/v1/genres/", json=genre_data)
    assert create_response.status_code == 201
    created_genre = create_response.json()
    genre_id = created_genre["id"]

    response = client.delete(f"/api/v1/genres/{genre_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/genres/{genre_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Жанр не найден"


def test_delete_genre_not_found(client):
    non_existent_id = uuid4()
    response = client.delete(f"/api/v1/genres/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Жанр не найден"


def test_get_genres_with_pagination(client):
    initial_response = client.get("/api/v1/genres/")
    initial_data = initial_response.json()
    initial_count = initial_data["total"]

    for i in range(15):
        genre_data = {
            "name": f"Жанр для пагинации {i + 1}"
        }
        client.post("/api/v1/genres/", json=genre_data)

    response = client.get("/api/v1/genres/?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == initial_count + 15
    assert data["page"] == 1
    assert data["page_size"] == 5

    response = client.get("/api/v1/genres/?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


def test_get_genres_with_search(client):
    genres = [
        {"name": "Научная фантастика"},
        {"name": "Фэнтези"},
        {"name": "Научная литература"},
        {"name": "Исторический роман"},
    ]

    for genre in genres:
        genre_data = {
            "name": genre["name"]
        }
        client.post("/api/v1/genres/", json=genre_data)

    response = client.get("/api/v1/genres/?q=Научная")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert all("Научная" in item["name"] for item in data["items"])


def test_create_genre_validation_error(client):
    genre_data = {
        "name": ""
    }
    response = client.post("/api/v1/genres/", json=genre_data)
    assert response.status_code == 422

    genre_data = {
        "name": "a" * 101
    }
    response = client.post("/api/v1/genres/", json=genre_data)
    assert response.status_code == 422


def test_create_duplicate_genre(client):
    genre_data = {
        "name": "Уникальный жанр"
    }
    response = client.post("/api/v1/genres/", json=genre_data)
    assert response.status_code == 201

    response = client.post("/api/v1/genres/", json=genre_data)
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]
