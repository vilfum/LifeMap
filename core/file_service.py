"""
Сервис для работы с файловыми вложениями
"""

"""
========================================================================
СЕРВИС ФАЙЛОВЫХ ВЛОЖЕНИЙ
========================================================================
ЧАСТЬ ПРОЕКТА: Карта жизни (Альфа-версия 1.0)
АВТОР: vilfum
ЛИЦЕНЗИЯ: См. файл LICENSE
КОНФИДЕНЦИАЛЬНО: Логика работы с файлами и папками является
                 интеллектуальной собственностью автора.
========================================================================
"""

from pathlib import Path
import shutil


class FileService:
    def __init__(self, base_path="data/attachments"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_node_folder(self, node_id):
        folder = self.base_path / f"node_{node_id}"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def add_file(self, node_id, source_path):
        source_path = Path(source_path)
        if not source_path.exists():
            return None

        folder = self.get_node_folder(node_id)
        destination = folder / source_path.name

        # автоиндекс если файл существует
        counter = 1
        while destination.exists():
            destination = folder / f"{source_path.stem}_{counter}{source_path.suffix}"
            counter += 1

        shutil.copy2(source_path, destination)

        return destination  # возвращаем полный путь

    def remove_file(self, file_path):
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()

    def file_exists(self, file_path):
        return Path(file_path).exists()
    
    def delete_node_folder(self, node_id):
        folder = self.base_path / f"node_{node_id}"
        if folder.exists():
            try:
                shutil.rmtree(folder)
                print(f"🗑️ Удалена папка узла: {folder}")
            except Exception as e:
                print(f"❌ Ошибка удаления папки узла: {e}")

