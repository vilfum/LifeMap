import os
import sys
import subprocess

def main():
    print("=" * 50)
    print("LIFE MAP - Starting...")
    print("=" * 50)

    # Проверяем пути
    python_path = r"D:\Python\python.exe"
    script_path = r"D:\LifeMap\main.py"

    print(f"Python: {python_path}")
    print(f"Script: {script_path}")

    # Проверяем существование файлов
    if not os.path.exists(python_path):
        print(f"ERROR: Python not found at {python_path}")
        input("Press Enter to exit...")
        return

    if not os.path.exists(script_path):
        print(f"ERROR: Script not found at {script_path}")
        input("Press Enter to exit...")
        return

    # Запускаем программу
    print("\nLaunching Life Map...")
    print("-" * 50)

    try:
        subprocess.run([python_path, script_path])
    except Exception as e:
        print(f"ERROR: {e}")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()