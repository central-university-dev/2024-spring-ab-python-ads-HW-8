# Указываем базовый образ
FROM python:3.9

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем рабочий каталог для приложения
WORKDIR /app

# Копируем файлы конфигурации зависимостей в рабочий каталог
COPY pyproject.toml poetry.lock* /app/

# Отключаем виртуальное окружение Poetry и устанавливаем зависимости
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Копируем остальные файлы проекта в рабочий каталог
COPY . /app

# Запускаем приложение
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
