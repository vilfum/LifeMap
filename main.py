"""
========================================================================
КАРТА ЖИЗНИ - PERSONAL LIFE MAPPING SYSTEM (Альфа-версия 1.0)
========================================================================
АВТОР: vilfum
ДАТА НАЧАЛА РАЗРАБОТКИ: 17/01/2026
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
    #app.setStyleSheet("""
    #    QMainWindow {
    #        background: #f0f0f0;
    #    }
    #    QGraphicsView {
    #        border: 0px;
    #        outline: 0px;
    #        background: transparent;
    #    }
    #""")

    # Устанавливаем глобальный стиль для всего приложения
    app.setStyleSheet("""
        /* Стиль для всех меню */
        QMenu {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            color: #333333;
            padding: 4px;
        }
        
        QMenu::item {
            background-color: transparent;
            padding: 6px 24px 6px 8px;
            margin: 2px 4px;
            border-radius: 3px;
        }
        
        QMenu::item:selected {
            background-color: #e0e0e0;
            color: #000000;
        }
        
        QMenu::item:disabled {
            color: #999999;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #dddddd;
            margin: 4px 8px;
        }
        
        /* Стиль для панели инструментов */
        QToolBar {
            background-color: #2b2b2b;
            border: none;
            spacing: 3px;
            padding: 2px;
        }
        
        QToolBar QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 4px;
            color: #ffffff;
        }
        
        QToolBar QToolButton:hover {
            background-color: #404040;
            border: 1px solid #505050;
        }
        
        QToolBar QToolButton:pressed {
            background-color: #505050;
        }
        
        /* Стиль для QGraphicsView */
        QGraphicsView {
            border: 0px;
            outline: 0px;
            background: transparent;
        }
        
        QGraphicsView::rubberBand {
            border: 2px dashed #2196F3;
            background-color: rgba(33, 150, 243, 30);
        }
    """)
    
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
