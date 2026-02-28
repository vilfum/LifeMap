------------------------------------------------------------------------
АРХИТЕКТУРА (СТРОГАЯ) ПРОЕКТА "КАРТА ЖИЗНИ"
------------------------------------------------------------------------
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
------------------------------------------------------------------------

# LifeMap — Architecture Specification

## 1. Architectural Style

Проект реализован в стиле:

* Layered Architecture
* Separation of Concerns
* Dependency Direction Inward
* UI-independent business logic

---

## 2. Layer Definitions

---

### 2.1 Entry Layer

**Файлы:**

* main.py
* app.py

**Ответственность:**

* Инициализация приложения
* Создание QApplication
* Запуск MainWindow

**Запрещено:**

* Работа с БД
* Бизнес-логика
* Работа с моделями

---

### 2.2 UI Layer (`ui/`, `widgets/`)

**Компоненты:**

* MainWindow
* GraphScene
* NodeItem
* EdgeItem
* EditorDialog
* Tabs (BaseTab descendants)

**Ответственность:**

* Визуализация
* Обработка пользовательского ввода
* Делегирование операций в сервисы

**Правила:**

* Не обращаться напрямую к database
* Не выполнять SQL
* Не хранить бизнес-логику

---

### 2.3 Service Layer (`core/*_service.py`)

**Компоненты:**

* graph_service.py
* content_service.py
* file_service.py

**Ответственность:**

* Бизнес-логика
* Координация операций
* Управление транзакциями
* Валидация данных

**Правила:**

* Не импортировать UI
* Не работать напрямую с Qt
* Работать через repository

---

### 2.4 Repository Layer

**Компоненты:**

* content_repository.py

**Ответственность:**

* Инкапсуляция SQL
* CRUD операции
* Изоляция БД от сервисов

---

### 2.5 Database Layer

**Компонент:**

* database.py

**Ответственность:**

* Подключение
* Инициализация схемы
* Низкоуровневые запросы

---

## 3. Dependency Rules

Разрешенные зависимости:

```
Entry → UI
UI → Services
Services → Repository
Services → Database
Repository → Database
```

Запрещенные зависимости:

```
Database → Services
Database → UI
Services → UI
Repository → UI
NodeItem → Service
```

---

## 4. Data Flow

### 4.1 Создание узла

```
GraphScene
  → GraphService
      → Database
```

---

### 4.2 Редактирование содержимого

```
EditorDialog
  → ContentService
      → ContentRepository
          → Database
```

---

### 4.3 Работа с файлами

```
FilesTab
  → FileService
      → ContentService
          → Repository
              → Database
```

---

## 5. Architectural Guarantees

✔ Нет циклических зависимостей
✔ UI не зависит от БД
✔ Scene не содержит бизнес-логики
✔ SQL изолирован
✔ Расширяемость через BaseTab

---

## 6. Architectural Risks

* Прямой импорт database в UI
* Логика в NodeItem
* Service → UI зависимости
* Нарушение однонаправленного потока

---

## 7. Future Improvements

* Dependency Injection Container
* Event Bus
* Command Pattern (Undo/Redo)
* DTO Layer
* Plugin Loader
* Domain Event System

---