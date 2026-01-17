"""
========================================================================
СКРИПТ ДЛЯ СОЗДАНИЯ УСТАНОВЩИКА "КАРТЫ ЖИЗНИ"
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: Жариков Артем Леонидович
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Процесс сборки и конфигурация установщика
                 являются интеллектуальной собственностью автора.
========================================================================
"""

"""
Скрипт для создания установщика
"""
from cx_Freeze import setup, Executable
import sys
import os

# Включаем дополнительные файлы
include_files = [
    ("data/", "data/"),
    ("translations/", "translations/"),
    ("LICENSE", "LICENSE"),
    ("README.md", "README.md")
]

# Исключаем ненужные модули
excludes = ["tkinter", "unittest", "email", "http", "xml"]

# Настройки сборки
build_exe_options = {
    "packages": ["PyQt6", "sqlite3", "json", "pathlib", "datetime", "Crypto"],
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 2
}

# Исполняемый файл
executable = Executable(
    script="main.py",
    base="Win32GUI" if sys.platform == "win32" else None,
    icon="icon.ico",  # Нужно будет создать иконку
    target_name="LifeMap.exe",
    copyright="Copyright © [Ваше Имя] 2024",
    trademarks="Карта жизни является интеллектуальной собственностью автора"
)

# Настройка setup
setup(
    name="Карта жизни",
    version="1.0.0",
    description="Приложение для визуализации и организации жизни",
    options={"build_exe": build_exe_options},
    executables=[executable]
)