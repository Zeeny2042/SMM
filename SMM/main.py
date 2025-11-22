import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import subprocess
import threading
import requests
import sys
import time
import json

class MinecraftServerManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Server Manager")
        self.root.geometry("1000x700")
        
        # Переменные
        self.server_process = None
        self.current_project_path = None
        self.server_running = False
        self.projects_data = {}
        self.current_step = 1
        self.config = {}
        
        # Загружаем конфигурацию
        self.load_config()
        
        # Пути из конфигурации
        self.default_projects_path = os.path.join(os.getcwd(), self.config["default_settings"]["projects_path"])
        self.cores_path = os.path.join(os.getcwd(), self.config["default_settings"]["cores_path"])
        
        # Создаем папки по умолчанию
        self.create_default_folders()
        
        # Загружаем данные проектов
        self.load_projects_data()
        
        self.create_widgets()
    
    def load_config(self):
        """Загружает конфигурацию из config.json"""
        config_path = os.path.join(os.getcwd(), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                # Создаем базовый конфиг если файл поврежден
                self.create_default_config()
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Создает конфигурацию по умолчанию"""
        self.config = {
            "core_urls": {
                "Purpur": "https://api.purpurmc.org/v2/purpur/{version}/latest/download",
                "Paper": "https://api.papermc.io/v2/projects/paper/versions/{version}/builds/latest/downloads/paper-{version}-latest.jar",
                "Fabric": "https://meta.fabricmc.net/v2/versions/loader/{version}/0.14.21/0.11.2/server/jar",
                "Forge": "https://maven.minecraftforge.net/net/minecraftforge/forge/{version}/forge-{version}-installer.jar",
                "Vanilla": "https://piston-data.mojang.com/v1/objects/{hash}/server.jar"
            },
            "vanilla_hashes": {
                "1.21.4": "84194a2f286ef7c14ed7ce0090dba59902951553",
                "1.21.1": "84194a2f286ef7c14ed7ce0090dba59902951553",
                "1.20.6": "84194a2f286ef7c14ed7ce0090dba59902951553",
                "1.20.1": "15c777e2cdf05598e0c6fba5fec1cfd2c9751b95",
                "1.19.4": "8f3112a1049751cc472ec13e397eade5336ca7ae",
                "1.18.2": "c8f83c5655308435b3dcf03c06d9fe8740a77469",
                "1.17.1": "943d9876b0dcecc7d0d0b5eabf0e8b2c733c75c1",
                "1.16.5": "1b557e7b033b583cd9f66746b7a9a1eb5de295b8"
            },
            "available_versions": {
                "Purpur": ["1.21.4", "1.21.1", "1.20.6", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"],
                "Paper": ["1.21.4", "1.21.1", "1.20.6", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"],
                "Fabric": ["1.21.4", "1.21.1", "1.20.6", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"],
                "Forge": ["1.21.4", "1.21.1", "1.20.6", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"],
                "Vanilla": ["1.21.4", "1.21.1", "1.20.6", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5"]
            },
            "default_settings": {
                "projects_path": "projects",
                "cores_path": "cores",
                "default_ram": "2G",
                "server_port": "25565",
                "max_players": "20"
            }
        }
        
        # Сохраняем конфиг
        config_path = os.path.join(os.getcwd(), "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def create_default_folders(self):
        """Создает папки по умолчанию"""
        os.makedirs(self.default_projects_path, exist_ok=True)
        os.makedirs(self.cores_path, exist_ok=True)
    
    def load_projects_data(self):
        """Загружает данные о проектах"""
        projects_file = os.path.join(os.getcwd(), "projects.json")
        if os.path.exists(projects_file):
            try:
                with open(projects_file, 'r', encoding='utf-8') as f:
                    self.projects_data = json.load(f)
            except:
                self.projects_data = {}
    
    def save_projects_data(self):
        """Сохраняет данные о проектах"""
        projects_file = os.path.join(os.getcwd(), "projects.json")
        try:
            with open(projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects_data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def create_widgets(self):
        # Главный контейнер с разделителем
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - файловый менеджер и управление
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Правая панель - консоль сервера
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Левая панель: Вкладки
        left_notebook = ttk.Notebook(left_frame)
        left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка проектов
        self.projects_frame = ttk.Frame(left_notebook)
        left_notebook.add(self.projects_frame, text="Проекты")
        self.create_projects_tab()
        
        # Вкладка файлов
        self.files_frame = ttk.Frame(left_notebook)
        left_notebook.add(self.files_frame, text="Файлы")
        self.create_files_tab()
        
        # Вкладка плагинов
        self.plugins_frame = ttk.Frame(left_notebook)
        left_notebook.add(self.plugins_frame, text="Плагины")
        self.create_plugins_tab()

        # Вкладка загрузки ядер
        self.cores_frame = ttk.Frame(left_notebook)
        left_notebook.add(self.cores_frame, text="Ядра")
        self.create_cores_tab()
        
        # Правая панель: Консоль сервера
        self.create_console_tab(right_frame)
    
    def create_projects_tab(self):
        # Заголовок
        title_label = ttk.Label(self.projects_frame, text="Управление серверами", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)
        
        # Область информации о проекте
        info_frame = ttk.LabelFrame(self.projects_frame, text="Текущий проект")
        info_frame.pack(pady=10, fill='x', padx=10)
        
        self.project_info_var = tk.StringVar(value="Проект не выбран")
        project_label = ttk.Label(info_frame, textvariable=self.project_info_var, wraplength=300)
        project_label.pack(pady=5, padx=5)
        
        # Список проектов
        projects_list_frame = ttk.LabelFrame(self.projects_frame, text="Мои проекты")
        projects_list_frame.pack(pady=10, fill='both', expand=True, padx=10)
        
        # Панель инструментов для проектов
        projects_toolbar = ttk.Frame(projects_list_frame)
        projects_toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(projects_toolbar, text="Создать новый", 
                  command=self.create_new_project).pack(side='left', padx=2)
        ttk.Button(projects_toolbar, text="Обновить список", 
                  command=self.refresh_projects_list).pack(side='left', padx=2)
        
        # Список проектов
        self.projects_listbox = tk.Listbox(projects_list_frame, height=8)
        self.projects_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.projects_listbox.bind('<<ListboxSelect>>', self.on_project_selected)
        
        # Кнопка загрузки выбранного проекта
        ttk.Button(projects_list_frame, text="Загрузить выбранный проект", 
                  command=self.load_selected_project).pack(pady=5)
        
        # Обновляем список проектов
        self.refresh_projects_list()
        
        # Управление сервером
        control_frame = ttk.LabelFrame(self.projects_frame, text="Управление сервером")
        control_frame.pack(pady=10, fill='x', padx=10)
        
        self.start_btn = ttk.Button(control_frame, text="Запустить сервер", 
                                   command=self.start_server)
        self.start_btn.pack(pady=5, padx=10, fill='x')
        
        self.stop_btn = ttk.Button(control_frame, text="Остановить сервер", 
                                  command=self.stop_server, state='disabled')
        self.stop_btn.pack(pady=5, padx=10, fill='x')
        
        # Статус сервера
        self.status_var = tk.StringVar(value="Статус: Сервер остановлен")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, 
                                foreground='red', font=('Arial', 10, 'bold'))
        status_label.pack(pady=5)
        
        # Быстрые команды
        commands_frame = ttk.LabelFrame(self.projects_frame, text="Быстрые команды")
        commands_frame.pack(pady=10, fill='x', padx=10)
        
        cmd_btn_frame = ttk.Frame(commands_frame)
        cmd_btn_frame.pack(pady=5)
        
        ttk.Button(cmd_btn_frame, text="Say Hello", 
                  command=lambda: self.send_command("say Привет от Minecraft Manager!")).pack(side='left', padx=2)
        ttk.Button(cmd_btn_frame, text="List Players", 
                  command=lambda: self.send_command("list")).pack(side='left', padx=2)
        ttk.Button(cmd_btn_frame, text="Save All", 
                  command=lambda: self.send_command("save-all")).pack(side='left', padx=2)
    
    def refresh_projects_list(self):
        """Обновляет список проектов"""
        self.projects_listbox.delete(0, 'end')
        
        if os.path.exists(self.default_projects_path):
            for item in os.listdir(self.default_projects_path):
                item_path = os.path.join(self.default_projects_path, item)
                if os.path.isdir(item_path):
                    if os.path.exists(os.path.join(item_path, "server.jar")):
                        self.projects_listbox.insert('end', item)
    
    def on_project_selected(self, event):
        """Обработчик выбора проекта в списке"""
        selection = self.projects_listbox.curselection()
        if selection:
            project_name = self.projects_listbox.get(selection[0])
            project_path = os.path.join(self.default_projects_path, project_name)
            self.project_info_var.set(f"Выбран: {project_name}\nГотов к загрузке")
    
    def load_selected_project(self):
        """Загружает выбранный проект"""
        selection = self.projects_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите проект из списка")
            return
        
        project_name = self.projects_listbox.get(selection[0])
        project_path = os.path.join(self.default_projects_path, project_name)
        
        if os.path.exists(os.path.join(project_path, "server.jar")):
            self.current_project_path = project_path
            self.project_info_var.set(f"Проект: {project_name}\nПуть: {project_path}")
            self.refresh_file_list()
            self.refresh_plugins_list()
            self.log_to_console(f"Загружен проект: {project_name}")
            
            # Сохраняем в историю
            if project_name not in self.projects_data:
                self.projects_data[project_name] = {
                    "path": project_path,
                    "last_loaded": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "created": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                self.projects_data[project_name]["last_loaded"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            self.save_projects_data()
        else:
            messagebox.showerror("Ошибка", "В выбранной папке нет server.jar файла")
    
    def create_files_tab(self):
        # Панель инструментов файлового менеджера
        toolbar = ttk.Frame(self.files_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Обновить", command=self.refresh_file_list).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Открыть папку", command=self.open_project_folder).pack(side='left', padx=2)
        
        # Список файлов
        file_list_frame = ttk.Frame(self.files_frame)
        file_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Заголовки столбцов
        columns = ('name', 'size', 'type')
        self.file_tree = ttk.Treeview(file_list_frame, columns=columns, show='headings')
        
        self.file_tree.heading('name', text='Имя файла')
        self.file_tree.heading('size', text='Размер')
        self.file_tree.heading('type', text='Тип')
        
        self.file_tree.column('name', width=200)
        self.file_tree.column('size', width=100)
        self.file_tree.column('type', width=100)
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(file_list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Двойной клик для открытия файлов
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
    
    def refresh_file_list(self):
        if not self.current_project_path:
            return
        
        # Очищаем список
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Добавляем файлы
        try:
            for item in os.listdir(self.current_project_path):
                item_path = os.path.join(self.current_project_path, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    file_type = "Файл"
                    if item.endswith('.jar'):
                        file_type = "JAR"
                    elif item.endswith('.properties'):
                        file_type = "Настройки"
                    elif item.endswith('.bat'):
                        file_type = "Скрипт"
                    
                    self.file_tree.insert('', 'end', values=(
                        item, 
                        self.format_file_size(size),
                        file_type
                    ))
                else:
                    self.file_tree.insert('', 'end', values=(
                        f"[{item}]", 
                        "Папка", 
                        "Директория"
                    ))
        except Exception as e:
            self.log_to_console(f"Ошибка при обновлении списка файлов: {str(e)}")
    
    def format_file_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def on_file_double_click(self, event):
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            file_name = item['values'][0]
            
            if file_name.startswith('[') and file_name.endswith(']'):
                # Это папка
                folder_name = file_name[1:-1]
                folder_path = os.path.join(self.current_project_path, folder_name)
                try:
                    if sys.platform == "win32":
                        os.startfile(folder_path)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", folder_path])
                    else:
                        subprocess.Popen(["xdg-open", folder_path])
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")
            else:
                # Это файл
                file_path = os.path.join(self.current_project_path, file_name)
                try:
                    if sys.platform == "win32":
                        os.startfile(file_path)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", file_path])
                    else:
                        subprocess.Popen(["xdg-open", file_path])
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
    
    def open_project_folder(self):
        if self.current_project_path:
            try:
                if sys.platform == "win32":
                    os.startfile(self.current_project_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", self.current_project_path])
                else:
                    subprocess.Popen(["xdg-open", self.current_project_path])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")
        else:
            messagebox.showwarning("Предупреждение", "Сначала выберите проект")
    
    def create_plugins_tab(self):
        # Информация
        info_label = ttk.Label(self.plugins_frame, 
                              text="Управление плагинами сервера",
                              justify='center')
        info_label.pack(pady=10)
        
        # Панель управления плагинами
        plugin_controls = ttk.Frame(self.plugins_frame)
        plugin_controls.pack(pady=5, fill='x', padx=10)
        
        ttk.Button(plugin_controls, text="Загрузить плагин", 
                  command=self.upload_plugin).pack(side='left', padx=2)
        ttk.Button(plugin_controls, text="Открыть папку plugins", 
                  command=self.open_plugins_folder).pack(side='left', padx=2)
        ttk.Button(plugin_controls, text="Обновить список", 
                  command=self.refresh_plugins_list).pack(side='left', padx=2)
        
        # Список плагинов
        plugins_list_frame = ttk.LabelFrame(self.plugins_frame, text="Установленные плагины")
        plugins_list_frame.pack(pady=10, fill='both', expand=True, padx=10)
        
        self.plugins_list = tk.Listbox(plugins_list_frame)
        self.plugins_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Кнопка удаления плагина
        ttk.Button(plugins_list_frame, text="Удалить выбранный плагин", 
                  command=self.delete_plugin).pack(pady=5)
    
    def upload_plugin(self):
        if not self.current_project_path:
            messagebox.showerror("Ошибка", "Сначала создайте или выберите проект")
            return
        
        file_path = filedialog.askopenfilename(
            title="Выберите файл плагина",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        
        if file_path:
            plugins_dir = os.path.join(self.current_project_path, "plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            
            plugin_name = os.path.basename(file_path)
            dest_path = os.path.join(plugins_dir, plugin_name)
            
            try:
                shutil.copy2(file_path, dest_path)
                self.log_to_console(f"Плагин '{plugin_name}' успешно загружен")
                self.refresh_plugins_list()
                
                if self.server_running:
                    messagebox.showinfo("Успех", 
                                      "Плагин загружен. Для применения изменений перезапустите сервер")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить плагин: {str(e)}")
    
    def open_plugins_folder(self):
        if not self.current_project_path:
            messagebox.showerror("Ошибка", "Сначала создайте или выберите проект")
            return
        
        plugins_path = os.path.join(self.current_project_path, "plugins")
        os.makedirs(plugins_path, exist_ok=True)
        
        try:
            if sys.platform == "win32":
                os.startfile(plugins_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", plugins_path])
            else:
                subprocess.Popen(["xdg-open", plugins_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")
    
    def refresh_plugins_list(self):
        if not self.current_project_path:
            return
        
        plugins_path = os.path.join(self.current_project_path, "plugins")
        self.plugins_list.delete(0, 'end')
        
        if os.path.exists(plugins_path):
            for file in os.listdir(plugins_path):
                if file.endswith('.jar'):
                    self.plugins_list.insert('end', file)
    
    def delete_plugin(self):
        if not self.current_project_path:
            return
        
        selection = self.plugins_list.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите плагин для удаления")
            return
        
        plugin_name = self.plugins_list.get(selection[0])
        plugins_path = os.path.join(self.current_project_path, "plugins", plugin_name)
        
        if os.path.exists(plugins_path):
            try:
                os.remove(plugins_path)
                self.log_to_console(f"Плагин '{plugin_name}' удален")
                self.refresh_plugins_list()
                
                if self.server_running:
                    messagebox.showinfo("Успех", 
                                      "Плагин удален. Для применения изменений перезапустите сервер")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить плагин: {str(e)}")
    
    def create_cores_tab(self):
        """Вкладка для управления ядрами сервера"""
        # Заголовок
        title_label = ttk.Label(self.cores_frame, text="Управление ядрами серверов", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)
        
        # Информация
        info_label = ttk.Label(self.cores_frame, 
                              text="Здесь вы можете скачать ядра для серверов Minecraft",
                              justify='center')
        info_label.pack(pady=5)
        
        # Выбор типа и версии
        selection_frame = ttk.LabelFrame(self.cores_frame, text="Выбор ядра")
        selection_frame.pack(pady=10, fill='x', padx=10)
        
        # Тип ядра
        type_frame = ttk.Frame(selection_frame)
        type_frame.pack(pady=5, fill='x', padx=5)
        
        ttk.Label(type_frame, text="Тип:").pack(side='left')
        self.core_type_var = tk.StringVar(value="Purpur")
        core_type_combo = ttk.Combobox(type_frame, textvariable=self.core_type_var,
                                      values=list(self.config["available_versions"].keys()),
                                      state="readonly")
        core_type_combo.pack(side='left', padx=5)
        core_type_combo.bind('<<ComboboxSelected>>', self.on_core_type_changed)
        
        # Версия
        version_frame = ttk.Frame(selection_frame)
        version_frame.pack(pady=5, fill='x', padx=5)
        
        ttk.Label(version_frame, text="Версия:").pack(side='left')
        self.core_version_var = tk.StringVar()
        self.core_version_combo = ttk.Combobox(version_frame, textvariable=self.core_version_var,
                                              state="readonly")
        self.core_version_combo.pack(side='left', padx=5)
        
        # Обновляем версии при запуске
        self.on_core_type_changed()
        
        # Кнопка скачивания
        download_btn = ttk.Button(selection_frame, text="Скачать ядро", 
                                 command=self.download_core)
        download_btn.pack(pady=10)
        
        # Прогресс бар
        self.download_progress = ttk.Progressbar(selection_frame, mode='determinate')
        self.download_progress.pack(pady=5, fill='x', padx=5)
        
        # Статус загрузки
        self.download_status_var = tk.StringVar(value="Готов к загрузке")
        download_status_label = ttk.Label(selection_frame, textvariable=self.download_status_var)
        download_status_label.pack(pady=5)
        
        # Список скачанных ядер
        downloaded_frame = ttk.LabelFrame(self.cores_frame, text="Скачанные ядра")
        downloaded_frame.pack(pady=10, fill='both', expand=True, padx=10)
        
        # Панель инструментов
        downloaded_toolbar = ttk.Frame(downloaded_frame)
        downloaded_toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(downloaded_toolbar, text="Обновить список", 
                  command=self.refresh_downloaded_cores).pack(side='left', padx=2)
        ttk.Button(downloaded_toolbar, text="Открыть папку ядер", 
                  command=self.open_cores_folder).pack(side='left', padx=2)
        
        # Список ядер
        self.cores_listbox = tk.Listbox(downloaded_frame)
        self.cores_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Обновляем список скачанных ядер
        self.refresh_downloaded_cores()
    
    def on_core_type_changed(self, event=None):
        """Обновляет список версий при изменении типа ядра"""
        core_type = self.core_type_var.get()
        if core_type in self.config["available_versions"]:
            versions = self.config["available_versions"][core_type]
            self.core_version_combo['values'] = versions
            if versions:
                self.core_version_var.set(versions[0])
    
    def download_core(self):
        """Скачивает выбранное ядро"""
        core_type = self.core_type_var.get()
        version = self.core_version_var.get()
        
        if not core_type or not version:
            messagebox.showerror("Ошибка", "Выберите тип и версию ядра")
            return
        
        # Запускаем загрузку в отдельном потоке
        threading.Thread(target=self._download_core_thread, 
                        args=(core_type, version), daemon=True).start()
    
    def _download_core_thread(self, core_type, version):
        """Поток для загрузки ядра"""
        try:
            self.root.after(0, lambda: self.download_status_var.set(f"Начинаю загрузку {core_type} {version}..."))
            self.root.after(0, lambda: self.download_progress.config(value=0))
            
            # Формируем URL для загрузки
            download_url = self.get_download_url(core_type, version)
            if not download_url:
                self.root.after(0, lambda: self.download_status_var.set("Ошибка: не удалось получить URL для загрузки"))
                return
            
            # Имя файла для сохранения
            filename = f"{core_type}_{version}.jar"
            filepath = os.path.join(self.cores_path, filename)
            
            # Скачиваем файл
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # Получаем общий размер файла
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.root.after(0, lambda p=progress: self.download_progress.config(value=p))
            
            self.root.after(0, lambda: self.download_progress.config(value=100))
            self.root.after(0, lambda: self.download_status_var.set(f"Успешно скачано: {filename}"))
            self.root.after(0, self.refresh_downloaded_cores)
            
        except Exception as e:
            # ИСПРАВЛЕНИЕ: Сохраняем ошибку в переменную перед использованием в лямбде
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.download_status_var.set(f"Ошибка загрузки: {msg}"))
    
    def get_download_url(self, core_type, version):
        """Возвращает URL для скачивания ядра"""
        if core_type in self.config["core_urls"]:
            url_template = self.config["core_urls"][core_type]
            if core_type == "Vanilla":
                if version in self.config["vanilla_hashes"]:
                    hash_value = self.config["vanilla_hashes"][version]
                    return url_template.replace("{hash}", hash_value)
            else:
                return url_template.replace("{version}", version)
        return None
    
    def refresh_downloaded_cores(self):
        """Обновляет список скачанных ядер"""
        self.cores_listbox.delete(0, 'end')
        
        if os.path.exists(self.cores_path):
            for file in os.listdir(self.cores_path):
                if file.endswith('.jar'):
                    self.cores_listbox.insert('end', file)
    
    def open_cores_folder(self):
        """Открывает папку с ядрами"""
        if os.path.exists(self.cores_path):
            try:
                if sys.platform == "win32":
                    os.startfile(self.cores_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", self.cores_path])
                else:
                    subprocess.Popen(["xdg-open", self.cores_path])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")
    
    def create_console_tab(self, parent):
        # Заголовок консоли
        console_header = ttk.Frame(parent)
        console_header.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(console_header, text="Консоль сервера", 
                 font=('Arial', 12, 'bold')).pack(side='left')
        
        # Кнопки управления консолью
        console_controls = ttk.Frame(console_header)
        console_controls.pack(side='right')
        
        ttk.Button(console_controls, text="Очистить", 
                  command=self.clear_console).pack(side='left', padx=2)
        ttk.Button(console_controls, text="Скопировать", 
                  command=self.copy_console).pack(side='left', padx=2)
        
        # Сама консоль
        console_frame = ttk.Frame(parent)
        console_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD,
            bg='black',
            fg='white',
            font=('Consolas', 10)
        )
        self.console_text.pack(fill='both', expand=True)
        
        # Поле ввода команд
        command_frame = ttk.Frame(parent)
        command_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(command_frame, text="Команда:").pack(side='left', padx=5)
        
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(command_frame, textvariable=self.command_var, width=50)
        self.command_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.command_entry.bind('<Return>', self.send_command_from_entry)
        
        ttk.Button(command_frame, text="Отправить", 
                  command=self.send_command_from_entry).pack(side='left', padx=5)
    
    def clear_console(self):
        self.console_text.config(state='normal')
        self.console_text.delete(1.0, 'end')
        self.console_text.config(state='disabled')
    
    def copy_console(self):
        try:
            text = self.console_text.get(1.0, 'end')
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Успех", "Текст консоли скопирован в буфер обмена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать текст: {str(e)}")
    
    def send_command(self, command):
        if self.server_running and self.server_process:
            try:
                self.server_process.stdin.write(command + "\n")
                self.server_process.stdin.flush()
                self.log_to_console(f"> {command}")
            except Exception as e:
                self.log_to_console(f"Ошибка отправки команды: {str(e)}")
        else:
            messagebox.showwarning("Предупреждение", "Сервер не запущен")
    
    def send_command_from_entry(self, event=None):
        command = self.command_var.get().strip()
        if command:
            self.send_command(command)
            self.command_var.set("")
    
    def log_to_console(self, message):
        def update_console():
            self.console_text.config(state='normal')
            self.console_text.insert('end', message + "\n")
            self.console_text.see('end')
            self.console_text.config(state='disabled')
        
        self.root.after(0, update_console)
    
    def create_new_project(self):
        # Окно создания проекта
        self.project_window = tk.Toplevel(self.root)
        self.project_window.title("Создание нового проекта сервера")
        self.project_window.geometry("500x500")
        self.project_window.transient(self.root)
        self.project_window.grab_set()
        
        self.current_step = 1
        self.show_project_creation_step()
    
    def show_project_creation_step(self):
        """Показывает текущий шаг создания проекта"""
        # Очищаем окно
        for widget in self.project_window.winfo_children():
            widget.destroy()
        
        if self.current_step == 1:
            self.show_step1()
        elif self.current_step == 2:
            self.show_step2()
        elif self.current_step == 3:
            self.show_step3()
    
    def show_step1(self):
        """Шаг 1: Выбор ядра"""
        step1_frame = ttk.LabelFrame(self.project_window, text="Шаг 1: Выбор ядра сервера")
        step1_frame.pack(pady=10, fill='x', padx=20)
        
        # Вариант 1: Скачать ядро через программу
        download_frame = ttk.Frame(step1_frame)
        download_frame.pack(pady=10, fill='x')
        
        ttk.Label(download_frame, text="Скачать ядро через программу:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # Выбор типа ядра
        type_frame = ttk.Frame(download_frame)
        type_frame.pack(pady=5, fill='x')
        
        ttk.Label(type_frame, text="Тип ядра:").pack(side='left')
        self.project_core_type_var = tk.StringVar(value="Purpur")
        core_type_combo = ttk.Combobox(type_frame, textvariable=self.project_core_type_var,
                                      values=list(self.config["available_versions"].keys()),
                                      state="readonly")
        core_type_combo.pack(side='left', padx=5)
        core_type_combo.bind('<<ComboboxSelected>>', self.on_project_core_type_changed)
        
        # Выбор версии
        version_frame = ttk.Frame(download_frame)
        version_frame.pack(pady=5, fill='x')
        
        ttk.Label(version_frame, text="Версия:").pack(side='left')
        self.project_core_version_var = tk.StringVar()
        self.project_core_version_combo = ttk.Combobox(version_frame, 
                                                      textvariable=self.project_core_version_var,
                                                      state="readonly")
        self.project_core_version_combo.pack(side='left', padx=5)
        
        # Обновляем версии
        self.on_project_core_type_changed()
        
        # Разделитель
        separator = ttk.Separator(step1_frame, orient='horizontal')
        separator.pack(pady=10, fill='x')
        
        # Вариант 2: Использовать свое ядро
        custom_frame = ttk.Frame(step1_frame)
        custom_frame.pack(pady=10, fill='x')
        
        ttk.Label(custom_frame, text="Использовать свое ядро:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w')
        
        custom_jar_frame = ttk.Frame(custom_frame)
        custom_jar_frame.pack(pady=5, fill='x')
        
        self.custom_jar_path_var = tk.StringVar()
        custom_jar_entry = ttk.Entry(custom_jar_frame, textvariable=self.custom_jar_path_var, width=50)
        custom_jar_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(custom_jar_frame, text="Обзор", 
                  command=self.browse_custom_jar).pack(side='left', padx=5)
        
        # Кнопка Далее
        next_btn = ttk.Button(self.project_window, text="Далее →", 
                             command=self.go_to_step2)
        next_btn.pack(pady=20)
    
    def browse_custom_jar(self):
        """Выбор своего jar-файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл ядра сервера",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if file_path:
            self.custom_jar_path_var.set(file_path)
    
    def on_project_core_type_changed(self, event=None):
        """Обновляет список версий для проекта"""
        core_type = self.project_core_type_var.get()
        if core_type in self.config["available_versions"]:
            versions = self.config["available_versions"][core_type]
            self.project_core_version_combo['values'] = versions
            if versions:
                self.project_core_version_var.set(versions[0])
    
    def go_to_step1(self):
        """Возврат к шагу 1 создания проекта"""
        self.current_step = 1
        self.show_project_creation_step()
    
    def go_to_step2(self):
        """Переход к шагу 2"""
        # Проверяем, выбран ли способ получения ядра
        custom_jar = self.custom_jar_path_var.get()
        core_type = self.project_core_type_var.get()
        version = self.project_core_version_var.get()
        
        if not custom_jar and (not core_type or not version):
            messagebox.showerror("Ошибка", "Выберите способ получения ядра сервера")
            return
        
        if custom_jar and not custom_jar.endswith('.jar'):
            messagebox.showerror("Ошибка", "Выберите корректный .jar файл")
            return
        
        self.current_step = 2
        self.show_project_creation_step()
    
    def show_step2(self):
        """Шаг 2: Настройки проекта"""
        step2_frame = ttk.LabelFrame(self.project_window, text="Шаг 2: Настройки проекта")
        step2_frame.pack(pady=10, fill='x', padx=20)
        
        ttk.Label(step2_frame, text="Название проекта:").pack(pady=5)
        self.project_name_var = tk.StringVar(value=f"Server_{time.strftime('%Y%m%d_%H%M%S')}")
        project_name_entry = ttk.Entry(step2_frame, textvariable=self.project_name_var, width=30)
        project_name_entry.pack(pady=5)
        
        # Выбор пути проекта
        path_frame = ttk.Frame(step2_frame)
        path_frame.pack(pady=10, fill='x')
        
        ttk.Label(path_frame, text="Путь для сохранения:").pack(anchor='w')
        
        path_selection_frame = ttk.Frame(path_frame)
        path_selection_frame.pack(pady=5, fill='x')
        
        self.project_path_var = tk.StringVar(value=self.default_projects_path)
        path_entry = ttk.Entry(path_selection_frame, textvariable=self.project_path_var, width=50)
        path_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(path_selection_frame, text="Обзор", 
                  command=self.browse_project_path).pack(side='left', padx=5)
        
        # Информация о выбранном ядре
        info_frame = ttk.Frame(step2_frame)
        info_frame.pack(pady=10, fill='x')
        
        custom_jar = self.custom_jar_path_var.get()
        if custom_jar:
            core_info = f"Свое ядро: {os.path.basename(custom_jar)}"
        else:
            core_info = f"Ядро: {self.project_core_type_var.get()} {self.project_core_version_var.get()}"
        
        ttk.Label(info_frame, text=core_info, foreground='blue').pack()
        
        # Кнопки Назад и Далее
        btn_frame = ttk.Frame(self.project_window)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="← Назад", 
                  command=self.go_to_step1).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Далее →", 
                  command=self.go_to_step3).pack(side='left', padx=10)
    
    def browse_project_path(self):
        """Выбор пути для проекта"""
        path = filedialog.askdirectory(title="Выберите папку для сервера")
        if path:
            self.project_path_var.set(path)
    
    def go_to_step3(self):
        """Переход к шагу 3"""
        project_name = self.project_name_var.get()
        project_path = self.project_path_var.get()
        
        if not project_name or not project_path:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        self.current_step = 3
        self.show_project_creation_step()
    
    def show_step3(self):
        """Шаг 3: Дополнительные настройки"""
        step3_frame = ttk.LabelFrame(self.project_window, text="Шаг 3: Дополнительные настройки")
        step3_frame.pack(pady=10, fill='x', padx=20)
        
        # Настройки RAM
        ram_frame = ttk.Frame(step3_frame)
        ram_frame.pack(pady=5, fill='x')
        
        ttk.Label(ram_frame, text="Память (RAM):").pack(side='left')
        self.ram_var = tk.StringVar(value=self.config["default_settings"]["default_ram"])
        ram_combo = ttk.Combobox(ram_frame, textvariable=self.ram_var, 
                                values=["1G", "2G", "3G", "4G", "6G", "8G"], width=10)
        ram_combo.pack(side='left', padx=5)
        
        # Порт сервера
        port_frame = ttk.Frame(step3_frame)
        port_frame.pack(pady=5, fill='x')
        
        ttk.Label(port_frame, text="Порт сервера:").pack(side='left')
        self.port_var = tk.StringVar(value=self.config["default_settings"]["server_port"])
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side='left', padx=5)
        
        # Максимальное количество игроков
        players_frame = ttk.Frame(step3_frame)
        players_frame.pack(pady=5, fill='x')
        
        ttk.Label(players_frame, text="Макс. игроков:").pack(side='left')
        self.max_players_var = tk.StringVar(value=self.config["default_settings"]["max_players"])
        players_entry = ttk.Entry(players_frame, textvariable=self.max_players_var, width=10)
        players_entry.pack(side='left', padx=5)
        
        # Сводная информация
        info_frame = ttk.Frame(step3_frame)
        info_frame.pack(pady=10, fill='x')
        
        info_text = f"""
Проект: {self.project_name_var.get()}
Путь: {self.project_path_var.get()}
Ядро: {self.project_core_type_var.get()} {self.project_core_version_var.get() if not self.custom_jar_path_var.get() else 'Custom'}
RAM: {self.ram_var.get()}
Порт: {self.port_var.get()}
        """
        ttk.Label(info_frame, text=info_text.strip(), justify='left').pack()
        
        # Кнопки Назад и Создать
        btn_frame = ttk.Frame(self.project_window)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="← Назад", 
                  command=self.go_to_step2).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Создать проект", 
                  command=self.setup_project).pack(side='left', padx=10)
    
    def setup_project(self):
        """Создает проект сервера"""
        project_name = self.project_name_var.get()
        project_path = self.project_path_var.get()
        custom_jar = self.custom_jar_path_var.get()
        
        if not project_name or not project_path:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        # Создаем папку проекта
        full_project_path = os.path.join(project_path, project_name)
        try:
            if os.path.exists(full_project_path):
                response = messagebox.askyesno(
                    "Подтверждение", 
                    f"Папка '{project_name}' уже существует. Перезаписать?"
                )
                if not response:
                    return
            
            os.makedirs(full_project_path, exist_ok=True)
            
            # Копируем ядро
            new_jar_path = os.path.join(full_project_path, "server.jar")
            
            if custom_jar:
                # Используем свое ядро
                shutil.copy2(custom_jar, new_jar_path)
                core_type = "custom"
                core_version = "custom"
            else:
                # Скачиваем ядро через программу
                core_type = self.project_core_type_var.get()
                core_version = self.project_core_version_var.get()
                self.download_core_for_project(core_type, core_version, new_jar_path)
            
            # Создаем bat файл для запуска с выбранной RAM
            self.create_bat_file(full_project_path, self.ram_var.get())
            
            # Создаем папки
            os.makedirs(os.path.join(full_project_path, "plugins"), exist_ok=True)
            os.makedirs(os.path.join(full_project_path, "world"), exist_ok=True)
            
            # Создаем базовый server.properties с выбранными настройками
            self.create_server_properties(full_project_path, self.port_var.get(), self.max_players_var.get())
            
            # Сохраняем информацию о проекте
            self.projects_data[project_name] = {
                "path": full_project_path,
                "type": core_type,
                "version": core_version,
                "ram": self.ram_var.get(),
                "port": self.port_var.get(),
                "max_players": self.max_players_var.get(),
                "created": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_projects_data()
            
            self.current_project_path = full_project_path
            self.project_info_var.set(f"Проект: {project_name}\nПуть: {full_project_path}")
            
            self.refresh_file_list()
            self.refresh_plugins_list()
            self.refresh_projects_list()
            
            messagebox.showinfo("Успех", f"Проект '{project_name}' успешно создан!")
            self.project_window.destroy()
            
            # Автоматически загружаем созданный проект
            self.load_created_project(project_name)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать проект: {str(e)}")
    
    def download_core_for_project(self, core_type, version, destination_path):
        """Скачивает ядро для проекта"""
        try:
            download_url = self.get_download_url(core_type, version)
            if not download_url:
                raise Exception(f"Не удалось получить URL для {core_type} {version}")
            
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
        except Exception as e:
            raise Exception(f"Ошибка загрузки ядра: {str(e)}")
    
    def create_bat_file(self, project_path, ram):
        bat_content = f"""@echo off
title Minecraft Server
java -Xmx{ram} -Xms{ram} -jar server.jar nogui
pause
"""
        bat_path = os.path.join(project_path, "start_server.bat")
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
    
    def create_server_properties(self, project_path, port, max_players):
        """Создает базовый server.properties"""
        properties_content = f"""#Minecraft Server Properties
#Created by Minecraft Server Manager
max-players={max_players}
server-port={port}
online-mode=true
level-type=default
enable-command-block=true
server-name={os.path.basename(project_path)} Minecraft Server
motd=A Minecraft Server powered by Minecraft Server Manager
"""
        properties_path = os.path.join(project_path, "server.properties")
        with open(properties_path, 'w', encoding='utf-8') as f:
            f.write(properties_content)
    
    def load_created_project(self, project_name):
        """Автоматически загружает созданный проект"""
        for i in range(self.projects_listbox.size()):
            if self.projects_listbox.get(i) == project_name:
                self.projects_listbox.selection_clear(0, 'end')
                self.projects_listbox.selection_set(i)
                self.projects_listbox.see(i)
                self.load_selected_project()
                break
    
    def start_server(self):
        if not self.current_project_path:
            messagebox.showerror("Ошибка", "Сначала создайте или выберите проект")
            return
        
        jar_path = os.path.join(self.current_project_path, "server.jar")
        if not os.path.exists(jar_path):
            messagebox.showerror("Ошибка", "Файл server.jar не найден")
            return
        
        if self.server_running:
            messagebox.showwarning("Предупреждение", "Сервер уже запущен")
            return
        
        try:
            # Используем сохраненные настройки RAM или настройки по умолчанию
            project_name = os.path.basename(self.current_project_path)
            if project_name in self.projects_data and "ram" in self.projects_data[project_name]:
                ram = self.projects_data[project_name]["ram"]
            else:
                ram = self.config["default_settings"]["default_ram"]
            
            # Запускаем сервер
            self.server_process = subprocess.Popen(
                ['java', f'-Xmx{ram}', f'-Xms{ram}', '-jar', 'server.jar', 'nogui'],
                cwd=self.current_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.server_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_var.set("Статус: Сервер запущен")
            
            # Запускаем мониторинг вывода
            threading.Thread(target=self.monitor_server_output, daemon=True).start()
            
            self.log_to_console("=== Сервер запущен ===")
            self.log_to_console("Ожидание инициализации...")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить сервер: {str(e)}")
            self.log_to_console(f"Ошибка запуска: {str(e)}")
    
    def stop_server(self):
        if not self.server_running or not self.server_process:
            return
        
        try:
            self.log_to_console("Останавливаем сервер...")
            self.server_process.stdin.write("stop\n")
            self.server_process.stdin.flush()
        except:
            try:
                self.server_process.terminate()
            except:
                pass
    
    def monitor_server_output(self):
        while self.server_process and self.server_running:
            try:
                output = self.server_process.stdout.readline()
                if output:
                    self.log_to_console(output.strip())
                
                # Проверяем, завершился ли процесс
                if self.server_process.poll() is not None:
                    break
            except:
                break
        
        # Сервер остановлен
        self.server_running = False
        self.server_process = None
        
        self.root.after(0, self.on_server_stopped)
    
    def on_server_stopped(self):
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Статус: Сервер остановлен")
        self.log_to_console("=== Сервер остановлен ===")

def main():
    root = tk.Tk()
    app = MinecraftServerManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()