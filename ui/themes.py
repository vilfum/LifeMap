"""
========================================================================
МЕНЕДЖЕР ТЕМ ДЛЯ "КАРТЫ ЖИЗНИ"
========================================================================
"""
from pathlib import Path

_dark_mode = False

def set_dark_mode(enabled: bool):
    """Установить глобальное состояние тёмной темы"""
    global _dark_mode
    _dark_mode = enabled

def is_dark_mode() -> bool:
    """Получить текущее состояние тёмной темы"""
    return _dark_mode

def get_stylesheet() -> str:
    """Загрузить и вернуть stylesheet для текущей темы"""
    style_file = Path("resources/styles/dark.qss" if _dark_mode else "resources/styles/light.qss")
    if style_file.exists():
        return style_file.read_text(encoding='utf-8')
    return ""