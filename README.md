# Описание проекта: Uplift Modeling API

## Общий обзор
Проект представляет собой API для обучения uplift моделей с использованием различных классификаторов и подходов. API предоставляет два основных endpoint'a для отправки запросов на обучение модели (`/score`) и получения результатов обучения (`/score/result`).

## Основные характеристики

1. **Endpoint `/score`**:
   - Позволяет пользователю отправить запрос на обучение модели с заданными параметрами:
     - `approach`: выбор между "two-model" и "solo-model".
     - `classifier`: выбор между "catboost" и "random-forest".
     - `train-size`: доля данных, используемая для обучения, вещественное число от 0 до 1.
   - Возвращает `request_id` для последующего отслеживания статуса обучения.

2. **Endpoint `/score/result`**:
   - Возвращает как результат обучения метрику `precision` по `request_id`.

## Техническая реализация

- **Redis**: используется для хранения статуса и результатов обработки запросов.
- **RabbitMQ**: используется для асинхронной обработки запросов на обучение моделей.
- **Uplift-модели**: обучаются на выборке из датасета x5 с последующим расчетом метрики `precision`.

## Деплоймент

- Реализован на кластере Kubernetes с использованием Kind.
- Все компоненты системы (API, Redis, RabbitMQ, worker) упакованы в Docker контейнеры и развернуты как сервисы в Kubernetes.

## Настройка и запуск проекта

### Makefile
В `Makefile` включены команды для:
1. Создания и удаления Kubernetes кластера в Kind.
2. Сборки и загрузки Docker образов для API и worker.
3. Деплоя сервисов Redis и RabbitMQ, а также API и worker.

### Kubernetes конфигурации
Конфигурации Kubernetes `yaml` для всех сервисов включены в папку `k8s`

### Запуск проекта
1. **Создание кластера**: `make create-cluster`
2. **Деплой сервисов**: `make deploy`
3. **Удаление кластера**: `make delete-cluster`
