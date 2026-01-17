"""
========================================================================
КАРТА ЖИЗНИ - PERSONAL LIFE MAPPING SYSTEM (Альфа-версия 1.0)
========================================================================
АВТОР: [Ваше Имя]
ДАТА НАЧАЛА РАЗРАБОТКИ: [Укажите дату]
ВЕРСИЯ: 1.0 (Альфа)
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНТАКТ: [Ваш email]
========================================================================

ЛИЦЕНЗИОННОЕ УВЕДОМЛЕНИЕ:
Данная программа находится на стадии активной разработки.
Разрешено только личное некоммерческое тестирование.
Запрещено распространение, модификация и коммерческое использование.
Авторские права © [Ваше Имя], 2024. Все права защищены.

ПРОГРАММА ПРЕДОСТАВЛЯЕТСЯ "КАК ЕСТЬ" БЕЗ ГАРАНТИЙ ЛЮБОГО РОДА.
========================================================================
"""

"""
Точка входа в приложение
"""
import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale, QTranslator
from PyQt6.QtGui import QFont

from ui_main_window import MainWindow


def setup_application():
    """Настройка приложения"""
    # Создаем необходимые директории
    Path("data/attachments").mkdir(parents=True, exist_ok=True)
    Path("data/templates").mkdir(parents=True, exist_ok=True)
    Path("data/exports").mkdir(parents=True, exist_ok=True)
    
    # Создаем приложение
    app = QApplication(sys.argv)
    
    # Настройка шрифта
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Настройка локализации
    translator = QTranslator()
    locale = QLocale.system().name()
    
    # Пробуем загрузить перевод (если есть)
    if translator.load(f"translations/{locale}.qm"):
        app.installTranslator(translator)
    
    # Установка стиля
    app.setStyle("Fusion")
    
    return app


def main():
    """Основная функция"""
    # Настройка приложения
    app = setup_application()
    
    # Создание главного окна
    window = MainWindow()
    window.show()
    
    # Запуск главного цикла
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
