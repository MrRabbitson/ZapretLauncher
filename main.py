import os
import sys
import ctypes
import zipfile
import requests
import shutil
import subprocess
import re
import customtkinter as ctk
from tkinter import messagebox
from threading import Thread


# Проверка прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


# Запуск файла от имени администратора и захват вывода
def run_as_admin(bat_file):
    if not os.path.exists(bat_file):
        return False, "Файл не найден"

    try:
        result = subprocess.run(
            ["cmd.exe", "/c", bat_file],
            capture_output=True,
            text=True,
            shell=True
        )
        return True, result.stdout
    except Exception as e:
        return False, str(e)


# Скачивание и обновление zapret
def update_zapret():
    try:
        # URL архива с GitHub
        repo_url = "https://github.com/Flowseal/zapret-discord-youtube/archive/refs/heads/main.zip"
        temp_dir = os.path.dirname(__file__)
        zip_path = os.path.join(temp_dir, "zapret_update.zip")

        # Скачивание архива
        response = requests.get(repo_url, stream=True)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Удаление старой папки zapret (если есть)
        zapret_dir = os.path.join(temp_dir, "zapret")
        if os.path.exists(zapret_dir):
            shutil.rmtree(zapret_dir)

        # Распаковка архива
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Переименование папки
        extracted_dir = os.path.join(temp_dir, "zapret-discord-youtube-main")
        if os.path.exists(extracted_dir):
            os.rename(extracted_dir, zapret_dir)

        # Удаление временного архива
        os.remove(zip_path)

        return True, "Обновление успешно завершено"
    except Exception as e:
        return False, f"Ошибка обновления: {str(e)}"


# Проверка наличия необходимых файлов
def check_files():
    required_files = {
        "zapret": ["general.bat", "service.bat"]
    }

    for folder, files in required_files.items():
        folder_path = os.path.join(os.path.dirname(__file__), folder)
        if not os.path.exists(folder_path):
            return False

        for file in files:
            if not os.path.exists(os.path.join(folder_path, file)):
                return False
    return True


# Поиск URL в тексте
def find_url(text):
    url_pattern = re.compile(r'https?://\S+')
    match = url_pattern.search(text)
    return match.group(0) if match else None


class ZapretLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Zapret Launcher")
        self.geometry("400x300")
        self.resizable(False, False)
        self.zapret_dir = os.path.join(os.path.dirname(__file__), "zapret")
        self.general_bat = os.path.join(self.zapret_dir, "general.bat")
        self.service_bat = os.path.join(self.zapret_dir, "service.bat")
        # Основной фрейм
        self.frame = ctk.CTkFrame(self, fg_color="#16181c")
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.configure(fg_color="#2b2b2b")  # Серый цвет фона
        # Заголовок
        self.label = ctk.CTkLabel(
            self.frame,
            text="Zapret Launcher",
            font=("Arial", 20, "bold"),
            text_color="#00af5c"
        )
        self.label.pack(pady=10)

        # Кнопка старта
        self.start_btn = ctk.CTkButton(
            self.frame,
            text="Старт",
            command=self.run_general,
            fg_color="#00af5c",
            hover_color="#008a4a",
            font=("Arial", 14)
        )
        self.start_btn.pack(pady=10, padx=20, fill="x")

        # Кнопка управления автозагрузкой
        self.service_btn = ctk.CTkButton(
            self.frame,
            text="Управление автозагрузкой",
            command=self.run_service,
            fg_color="#00af5c",
            hover_color="#008a4a",
            font=("Arial", 14)
        )
        self.service_btn.pack(pady=10, padx=20, fill="x")

        # Кнопка обновления
        self.update_btn = ctk.CTkButton(
            self.frame,
            text="Обновить Zapret",
            command=self.run_update,
            fg_color="#00af5c",
            hover_color="#008a4a",
            font=("Arial", 14)
        )
        self.update_btn.pack(pady=10, padx=20, fill="x")

        # Статус
        self.status = ctk.CTkLabel(
            self.frame,
            text="Готов к работе",
            font=("Arial", 12),
            text_color="gray70"
        )
        self.status.pack(pady=10)

        # Автопроверка файлов при запуске
        if not check_files():
            self.status.configure(text="Файлы не найдены, начинаю обновление...")
            Thread(target=self.auto_update).start()

    def run_in_same_console(self, bat_file):
        """Запуск BAT-файла в текущей консоли"""
        if not is_admin():
            # Запрашиваем права админа с перезапуском
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                f'"{sys.argv[0]}" --admin-run "{bat_file}"',
                None, 1
            )
        else:
            # Если права есть - запуск напрямую
            os.chdir(os.path.dirname(bat_file))
            os.system(os.path.basename(bat_file))
    def auto_update(self):
        success, message = update_zapret()
        if success:
            self.status.configure(text="Обновление завершено")
            messagebox.showinfo("Успех", message)
        else:
            self.status.configure(text="Ошибка обновления")
            messagebox.showerror("Ошибка", message)

    def run_general(self):
        self.run_in_same_console(self.general_bat)

    def run_service(self):
        self.run_in_same_console(self.service_bat)

    def run_update(self):
        self.status.configure(text="Проверка обновлений...")
        Thread(target=self.auto_update).start()


if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    app = ZapretLauncher()
    app.mainloop()