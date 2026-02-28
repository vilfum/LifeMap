------------------------------------------------------------------------
АРХИТЕКТУРА ПРОЕКТА "КАРТА ЖИЗНИ"
------------------------------------------------------------------------
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
------------------------------------------------------------------------

# LifeMap — Архитектура проекта (после рефакторинга)

---

## 1. Общий обзор архитектуры

Проект **LifeMap (Карта жизни)** построен по принципу разделения ответственности и состоит из следующих слоев:

```
┌──────────────────────────┐
│        Entry Point       │
│        main.py           │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│      Application Layer   │
│         app.py           │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│         UI Layer         │
│   ui/  +  widgets/       │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│      Service Layer       │
│        core/*_service    │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│    Repository Layer      │
│   content_repository     │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│      Database Layer      │
│        database.py       │
└──────────────────────────┘
```

Архитектура реализует четкое разделение:

* UI не работает напрямую с БД
* Сцена не хранит бизнес-логику
* Сервисы инкапсулируют операции
* Репозитории работают с хранилищем
* Модели описывают структуру данных

---

## 2. Структура проекта

```
LifeMap/
│
├── main.py
├── app.py
├── setup.py
├── requirements.txt
│
├── core/
│   ├── database.py
│   ├── models.py
│   ├── graph_service.py
│   ├── content_service.py
│   ├── content_repository.py
│   ├── file_service.py
│   └── __init__.py
│
├── ui/
│   ├── main_window.py
│   ├── graph_scene.py
│   ├── node_item.py
│   ├── edge_item.py
│   ├── editor_dialog.py
│   ├── themes.py
│   └── __init__.py
│
├── widgets/
│   ├── base_tab.py
│   ├── text_tab.py
│   ├── todo_tab.py
│   ├── list_tab.py
│   ├── date_tab.py
│   ├── files_tab.py
│   └── __init__.py
│
└── zoldik/   (устаревший код)
```

---

## 3. Точка входа

#### main.py

Назначение:

* Защищенная точка входа
* Обработка критических ошибок
* Вывод лицензионного уведомления

Поток запуска:

```
main()
   ↓
run() из app.py
   ↓
Создание QApplication
   ↓
Создание MainWindow
   ↓
app.exec()
```

---

#### app.py

Назначение:

* Инициализация QApplication
* Создание главного окна
* Запуск цикла Qt

Это чистый Application Layer без бизнес-логики.

---

## 4. UI Layer

Каталог: `ui/`

Этот слой отвечает только за визуализацию и взаимодействие пользователя.

---

#### 4.1 MainWindow

Файл: `ui/main_window.py`

Главное окно приложения.

Ответственность:

* Создание GraphScene
* Размещение QGraphicsView
* Обработка меню
* Связь UI → Service

Не хранит данные.
Не работает напрямую с БД.

---

#### 4.2 GraphScene

Файл: `ui/graph_scene.py`

Центральный слой визуального графа.

Ответственность:

* Управление NodeItem
* Управление EdgeItem
* Обработка событий мыши
* Перетаскивание
* Связи между узлами

GraphScene работает с `graph_service`, а не с БД напрямую.

---

#### 4.3 NodeItem

Файл: `ui/node_item.py`

Представление узла в сцене.

Содержит:

* ID узла
* Позицию
* Цвет
* Ссылку на данные

Важно:
NodeItem — это View-объект, не модель данных.

---

#### 4.4 EdgeItem

Файл: `ui/edge_item.py`

Отвечает за визуальное соединение узлов.

Зависит от:

* NodeItem (start/end)
* Позиции узлов

EdgeItem не хранит бизнес-данные — только визуальную связь.

---

#### 4.5 EditorDialog

Файл: `ui/editor_dialog.py`

Окно редактирования содержимого узла.

Работает через:

* content_service
* динамическую загрузку вкладок из `widgets/`

---

#### 4.6 themes.py

Отвечает за централизованную систему оформления:

* Цвета
* Стиль
* Параметры UI

---

## 5. Widgets Layer (Редактор содержимого узла)

Каталог: `widgets/`

Реализует расширяемую систему вкладок.

Архитектура:

```
BaseTab (абстрактный базовый класс)
    ├── TextTab
    ├── TodoTab
    ├── ListTab
    ├── DateTab
    └── FilesTab
```

---

#### 5.1 BaseTab

Файл: `base_tab.py`

Определяет контракт:

* load_data()
* save_data()
* validate()

Все вкладки обязаны реализовать этот интерфейс.

---

#### 5.2 Типы вкладок

###### TextTab

* Хранение текстового содержимого

###### TodoTab

* Список задач
* Статус выполнения

###### ListTab

* Произвольные списки

###### DateTab

* Работа с датами
* События

###### FilesTab

* Привязка файлов
* Работа через file_service

---

## 6. Core Layer (Бизнес-логика)

Каталог: `core/`

Это центр архитектуры.

UI работает только через этот слой.

---

#### 6.1 models.py

Описание структур данных:

* Node
* Edge
* Content
* Связанные структуры

Это слой доменных моделей.

---

#### 6.2 database.py

Низкоуровневая работа с хранилищем.

Ответственность:

* Подключение к БД
* Инициализация схем
* CRUD операции

Никакой логики приложения здесь нет.

---

#### 6.3 content_repository.py

Промежуточный слой между:

* content_service
* database

Реализует:

* Получение данных
* Сохранение данных
* Инкапсуляцию SQL

---

#### 6.4 content_service.py

Бизнес-логика работы с содержимым узлов.

Отвечает за:

* Координацию вкладок
* Валидацию
* Формирование структуры данных
* Агрегацию

UI → ContentService → Repository → DB

---

