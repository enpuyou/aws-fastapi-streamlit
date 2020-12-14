FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

RUN pip install pipenv

# Install application into container

COPY Pipfile Pipfile.lock* /app/
RUN pipenv install --system --deploy

COPY ./app /app/app
