from fastapi import FastAPI

from app.books.router import router as books_router
from app.genre.router import router as genres_router


app = FastAPI(title='BD for books')


@app.get('/', summary='Главная страница')
async def main_page():
    return {'message': 'Главная страница'}


@app.get('/api/ping', summary='Healthcheck')
async def healthcheck():
    return {'status': 'ok'}


app.include_router(books_router, prefix='/api/v1')
app.include_router(genres_router, prefix='/api/v1')