#### 6.5 graph_service.py

Сервис управления графом.

Отвечает за:

* Создание узлов
* Удаление узлов
* Создание связей
* Логику графа

GraphScene не знает, как устроено хранение — только вызывает методы сервиса.

---

#### 6.6 file_service.py

Работа с файловыми вложениями:

* Сохранение
* Привязка к узлам
* Управление путями

Используется FilesTab.

---

## 7. Поток данных

#### Создание узла

```
UI (GraphScene)
    ↓
graph_service.create_node()
    ↓
database / repository
    ↓
возврат ID
    ↓
создание NodeItem
```

---

#### Редактирование содержимого

```
EditorDialog
    ↓
Tabs (BaseTab descendants)
    ↓
content_service.save_content()
    ↓
content_repository
    ↓
database
```

---

#### Загрузка проекта

```
MainWindow
    ↓
graph_service.load_graph()
    ↓
database
    ↓
создание NodeItem и EdgeItem
```

---

## 8. Принципы архитектуры

Проект следует принципам:

* Separation of Concerns
* Layered Architecture
* UI ≠ Business Logic
* Dependency Direction → внутрь (к core)
* Расширяемость через плагинообразные вкладки

---

## 9. Расширяемость

Добавление новой вкладки:

1. Создать файл в `widgets/`
2. Наследоваться от BaseTab
3. Реализовать интерфейс
4. Подключить в EditorDialog

Добавление нового типа сервиса:

1. Создать файл в core/
2. Инкапсулировать логику
3. Подключать только через MainWindow или Scene

---

## 10. Legacy код

Каталог `zoldik/` содержит устаревшие версии:

* старые точки входа
* тестовые файлы
* ранние UI-эксперименты

Не участвуют в текущей архитектуре.

---

## 11. Сборка

* `setup.py` — подготовка к сборке
* `LifeMap.spec` — PyInstaller
* `requirements.txt` — зависимости

---

## 12. Текущая архитектура

Сильные стороны:

* Четкое разделение слоев
* Модульность
* Расширяемость вкладок
* Инкапсуляция БД
* Отделение Scene от Data

Потенциальные направления развития:

* Dependency Injection
* Event Bus
* Undo/Redo через Command Pattern
* Plugin system для вкладок
* Слой DTO между UI и Service

---

## 13. Итоговая схема

```
main.py
   ↓
app.py
   ↓
MainWindow
   ↓
GraphScene
   ↓
Services (graph_service / content_service)
   ↓
Repositories
   ↓
Database
```

---

## 14. Структурная диаграмма проекта

```
main.py
   ↓
app.py
   ↓
ui.main_window
   ↓
ui.graph_scene
   ↓
ui.node_item / ui.edge_item
   ↓
core.graph_service
   ↓
core.content_service
   ↓
core.content_repository
   ↓
core.database
```

---

## 15. Детализация зависимостей по модулям

#### Entry Layer

###### main.py

Зависит от:

* app.py

Не зависит ни от одного внутреннего слоя напрямую.

---

###### app.py

Зависит от:

* ui.main_window
* PyQt6 / Qt

Не знает о:

* database
* repository
* моделях

---

#### UI Layer (`ui/`)

###### main_window.py

Зависит от:

* graph_scene
* editor_dialog
* core.graph_service
* core.content_service

Не зависит от:

* database напрямую

---

###### graph_scene.py

Зависит от:

* node_item
* edge_item
* core.graph_service

Не знает:

* как устроена БД
* SQL
* repository

---

###### node_item.py

Зависит только от:

* Qt

Не зависит от:

* сервисов
* БД
* моделей

Это чистый View-объект.

---

###### edge_item.py

Зависит от:

* node_item
* Qt

---

###### editor_dialog.py

Зависит от:

* widgets.*
* core.content_service

Не работает напрямую с database.

---

#### Widgets Layer (`widgets/`)

```
BaseTab
   ↑
TextTab
TodoTab
ListTab
DateTab
FilesTab
```

Все вкладки зависят от:

* BaseTab
* Qt
* content_service (через EditorDialog)

FilesTab дополнительно зависит от:

* core.file_service

---

#### Core Layer (`core/`)

###### graph_service.py

Зависит от:

* models
* database (или repository, если через слой)

Не зависит от UI.

---

###### content_service.py

Зависит от:

* content_repository
* models

Не зависит от UI.

---

###### content_repository.py

Зависит от:

* database

Не знает:

* UI
* Scene
* Widgets

---

###### database.py

Самый нижний слой.

Не зависит ни от кого внутри проекта.

---

## 16. Направление зависимостей

Главное правило проекта:

```
UI  →  Services  →  Repository  →  Database
```

Никогда:

```
Database → UI   ❌
Service → Scene ❌
NodeItem → Service ❌
```

---

#### Карта зависимостей (визуальная логика)

```
[ UI Layer ]
    ↓
[ Service Layer ]
    ↓
[ Repository Layer ]
    ↓
[ Database Layer ]
```

Зависимости направлены только вниз.

---

## 17. Уровень изоляции

| Слой       | Знает о    | Не знает о    |
| ---------- | ---------- | ------------- |
| UI         | Services   | Database      |
| Services   | Repository | UI            |
| Repository | Database   | UI            |
| Database   | SQLite     | Всё остальное |

---

## 18. Граф зависимостей (концептуально)

```
main
  └── app
        └── main_window
              ├── graph_scene
              │      ├── node_item
              │      ├── edge_item
              │      └── graph_service
              │
              ├── editor_dialog
              │      ├── widgets/*
              │      └── content_service
              │
              └── services
                     ├── graph_service
                     ├── content_service
                     ├── file_service
                     └── content_repository
                             └── database
```

---