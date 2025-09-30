from uuid import uuid4


def test_get_books_empty(client):
    response = client.get("/api/v1/books/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_create_book(client):
    book_data = {
        "title": "Тестовая книга",
        "rating": 4.5,
        "description": "Описание тестовой книги",
        "published_year": 2023,
        "genre_ids": [],
        "contributors": []
    }
    response = client.post("/api/v1/books/", json=book_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["rating"] == str(book_data["rating"])
    assert data["description"] == book_data["description"]
    assert data["published_year"] == book_data["published_year"]
    assert "id" in data


def test_get_book_by_id(client):
    book_data = {
        "title": "Книга для получения по ID",
        "rating": 3.8,
        "description": "Описание книги для теста получения по ID",
        "published_year": 2022,
        "genre_ids": [],
        "contributors": []
    }
    create_response = client.post("/api/v1/books/", json=book_data)
    assert create_response.status_code == 201
    created_book = create_response.json()
    book_id = created_book["id"]

    response = client.get(f"/api/v1/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == book_data["title"]
    assert data["rating"] == str(book_data["rating"])
    assert data["description"] == book_data["description"]
    assert data["published_year"] == book_data["published_year"]


def test_get_book_not_found(client):
    non_existent_id = uuid4()
    response = client.get(f"/api/v1/books/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга не найдена"


def test_delete_book(client):
    book_data = {
        "title": "Книга для удаления",
        "rating": 5.0,
        "description": "Описание книги для удаления",
        "published_year": 2021,
        "genre_ids": [],
        "contributors": []
    }
    create_response = client.post("/api/v1/books/", json=book_data)
    assert create_response.status_code == 201
    created_book = create_response.json()
    book_id = created_book["id"]

    response = client.delete(f"/api/v1/books/{book_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/books/{book_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Книга не найдена"


def test_delete_book_not_found(client):
    non_existent_id = uuid4()
    response = client.delete(f"/api/v1/books/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга не найдена"


def test_get_books_with_pagination(client):
    initial_response = client.get("/api/v1/books/")
    initial_data = initial_response.json()
    initial_count = initial_data["total"]

    for i in range(15):
        book_data = {
            "title": f"Книга для пагинации {i + 1}",
            "rating": 4.0,
            "description": f"Описание книги для пагинации {i + 1}",
            "published_year": 2020 + i,
            "genre_ids": [],
            "contributors": []
        }
        client.post("/api/v1/books/", json=book_data)

    response = client.get("/api/v1/books/?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == initial_count + 15
    assert data["page"] == 1
    assert data["page_size"] == 5

    response = client.get("/api/v1/books/?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


def test_get_books_with_search(client):
    books = [
        {"title": "Python программирование", "rating": 4.5,
         "published_year": 2020},
        {"title": "JavaScript для начинающих", "rating": 4.0,
         "published_year": 2021},
        {"title": "Python高级编程", "rating": 4.8,
         "published_year": 2022},
        {"title": "Веб-разработка на Django", "rating": 4.2,
         "published_year": 2023},
    ]

    for book in books:
        book_data = {
            "title": book["title"],
            "rating": book["rating"],
            "description": f"Описание {book['title']}",
            "published_year": book["published_year"],
            "genre_ids": [],
            "contributors": []
        }
        client.post("/api/v1/books/", json=book_data)

    response = client.get("/api/v1/books/?q=Python")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert all("Python" in item["title"] for item in data["items"])
