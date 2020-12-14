from fastapi import FastAPI
from .routers import tweets, stocks

app = FastAPI()

app.include_router(tweets.router)
app.include_router(stocks.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/main")
def read_item(item, value):
    return {"item": item, "value": value}


@app.get("/main/add")
def add(num_1: int, num_2: int):
    return {"result": num_1 + num_2}
