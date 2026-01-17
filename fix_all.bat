@echo off
echo Исправление файлов проекта...

rem Удаляем обратные кавычки из начала файлов
powershell -Command "(Get-Content 'main.py') -replace '^```python', '' | Set-Content 'main.py'"
powershell -Command "(Get-Content 'database.py') -replace '^```python', '' | Set-Content 'database.py'"
powershell -Command "(Get-Content 'models.py') -replace '^```python', '' | Set-Content 'models.py'"
powershell -Command "(Get-Content 'ui_main_window.py') -replace '^```python', '' | Set-Content 'ui_main_window.py'"
powershell -Command "(Get-Content 'ui_graph_scene.py') -replace '^```python', '' | Set-Content 'ui_graph_scene.py'"
powershell -Command "(Get-Content 'ui_node_item.py') -replace '^```python', '' | Set-Content 'ui_node_item.py'"
powershell -Command "(Get-Content 'ui_edge_item.py') -replace '^```python', '' | Set-Content 'ui_edge_item.py'"

echo Файлы исправлены!
pause