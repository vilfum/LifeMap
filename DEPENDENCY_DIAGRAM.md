------------------------------------------------------------------------
ДИАГРАММА ЗАВИСИМОСТЕЙ ПРОЕКТА "КАРТА ЖИЗНИ"
------------------------------------------------------------------------
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
------------------------------------------------------------------------

# LifeMap — Dependency Diagram

Версия: Alpha 1.0
Тип: Layered Architecture
Стиль: Strict Dependency Direction

---

# 1. Основная диаграмма зависимостей (Layered)

```mermaid
flowchart TD

%% Entry
main[main.py] --> app[app.py]

%% UI Layer
app --> MainWindow[ui.main_window]
MainWindow --> GraphScene[ui.graph_scene]
MainWindow --> EditorDialog[ui.editor_dialog]

GraphScene --> NodeItem[ui.node_item]
GraphScene --> EdgeItem[ui.edge_item]

EditorDialog --> Widgets[widgets/*]

%% Service Layer
MainWindow --> GraphService[core.graph_service]
EditorDialog --> ContentService[core.content_service]

%% Widget specific
Widgets --> FileService[core.file_service]

%% Repository Layer
ContentService --> ContentRepo[core.content_repository]

%% Database Layer
ContentRepo --> Database[core.database]
GraphService --> Database

%% Direction styling
classDef layer fill:#f9f9f9,stroke:#333,stroke-width:1px;
```

---

# 2. Строгая диаграмма слоев

```mermaid
flowchart TB

subgraph ENTRY["Entry Layer"]
    main[main.py]
    app[app.py]
end

subgraph UI["UI Layer"]
    MainWindow[MainWindow]
    GraphScene[GraphScene]
    EditorDialog[EditorDialog]
    NodeItem[NodeItem]
    EdgeItem[EdgeItem]
    Widgets[widgets/*]
end

subgraph SERVICE["Service Layer"]
    GraphService[graph_service]
    ContentService[content_service]
    FileService[file_service]
end

subgraph REPO["Repository Layer"]
    ContentRepo[content_repository]
end

subgraph DB["Database Layer"]
    Database[database]
end

ENTRY --> UI
UI --> SERVICE
SERVICE --> REPO
SERVICE --> DB
REPO --> DB
```

---

# 3. Полный граф зависимостей модулей

```mermaid
flowchart LR

main --> app
app --> MainWindow

MainWindow --> GraphScene
MainWindow --> EditorDialog
MainWindow --> GraphService
MainWindow --> ContentService

GraphScene --> NodeItem
GraphScene --> EdgeItem
GraphScene --> GraphService

EditorDialog --> Widgets
EditorDialog --> ContentService

Widgets --> FileService

ContentService --> ContentRepo
ContentRepo --> Database

GraphService --> Database
```

---