import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import re
import webbrowser
import json
import subprocess
import sys
import threading
from pathlib import Path


class JavaScriptTerminal:
    """Полноценный JavaScript терминал с выполнением кода"""

    def __init__(self, parent, project_path=None):
        self.parent = parent
        self.project_path = project_path
        self.history = []
        self.history_index = -1
        self.commands = {}
        self.variables = {}
        self.init_js_functions()

    def init_js_functions(self):
        """Инициализация JavaScript функций"""
        self.js_functions = {
            'console.log': self.js_console_log,
            'alert': self.js_alert,
            'prompt': self.js_prompt,
            'confirm': self.js_confirm,
            'document.write': self.js_document_write,
            'setTimeout': self.js_set_timeout,
            'setInterval': self.js_set_interval,
            'clearInterval': self.js_clear_interval,
            'parseInt': lambda x: int(x) if x else 0,
            'parseFloat': lambda x: float(x) if x else 0,
            'String': str,
            'Number': float,
            'Boolean': bool,
            'Array': list,
            'Object': dict,
            'Math': self.js_math,
            'Date': self.js_date,
            'JSON.stringify': json.dumps,
            'JSON.parse': json.loads,
        }

    def js_console_log(self, *args):
        """Вывод в консоль"""
        output = ' '.join(str(arg) for arg in args)
        self.add_output(f">>> {output}\n")
        return output

    def js_alert(self, message):
        """Alert диалог"""
        messagebox.showinfo("JavaScript Alert", str(message))
        return None

    def js_prompt(self, message, default=""):
        """Prompt диалог"""
        return messagebox.askquestion("JavaScript Prompt", str(message))

    def js_confirm(self, message):
        """Confirm диалог"""
        return messagebox.askyesno("JavaScript Confirm", str(message))

    def js_document_write(self, text):
        """Запись в документ (в терминал)"""
        self.add_output(str(text))
        return None

    def js_set_timeout(self, func, ms):
        """setTimeout эмуляция"""

        def delayed():
            self.parent.after(ms, func)

        threading.Thread(target=delayed, daemon=True).start()
        return None

    def js_set_interval(self, func, ms):
        """setInterval эмуляция"""

        def interval():
            while True:
                time.sleep(ms / 1000)
                self.parent.after(0, func)

        threading.Thread(target=interval, daemon=True).start()
        return None

    def js_clear_interval(self, interval_id):
        """Очистка интервала"""
        pass

    def js_math(self, method, *args):
        """Math объект"""
        import random
        math_methods = {
            'abs': abs,
            'ceil': lambda x: int(x) if x >= 0 else int(x) - 1,
            'floor': int,
            'round': round,
            'max': max,
            'min': min,
            'pow': pow,
            'sqrt': lambda x: x ** 0.5,
            'random': lambda: random.random()
        }
        if method in math_methods:
            return math_methods[method](*args) if args else math_methods[method]()
        return None

    def js_date(self):
        """Date объект"""
        from datetime import datetime
        now = datetime.now()
        return {
            'getFullYear': now.year,
            'getMonth': now.month - 1,
            'getDate': now.day,
            'getHours': now.hour,
            'getMinutes': now.minute,
            'getSeconds': now.second,
            'toString': str(now)
        }

    def execute_js(self, code):
        """Выполнение JavaScript кода"""
        try:
            # Создаем безопасную среду выполнения
            exec_globals = {
                '__builtins__': {},
                'console': type('Console', (), {'log': self.js_console_log})(),
                'alert': self.js_alert,
                'prompt': self.js_prompt,
                'confirm': self.js_confirm,
                'document': type('Document', (), {'write': self.js_document_write})(),
                'setTimeout': self.js_set_timeout,
                'setInterval': self.js_set_interval,
                'clearInterval': self.js_clear_interval,
                'Math': type('Math', (), {k: lambda self, *args, m=k: self.js_math(m, *args) for k in
                                          ['abs', 'ceil', 'floor', 'round', 'max', 'min', 'pow', 'sqrt', 'random']})(),
                'Date': self.js_date,
                'JSON': type('JSON', (), {'stringify': staticmethod(json.dumps), 'parse': staticmethod(json.loads)})(),
                'window': self,
                'this': self,
            }

            # Добавляем переменные
            exec_globals.update(self.variables)

            # Выполняем код
            result = eval(code, exec_globals) if not any(
                keyword in code for keyword in ['if', 'for', 'while', 'function', 'var', 'let', 'const']) else exec(
                code, exec_globals)

            if result is not None:
                self.add_output(f"← {result}\n")
                return result

        except Exception as e:
            self.add_output(f"⚠️ Ошибка: {str(e)}\n")
            return None

    def execute_command(self, command):
        """Выполнение команды терминала"""
        command = command.strip()

        if not command:
            return

        # Сохраняем в историю
        self.history.append(command)
        self.history_index = len(self.history)

        # Специальные команды
        if command == 'clear' or command == 'cls':
            self.clear_output()
            return

        if command.startswith('cd '):
            path = command[3:].strip()
            self.change_directory(path)
            return

        if command == 'ls' or command == 'dir':
            self.list_directory()
            return

        if command == 'pwd':
            self.add_output(f"{os.getcwd()}\n")
            return

        if command == 'help':
            self.show_help()
            return

        # Выполняем как JS
        self.execute_js(command)

    def change_directory(self, path):
        """Смена директории"""
        try:
            if os.path.isabs(path):
                os.chdir(path)
            elif self.project_path:
                os.chdir(os.path.join(self.project_path, path))
            else:
                os.chdir(path)
            self.add_output(f"→ {os.getcwd()}\n")
        except Exception as e:
            self.add_output(f"Ошибка: {str(e)}\n")

    def list_directory(self):
        """Список файлов в директории"""
        try:
            files = os.listdir()
            output = "\n".join(f"  {'📁' if os.path.isdir(f) else '📄'} {f}" for f in files)
            self.add_output(f"\n{output}\n\n")
        except Exception as e:
            self.add_output(f"Ошибка: {str(e)}\n")

    def show_help(self):
        """Показать справку"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    JavaScript Терминал - Help                ║
╠══════════════════════════════════════════════════════════════╣
║  Команды терминала:                                          ║
║    clear / cls    - Очистить терминал                        ║
║    cd <path>      - Сменить директорию                       ║
║    ls / dir       - Показать содержимое папки                ║
║    pwd            - Показать текущую папку                   ║
║    help           - Показать эту справку                     ║
╠══════════════════════════════════════════════════════════════╣
║  JavaScript функции:                                         ║
║    console.log(x) - Вывод в консоль                          ║
║    alert(x)       - Показать сообщение                       ║
║    prompt(x)      - Запрос ввода                             ║
║    confirm(x)     - Подтверждение действия                   ║
╠══════════════════════════════════════════════════════════════╣
║  Примеры:                                                    ║
║    console.log("Hello World!")                               ║
║    2 + 2                                                    ║
║    const name = "JS"; console.log(name)                     ║
║    for(let i = 0; i < 5; i++) console.log(i)               ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.add_output(help_text + "\n")

    def create_terminal(self, container):
        """Создание виджета терминала"""
        self.root = container

        # Основной фрейм
        terminal_frame = tk.Frame(container, bg="#0C0C0C")
        terminal_frame.pack(fill="both", expand=True)

        # Верхняя панель
        header = tk.Frame(terminal_frame, bg="#2D2D30", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="💻 JavaScript Terminal", font=("Consolas", 10, "bold"),
                 bg="#2D2D30", fg="#569CD6").pack(side="left", padx=10)

        tk.Label(header, text=f"📁 {self.project_path or 'Нет проекта'}",
                 font=("Consolas", 9), bg="#2D2D30", fg="#888888").pack(side="left", padx=10)

        # Область вывода
        output_frame = tk.Frame(terminal_frame, bg="#0C0C0C")
        output_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.output_text = tk.Text(
            output_frame,
            bg="#0C0C0C",
            fg="#D4D4D4",
            font=("Consolas", 10),
            wrap="word",
            relief="flat",
            borderwidth=0,
            selectbackground="#264F78"
        )

        scroll_y = tk.Scrollbar(output_frame, command=self.output_text.yview, bg="#3E3E42")
        scroll_x = tk.Scrollbar(terminal_frame, command=self.output_text.xview, orient="horizontal", bg="#3E3E42")

        self.output_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.output_text.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        # Строка ввода
        input_frame = tk.Frame(terminal_frame, bg="#1E1E1E", height=30)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        prompt_label = tk.Label(input_frame, text="$>", font=("Consolas", 10, "bold"),
                                bg="#1E1E1E", fg="#569CD6")
        prompt_label.pack(side="left", padx=(10, 5))

        self.input_entry = tk.Entry(
            input_frame,
            bg="#1E1E1E",
            fg="#D4D4D4",
            font=("Consolas", 10),
            relief="flat",
            insertbackground="#D4D4D4"
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.input_entry.bind("<Return>", self.on_enter)
        self.input_entry.bind("<Up>", self.on_up)
        self.input_entry.bind("<Down>", self.on_down)
        # Добавляем поддержку Ctrl+V и Ctrl+C для терминала
        self.input_entry.bind("<Control-v>", self.paste_from_clipboard)
        self.input_entry.bind("<Control-V>", self.paste_from_clipboard)
        self.input_entry.focus()

        # Приветственное сообщение
        welcome = """
╔═══════════════════════════════════════════════════════════════════════╗
║              JavaScript Terminal - Интерактивная среда JS             ║
╠═══════════════════════════════════════════════════════════════════════╣
║  Введите JavaScript код или команды терминала.                       ║
║  Введите 'help' для просмотра всех команд.                           ║
║  Используйте Ctrl+C для копирования, Ctrl+V для вставки              ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
        self.add_output(welcome + "\n")

        return terminal_frame

    def paste_from_clipboard(self, event):
        """Вставка из буфера обмена"""
        try:
            clipboard_text = self.parent.clipboard_get()
            self.input_entry.insert(tk.INSERT, clipboard_text)
        except:
            pass
        return "break"

    def add_output(self, text):
        """Добавление текста в вывод"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def clear_output(self):
        """Очистка вывода"""
        self.output_text.delete(1.0, tk.END)

    def on_enter(self, event):
        """Обработка ввода команды"""
        command = self.input_entry.get()
        self.add_output(f"\n$> {command}\n")
        self.execute_command(command)
        self.input_entry.delete(0, tk.END)
        self.add_output("\n$> ")

    def on_up(self, event):
        """Предыдущая команда из истории"""
        if self.history_index > 0:
            self.history_index -= 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.history[self.history_index])
        return "break"

    def on_down(self, event):
        """Следующая команда из истории"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.history[self.history_index])
        elif self.history_index == len(self.history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, tk.END)
        return "break"


class SyntaxHighlighter:
    """Класс для подсветки синтаксиса"""

    @staticmethod
    def get_language(filename):
        ext = os.path.splitext(filename)[1].lower()
        return {
            '.html': 'html', '.css': 'css', '.js': 'javascript'
        }.get(ext, 'text')

    @staticmethod
    def apply_highlighting(text_widget, filename, content):
        text_widget.delete(1.0, tk.END)
        text_widget.insert(1.0, content)

        colors = {
            'keyword': '#569CD6', 'string': '#CE9178', 'comment': '#6A9955',
            'number': '#B5CEA8', 'function': '#DCDCAA', 'tag': '#569CD6',
            'attribute': '#9CDCFE', 'property': '#9CDCFE'
        }

        for name, color in colors.items():
            text_widget.tag_config(name, foreground=color)

        lang = SyntaxHighlighter.get_language(filename)
        if lang == 'html':
            SyntaxHighlighter._highlight_html(text_widget, content)
        elif lang == 'css':
            SyntaxHighlighter._highlight_css(text_widget, content)
        elif lang == 'javascript':
            SyntaxHighlighter._highlight_javascript(text_widget, content)

    @staticmethod
    def _highlight_html(text_widget, content):
        patterns = [
            (r'<!--.*?-->', 'comment'),
            (r'<[^>]+>', 'tag'),
            (r'"[^"]*"', 'string'),
            (r"'[^']*'", 'string'),
            (r'\b(class|id|href|src|type|rel|style|name|value)\b', 'attribute'),
        ]
        for pattern, tag in patterns:
            start = "1.0"
            while True:
                match = re.search(pattern, text_widget.get(start, tk.END), re.DOTALL)
                if not match:
                    break
                s = f"{start}+{match.start()}c"
                e = f"{start}+{match.end()}c"
                text_widget.tag_add(tag, s, e)
                start = e

    @staticmethod
    def _highlight_css(text_widget, content):
        patterns = [
            (r'/\*.*?\*/', 'comment'),
            (r'"[^"]*"', 'string'),
            (r"'[^']*'", 'string'),
            (r'\b[0-9]+(px|em|rem|%|vh|vw)?\b', 'number'),
            (r'\b(color|background|margin|padding|border|font|display|position|width|height|flex|grid)\b', 'property'),
        ]
        for pattern, tag in patterns:
            start = "1.0"
            while True:
                match = re.search(pattern, text_widget.get(start, tk.END), re.DOTALL)
                if not match:
                    break
                s = f"{start}+{match.start()}c"
                e = f"{start}+{match.end()}c"
                text_widget.tag_add(tag, s, e)
                start = e

    @staticmethod
    def _highlight_javascript(text_widget, content):
        keywords = r'\b(function|var|let|const|if|else|for|while|return|class|extends|import|export|default|new|this|try|catch|throw|switch|case|break|continue|typeof|instanceof|console|log|document|window|alert)\b'
        patterns = [
            (r'//.*?$', 'comment'),
            (r'/\*.*?\*/', 'comment'),
            (r'"[^"]*"', 'string'),
            (r"'[^']*'", 'string'),
            (r'`[^`]*`', 'string'),
            (r'\b[0-9]+(\.[0-9]+)?\b', 'number'),
            (keywords, 'keyword'),
            (r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(', 'function'),
        ]
        for pattern, tag in patterns:
            start = "1.0"
            while True:
                match = re.search(pattern, text_widget.get(start, tk.END), re.MULTILINE | re.DOTALL)
                if not match:
                    break
                s = f"{start}+{match.start()}c"
                e = f"{start}+{match.end()}c"
                text_widget.tag_add(tag, s, e)
                start = e


class CodeEditor:
    """Редактор кода с подсветкой синтаксиса и поддержкой копирования/вставки"""

    ALLOWED_EXTENSIONS = {'.html', '.css', '.js'}

    def __init__(self, parent, file_path=None):
        self.parent = parent
        self.file_path = file_path
        self.is_modified = False
        self.text_widget = None

    def create(self, container):
        main_frame = tk.Frame(container, bg="#1E1E1E")
        main_frame.pack(fill="both", expand=True)

        # Верхняя панель
        info_bar = tk.Frame(main_frame, bg="#2D2D30", height=30)
        info_bar.pack(fill="x")
        info_bar.pack_propagate(False)

        self.file_label = tk.Label(
            info_bar,
            text=os.path.basename(self.file_path) if self.file_path else "Новый файл",
            font=("Segoe UI", 9),
            bg="#2D2D30",
            fg="#CCCCCC",
            anchor="w"
        )
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)

        self.modified_label = tk.Label(
            info_bar,
            text="",
            font=("Segoe UI", 9),
            bg="#2D2D30",
            fg="#CE9178"
        )
        self.modified_label.pack(side="left", padx=5)

        # Текстовое поле
        text_frame = tk.Frame(main_frame, bg="#1E1E1E")
        text_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.text_widget = tk.Text(
            text_frame,
            bg="#1E1E1E",
            fg="#D4D4D4",
            insertbackground="white",
            font=("Consolas", 11),
            wrap="none",
            undo=True,
            maxundo=100,
            selectbackground="#264F78",
            selectforeground="white",
            relief="flat",
            bd=0,
            tabs=("4c",)
        )

        v_scroll = tk.Scrollbar(text_frame, command=self.text_widget.yview, bg="#3E3E42")
        h_scroll = tk.Scrollbar(main_frame, command=self.text_widget.xview, orient="horizontal", bg="#3E3E42")

        self.text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.text_widget.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        # Строка состояния
        status_bar = tk.Frame(main_frame, bg="#007ACC", height=25)
        status_bar.pack(side="bottom", fill="x")
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            status_bar,
            text="Готов к работе | Ctrl+C - копировать, Ctrl+V - вставить",
            bg="#007ACC",
            fg="white",
            anchor="w",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left", padx=10, fill="x", expand=True)

        self.cursor_label = tk.Label(
            status_bar,
            text="Строка: 1, Колонка: 1",
            bg="#007ACC",
            fg="white",
            font=("Segoe UI", 9)
        )
        self.cursor_label.pack(side="right", padx=10)

        # Привязка событий для копирования/вставки
        self.text_widget.bind("<KeyRelease>", self.on_text_change)
        self.text_widget.bind("<ButtonRelease-1>", self.update_cursor)
        self.text_widget.bind("<Control-s>", lambda e: self.save())
        self.text_widget.bind("<Control-f>", lambda e: self.find())
        self.text_widget.bind("<Control-z>", lambda e: self.text_widget.edit_undo())
        self.text_widget.bind("<Control-y>", lambda e: self.text_widget.edit_redo())
        self.text_widget.bind("<Control-a>", lambda e: self.select_all())

        # Горячие клавиши для копирования/вставки
        self.text_widget.bind("<Control-c>", self.copy_to_clipboard)
        self.text_widget.bind("<Control-C>", self.copy_to_clipboard)
        self.text_widget.bind("<Control-v>", self.paste_from_clipboard)
        self.text_widget.bind("<Control-V>", self.paste_from_clipboard)
        self.text_widget.bind("<Control-x>", self.cut_to_clipboard)
        self.text_widget.bind("<Control-X>", self.cut_to_clipboard)

        # Контекстное меню для редактора
        self.context_menu = tk.Menu(self.text_widget, tearoff=0, bg="#2D2D30", fg="white")
        self.context_menu.add_command(label="📋 Копировать", command=self.copy_selection, accelerator="Ctrl+C")
        self.context_menu.add_command(label="📌 Вставить", command=self.paste_text, accelerator="Ctrl+V")
        self.context_menu.add_command(label="✂️ Вырезать", command=self.cut_selection, accelerator="Ctrl+X")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔍 Поиск", command=self.find, accelerator="Ctrl+F")
        self.context_menu.add_command(label="✅ Выделить всё", command=self.select_all, accelerator="Ctrl+A")

        self.text_widget.bind("<Button-3>", self.show_context_menu)

        if self.file_path and os.path.exists(self.file_path):
            self.load()

        return main_frame

    def show_context_menu(self, event):
        """Показать контекстное меню"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def copy_selection(self):
        """Копировать выделенный текст"""
        try:
            selected = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(selected)
            self.status_label.config(text="✓ Скопировано в буфер обмена")
            self.parent.after(2000, lambda: self.status_label.config(
                text="Готов к работе | Ctrl+C - копировать, Ctrl+V - вставить"))
        except:
            pass

    def paste_text(self):
        """Вставить текст из буфера"""
        try:
            text = self.parent.clipboard_get()
            self.text_widget.insert(tk.INSERT, text)
            self.status_label.config(text="✓ Вставлено из буфера обмена")
            self.parent.after(2000, lambda: self.status_label.config(
                text="Готов к работе | Ctrl+C - копировать, Ctrl+V - вставить"))
        except:
            pass

    def cut_selection(self):
        """Вырезать выделенный текст"""
        try:
            selected = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(selected)
            self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.status_label.config(text="✓ Вырезано в буфер обмена")
            self.parent.after(2000, lambda: self.status_label.config(
                text="Готов к работе | Ctrl+C - копировать, Ctrl+V - вставить"))
        except:
            pass

    def copy_to_clipboard(self, event):
        """Копирование в буфер обмена по Ctrl+C"""
        self.copy_selection()
        return "break"

    def paste_from_clipboard(self, event):
        """Вставка из буфера обмена по Ctrl+V"""
        self.paste_text()
        return "break"

    def cut_to_clipboard(self, event):
        """Вырезание в буфер обмена по Ctrl+X"""
        self.cut_selection()
        return "break"

    def on_text_change(self, event=None):
        self.is_modified = True
        self.update_status()
        self.apply_highlighting()

    def update_status(self):
        filename = os.path.basename(self.file_path) if self.file_path else "Новый файл"
        modified = " *" if self.is_modified else ""
        self.file_label.config(text=filename)
        self.modified_label.config(text=modified)

    def update_cursor(self, event=None):
        pos = self.text_widget.index(tk.INSERT)
        line, col = pos.split('.')
        self.cursor_label.config(text=f"Строка: {line}, Колонка: {int(col) + 1}")

    def apply_highlighting(self):
        if not self.file_path:
            return
        content = self.text_widget.get(1.0, tk.END)
        cursor = self.text_widget.index(tk.INSERT)
        SyntaxHighlighter.apply_highlighting(self.text_widget, self.file_path, content)
        try:
            self.text_widget.mark_set(tk.INSERT, cursor)
        except:
            pass

    def load(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(1.0, content)
                self.is_modified = False
                self.update_status()
                self.apply_highlighting()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")

    def save(self):
        if not self.file_path:
            return False
        try:
            content = self.text_widget.get(1.0, tk.END)[:-1]
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.is_modified = False
            self.update_status()
            self.status_label.config(text=f"✓ Сохранено: {os.path.basename(self.file_path)}")
            self.parent.after(2000, lambda: self.status_label.config(
                text="Готов к работе | Ctrl+C - копировать, Ctrl+V - вставить"))
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{e}")
            return False

    def select_all(self):
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        return "break"

    def find(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Поиск")
        dialog.geometry("400x180")
        dialog.configure(bg="#2D2D30")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Найти:", bg="#2D2D30", fg="white", font=("Segoe UI", 10)).pack(pady=15)
        entry = tk.Entry(dialog, width=50, font=("Segoe UI", 10), bg="#3E3E42", fg="white", insertbackground="white")
        entry.pack(pady=5)
        entry.focus()

        def search():
            term = entry.get()
            if term:
                self.text_widget.tag_remove("search", 1.0, tk.END)
                count = 0
                start = "1.0"
                while True:
                    start = self.text_widget.search(term, start, tk.END)
                    if not start:
                        break
                    end = f"{start}+{len(term)}c"
                    self.text_widget.tag_add("search", start, end)
                    count += 1
                    start = end
                self.text_widget.tag_config("search", background="#51516A")
                messagebox.showinfo("Результат", f"Найдено {count} совпадений")

        tk.Button(dialog, text="Найти", command=search, bg="#0E639C", fg="white", cursor="hand2", padx=20, pady=5).pack(
            pady=15)


class ProjectManager:
    """Управление проектами"""

    PROJECTS_FILE = os.path.join(os.path.expanduser("~"), ".incoming_web_projects.json")

    @classmethod
    def load_projects(cls):
        if os.path.exists(cls.PROJECTS_FILE):
            try:
                with open(cls.PROJECTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    @classmethod
    def save_project(cls, project_path, project_name):
        projects = cls.load_projects()
        project_data = {"path": project_path, "name": project_name}
        projects = [p for p in projects if p["path"] != project_path]
        projects.insert(0, project_data)
        projects = projects[:20]
        with open(cls.PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)

    @classmethod
    def remove_project(cls, project_path):
        projects = cls.load_projects()
        projects = [p for p in projects if p["path"] != project_path]
        with open(cls.PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)


class ProjectWindow:
    """Окно проекта с проводником и терминалом"""

    ALLOWED_EXTENSIONS = {'.html', '.css', '.js'}

    def __init__(self, parent, project_path, project_name):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Incoming WEB - {project_name}")
        self.window.geometry("1400x850")
        self.window.minsize(1024, 700)
        self.window.configure(bg="#1E1E1E")

        self.project_path = project_path
        self.project_name = project_name
        self.current_editor = None
        self.terminal = None
        self.file_listbox = None
        self.terminal_frame = None
        self.is_terminal_visible = False

        self.setup_ui()
        self.refresh_file_list()

    def setup_ui(self):
        # Верхняя панель
        toolbar = tk.Frame(self.window, bg="#2D2D30", height=50)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        title = tk.Label(
            toolbar,
            text=f"🎨 {self.project_name}",
            font=("Segoe UI", 13, "bold"),
            bg="#2D2D30",
            fg="white"
        )
        title.pack(side="left", padx=20)

        # Кнопки
        btn_frame = tk.Frame(toolbar, bg="#2D2D30")
        btn_frame.pack(side="right", padx=10)

        buttons = [
            ("📄 Новый", self.new_file),
            ("💾 Сохранить", self.save_current),
            ("🔍 Найти", self.find_text),
            ("🗑 Удалить", self.delete_file),
            ("💻 Терминал", self.toggle_terminal),
            ("🌐 Запустить", self.run_browser),
            ("✕ Выйти", self.close_project)
        ]

        for text, cmd in buttons:
            if text == "💻 Терминал":
                color = "#6A0DAD"
            elif text == "✕ Выйти":
                color = "#C42B1C"
            elif text == "🌐 Запустить":
                color = "#0E639C"
            elif text == "🗑 Удалить":
                color = "#8B0000"
            else:
                color = "#3E3E42"

            btn = tk.Button(
                btn_frame, text=text, command=cmd,
                bg=color, fg="white", font=("Segoe UI", 10),
                relief="flat", cursor="hand2", padx=15, pady=8
            )
            btn.pack(side="left", padx=3)

        # Основная панель
        self.main_pane = tk.PanedWindow(self.window, bg="#252526", sashwidth=5, sashrelief="flat")
        self.main_pane.pack(fill="both", expand=True)

        # Проводник
        explorer = tk.Frame(self.main_pane, bg="#252526")
        self.main_pane.add(explorer, width=280)

        explorer_header = tk.Label(
            explorer, text="📁 ПРОВОДНИК",
            font=("Segoe UI", 10, "bold"),
            bg="#2D2D30", fg="#CCCCCC",
            anchor="w", padx=15, pady=10
        )
        explorer_header.pack(fill="x")

        self.context_menu = tk.Menu(self.window, tearoff=0, bg="#2D2D30", fg="white")
        self.context_menu.add_command(label="📄 Открыть", command=self.open_selected_file)
        self.context_menu.add_command(label="🗑 Удалить", command=self.delete_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Копировать путь", command=self.copy_file_path)

        list_frame = tk.Frame(explorer, bg="#252526")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.file_listbox = tk.Listbox(
            list_frame, bg="#252526", fg="#CCCCCC",
            selectbackground="#094771", selectforeground="white",
            font=("Segoe UI", 10), borderwidth=0, highlightthickness=0
        )
        self.file_listbox.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(list_frame, command=self.file_listbox.yview, bg="#3E3E42")
        scroll.pack(side="right", fill="y")
        self.file_listbox.config(yscrollcommand=scroll.set)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        self.file_listbox.bind("<Button-3>", self.show_context_menu)

        # Контейнер для редактора и терминала
        self.right_container = tk.Frame(self.main_pane, bg="#1E1E1E")
        self.main_pane.add(self.right_container, width=1120)

        # Редактор
        self.editor_container = tk.Frame(self.right_container, bg="#1E1E1E")
        self.editor_container.pack(fill="both", expand=True)

        self.show_welcome()

    def show_context_menu(self, event):
        try:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.file_listbox.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def copy_file_path(self):
        sel = self.file_listbox.curselection()
        if sel:
            item = self.file_listbox.get(sel[0])
            filename = item.split(" ", 1)[1]
            path = os.path.join(self.project_path, filename)
            self.window.clipboard_clear()
            self.window.clipboard_append(path)
            messagebox.showinfo("Скопировано", "Путь к файлу скопирован")

    def open_selected_file(self):
        sel = self.file_listbox.curselection()
        if sel:
            item = self.file_listbox.get(sel[0])
            filename = item.split(" ", 1)[1]
            path = os.path.join(self.project_path, filename)
            if os.path.exists(path):
                self.open_editor(path)

    def toggle_terminal(self):
        """Показать/скрыть терминал"""
        if self.is_terminal_visible:
            if self.terminal_frame:
                self.terminal_frame.destroy()
                self.terminal_frame = None
            self.is_terminal_visible = False
        else:
            if not self.terminal_frame:
                self.terminal_frame = tk.Frame(self.right_container, bg="#0C0C0C", height=300)
                self.terminal_frame.pack(side="bottom", fill="x", before=self.editor_container)
                self.terminal_frame.pack_propagate(False)

                self.terminal = JavaScriptTerminal(self.window, self.project_path)
                self.terminal.create_terminal(self.terminal_frame)
            else:
                self.terminal_frame.pack(side="bottom", fill="x", before=self.editor_container)
            self.is_terminal_visible = True

    def show_welcome(self):
        for w in self.editor_container.winfo_children():
            w.destroy()

        welcome = tk.Frame(self.editor_container, bg="#1E1E1E")
        welcome.pack(expand=True)

        text = """✨ Добро пожаловать в Incoming WEB! ✨

Выберите файл из проводника слева
или создайте новый файл

─────────────────────────────────
Доступные расширения:
─────────────────────────────────
• .html - HTML документы
• .css  - таблицы стилей
• .js   - JavaScript скрипты

─────────────────────────────────
Горячие клавиши:
─────────────────────────────────
Ctrl+S  - Сохранить
Ctrl+F  - Поиск
Ctrl+Z  - Отменить
Ctrl+Y  - Повторить
Ctrl+A  - Выделить всё
Ctrl+C  - Копировать
Ctrl+V  - Вставить
Ctrl+X  - Вырезать

─────────────────────────────────
Терминал:
─────────────────────────────────
• Нажмите "Терминал" для открытия JS консоли
• Выполняйте JavaScript код в реальном времени
• Используйте команды терминала (help для справки)
─────────────────────────────────"""

        tk.Label(welcome, text=text, font=("Segoe UI", 11), bg="#1E1E1E", fg="#808080", justify="center").pack()

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        if os.path.exists(self.project_path):
            icons = {'.html': '🌐', '.css': '🎨', '.js': '⚡'}
            files = [f for f in os.listdir(self.project_path)
                     if os.path.isfile(os.path.join(self.project_path, f))
                     and os.path.splitext(f)[1].lower() in self.ALLOWED_EXTENSIONS]

            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                icon = icons.get(ext, '📄')
                self.file_listbox.insert(tk.END, f"{icon} {f}")

    def on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if sel:
            item = self.file_listbox.get(sel[0])
            filename = item.split(" ", 1)[1]
            path = os.path.join(self.project_path, filename)
            if os.path.exists(path):
                self.open_editor(path)

    def open_editor(self, file_path):
        for w in self.editor_container.winfo_children():
            w.destroy()
        self.current_editor = CodeEditor(self.window, file_path)
        self.current_editor.create(self.editor_container)

    def new_file(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Новый файл")
        dialog.geometry("450x280")
        dialog.configure(bg="#2D2D30")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Создание нового файла", font=("Segoe UI", 12, "bold"),
                 bg="#2D2D30", fg="white").pack(pady=15)

        tk.Label(dialog, text="Имя файла:", bg="#2D2D30", fg="white", font=("Segoe UI", 10)).pack(pady=(10, 0))
        name_entry = tk.Entry(dialog, font=("Segoe UI", 11), width=35, bg="#3E3E42", fg="white",
                              insertbackground="white")
        name_entry.pack(pady=5, padx=20, fill="x")

        tk.Label(dialog, text="Расширение:", bg="#2D2D30", fg="white", font=("Segoe UI", 10)).pack(pady=(10, 0))

        ext_var = tk.StringVar(value=".html")
        ext_frame = tk.Frame(dialog, bg="#2D2D30")
        ext_frame.pack(pady=5)

        extensions = [(".html", "🌐 HTML"), (".css", "🎨 CSS"), (".js", "⚡ JavaScript")]
        for ext, label in extensions:
            tk.Radiobutton(ext_frame, text=label, variable=ext_var, value=ext,
                           bg="#2D2D30", fg="white", selectcolor="#2D2D30",
                           activebackground="#2D2D30", activeforeground="white",
                           font=("Segoe UI", 10)).pack(side="left", padx=15)

        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Внимание", "Введите имя файла!")
                return

            name = os.path.splitext(name)[0]
            ext = ext_var.get()
            filename = f"{name}{ext}"
            path = os.path.join(self.project_path, filename)

            if not os.path.exists(path):
                templates = {
                    '.html': f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>{name}</h1>
    <script src="script.js"></script>
</body>
</html>''',
                    '.css': f'''/* {name}.css */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', sans-serif;
}}''',
                    '.js': f'''// {name}.js
console.log("Файл {name} загружен");

function init() {{
    console.log("Инициализация {name}");
}}

init();'''
                }

                with open(path, 'w', encoding='utf-8') as f:
                    f.write(templates.get(ext, ""))

                self.refresh_file_list()
                self.open_editor(path)
                dialog.destroy()
                messagebox.showinfo("Успех", f"Файл '{filename}' создан!")
            else:
                messagebox.showerror("Ошибка", "Файл уже существует!")

        btn_frame = tk.Frame(dialog, bg="#2D2D30")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="✅ Создать", command=create, bg="#0E639C", fg="white",
                  cursor="hand2", padx=20, pady=5, font=("Segoe UI", 10)).pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Отмена", command=dialog.destroy, bg="#555555", fg="white",
                  cursor="hand2", padx=20, pady=5, font=("Segoe UI", 10)).pack(side="left", padx=10)

    def delete_file(self):
        sel = self.file_listbox.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите файл для удаления!")
            return

        item = self.file_listbox.get(sel[0])
        filename = item.split(" ", 1)[1]

        if messagebox.askyesno("Подтверждение", f"Удалить файл '{filename}'?\nЭто действие нельзя отменить!"):
            path = os.path.join(self.project_path, filename)
            try:
                os.remove(path)
                self.refresh_file_list()
                if self.current_editor and self.current_editor.file_path == path:
                    self.show_welcome()
                    self.current_editor = None
                messagebox.showinfo("Успех", f"Файл '{filename}' удален!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{e}")

    def save_current(self):
        if self.current_editor:
            self.current_editor.save()

    def find_text(self):
        if self.current_editor:
            self.current_editor.find()

    def run_browser(self):
        if self.current_editor and self.current_editor.file_path:
            if self.current_editor.file_path.endswith('.html'):
                webbrowser.open(f"file://{self.current_editor.file_path}")
            else:
                messagebox.showinfo("Информация", "Запустить в браузере можно только HTML файлы")

    def close_project(self):
        if self.current_editor and self.current_editor.is_modified:
            if messagebox.askyesno("Сохранение", "Сохранить изменения?"):
                self.current_editor.save()
        self.window.destroy()


class ModernButton(tk.Button):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 12, "bold"),
            padx=40,
            pady=12,
            **kwargs
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.configure(bg=self['activebackground'] if 'activebackground' in self.keys() else "#1177BB")

    def on_leave(self, e):
        self.configure(bg=self['bg'])


class ProjectsListWindow:
    def __init__(self, parent, on_project_select):
        self.parent = parent
        self.on_project_select = on_project_select
        self.window = tk.Toplevel(parent)
        self.window.title("Мои проекты")
        self.window.geometry("600x500")
        self.window.configure(bg="#2D2D30")
        self.window.resizable(False, False)

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 600) // 2
        y = (self.window.winfo_screenheight() - 500) // 2
        self.window.geometry(f"600x500+{x}+{y}")

        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        header = tk.Frame(self.window, bg="#252526", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📁 Список проектов", font=("Segoe UI", 14, "bold"),
                 bg="#252526", fg="white").pack(side="left", padx=20, pady=10)

        list_frame = tk.Frame(self.window, bg="#2D2D30")
        list_frame.pack(fill="both", expand=True, padx=20, pady=20)

        scroll = tk.Scrollbar(list_frame, bg="#3E3E42")
        scroll.pack(side="right", fill="y")

        self.projects_listbox = tk.Listbox(
            list_frame, bg="#1E1E1E", fg="#CCCCCC",
            selectbackground="#094771", selectforeground="white",
            font=("Segoe UI", 11), borderwidth=0, highlightthickness=0,
            yscrollcommand=scroll.set
        )
        self.projects_listbox.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.projects_listbox.yview)

        self.context_menu = tk.Menu(self.window, tearoff=0, bg="#2D2D30", fg="white")
        self.context_menu.add_command(label="📂 Открыть проект", command=self.open_selected_project)
        self.context_menu.add_command(label="🗑 Удалить из списка", command=self.remove_selected_project)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 Копировать путь", command=self.copy_project_path)

        self.projects_listbox.bind("<Double-Button-1>", lambda e: self.open_selected_project())
        self.projects_listbox.bind("<Button-3>", self.show_context_menu)

        btn_frame = tk.Frame(self.window, bg="#2D2D30")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        tk.Button(btn_frame, text="📂 Открыть выбранный", command=self.open_selected_project,
                  bg="#0E639C", fg="white", font=("Segoe UI", 10), cursor="hand2",
                  padx=20, pady=8, relief="flat").pack(side="left", padx=5)

        tk.Button(btn_frame, text="🗑 Удалить из списка", command=self.remove_selected_project,
                  bg="#8B0000", fg="white", font=("Segoe UI", 10), cursor="hand2",
                  padx=20, pady=8, relief="flat").pack(side="left", padx=5)

        tk.Button(btn_frame, text="✕ Закрыть", command=self.window.destroy,
                  bg="#555555", fg="white", font=("Segoe UI", 10), cursor="hand2",
                  padx=20, pady=8, relief="flat").pack(side="right", padx=5)

    def show_context_menu(self, event):
        try:
            self.projects_listbox.selection_clear(0, tk.END)
            self.projects_listbox.selection_set(self.projects_listbox.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def copy_project_path(self):
        sel = self.projects_listbox.curselection()
        if sel:
            item = self.projects_listbox.get(sel[0])
            path = item.split(" | ")[1] if " | " in item else item.split(" - ")[1]
            self.window.clipboard_clear()
            self.window.clipboard_append(path)
            messagebox.showinfo("Скопировано", "Путь к проекту скопирован")

    def load_projects(self):
        self.projects_listbox.delete(0, tk.END)
        projects = ProjectManager.load_projects()

        if not projects:
            self.projects_listbox.insert(tk.END, "✨ Нет сохраненных проектов")
            self.projects_listbox.insert(tk.END, "Создайте проект чтобы он появился здесь")
        else:
            for p in projects:
                if os.path.exists(p["path"]):
                    display = f"📁 {p['name']} | {p['path']}"
                    self.projects_listbox.insert(tk.END, display)
                else:
                    display = f"⚠️ {p['name']} | {p['path']} (папка не найдена)"
                    self.projects_listbox.insert(tk.END, display)

    def open_selected_project(self):
        sel = self.projects_listbox.curselection()
        if sel:
            item = self.projects_listbox.get(sel[0])
            if "✨" in item or not item.strip():
                return

            path = item.split(" | ")[1] if " | " in item else item.split(" - ")[1]
            path = path.split(" (папка")[0] if " (папка" in path else path

            if os.path.exists(path):
                project_name = os.path.basename(path)
                self.window.destroy()
                self.on_project_select(path, project_name)
            else:
                messagebox.showerror("Ошибка", "Папка проекта не найдена!")

    def remove_selected_project(self):
        sel = self.projects_listbox.curselection()
        if sel:
            item = self.projects_listbox.get(sel[0])
            if "✨" in item or not item.strip():
                return

            path = item.split(" | ")[1] if " | " in item else item.split(" - ")[1]
            path = path.split(" (папка")[0] if " (папка" in path else path

            if messagebox.askyesno("Подтверждение", "Удалить проект из списка?\n(Файлы проекта останутся на диске)"):
                ProjectManager.remove_project(path)
                self.load_projects()
                messagebox.showinfo("Успех", "Проект удален из списка!")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Incoming WEB - Creative Studio")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)
        self.root.configure(bg="#1E1E1E")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1200) // 2
        y = (self.root.winfo_screenheight() - 750) // 2
        self.root.geometry(f"1200x750+{x}+{y}")

        self.show_main()

    def show_main(self):
        for w in self.root.winfo_children():
            w.destroy()

        main_frame = tk.Frame(self.root, bg="#1E1E1E")
        main_frame.pack(expand=True)

        title = tk.Label(
            main_frame,
            text="🎨 Incoming WEB\nCreative Studio",
            font=("Segoe UI", 42, "bold"),
            bg="#1E1E1E",
            fg="white",
            justify="center"
        )
        title.pack(pady=(80, 20))

        subtitle = tk.Label(
            main_frame,
            text="Создавайте веб-проекты с легкостью",
            font=("Segoe UI", 14),
            bg="#1E1E1E",
            fg="#888888"
        )
        subtitle.pack(pady=(0, 50))

        btn_frame = tk.Frame(main_frame, bg="#1E1E1E")
        btn_frame.pack(pady=30)

        create_btn = ModernButton(
            btn_frame,
            text="✨ Создать проект",
            bg="#0E639C",
            fg="white",
            activebackground="#1177BB",
            command=self.create_project
        )
        create_btn.pack(side="left", padx=15)

        open_btn = ModernButton(
            btn_frame,
            text="📂 Открыть проекты",
            bg="#6A0DAD",
            fg="white",
            activebackground="#7B1FA2",
            command=self.open_projects_list
        )
        open_btn.pack(side="left", padx=15)

        info_card = tk.Frame(main_frame, bg="#2D2D30", relief="flat", bd=1)
        info_card.pack(pady=40, padx=30, fill="x")

        info_text = """💡 Быстрый старт:

• Нажмите «Создать проект» для создания нового проекта
• Нажмите «Открыть проекты» чтобы увидеть список всех ваших проектов
• Создавайте файлы только с расширениями .html, .css, .js
• Нажмите «Терминал» для открытия JavaScript консоли
• Выполняйте JS код в реальном времени прямо в терминале
• Используйте Ctrl+C, Ctrl+V, Ctrl+X для работы с текстом
• Удаляйте ненужные файлы через кнопку «Удалить» или контекстное меню
• Запускайте HTML в браузере одной кнопкой"""

        info_label = tk.Label(
            info_card,
            text=info_text,
            font=("Segoe UI", 10),
            bg="#2D2D30",
            fg="#CCCCCC",
            justify="left",
            padx=30,
            pady=20
        )
        info_label.pack()

    def open_projects_list(self):
        ProjectsListWindow(self.root, self.open_project)

    def open_project(self, project_path, project_name):
        ProjectWindow(self.root, project_path, project_name)

    def create_project(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание проекта")
        dialog.geometry("550x400")
        dialog.configure(bg="#2D2D30")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 550) // 2
        y = (dialog.winfo_screenheight() - 400) // 2
        dialog.geometry(f"550x400+{x}+{y}")

        tk.Label(dialog, text="Создание нового проекта", font=("Segoe UI", 14, "bold"),
                 bg="#2D2D30", fg="white").pack(pady=20)

        tk.Label(dialog, text="Название проекта:", bg="#2D2D30", fg="#CCCCCC",
                 font=("Segoe UI", 11), anchor="w").pack(padx=40, pady=(20, 5), fill="x")
        name_entry = tk.Entry(dialog, font=("Segoe UI", 11), bg="#3E3E42", fg="white",
                              insertbackground="white", relief="flat")
        name_entry.pack(padx=40, pady=(0, 15), fill="x", ipady=8)
        name_entry.insert(0, "Мой первый проект")

        tk.Label(dialog, text="Путь сохранения:", bg="#2D2D30", fg="#CCCCCC",
                 font=("Segoe UI", 11), anchor="w").pack(padx=40, pady=(10, 5), fill="x")

        path_frame = tk.Frame(dialog, bg="#2D2D30")
        path_frame.pack(padx=40, pady=(0, 20), fill="x")

        path_entry = tk.Entry(path_frame, font=("Segoe UI", 11), bg="#3E3E42", fg="white",
                              insertbackground="white", relief="flat")
        path_entry.pack(side="left", fill="x", expand=True, ipady=8)
        default_path = os.path.join(os.path.expanduser("~"), "Desktop")
        path_entry.insert(0, default_path)

        def browse():
            folder = filedialog.askdirectory(title="Выберите папку для проекта")
            if folder:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, folder)

        tk.Button(path_frame, text="📁 Обзор", command=browse, bg="#555555", fg="white",
                  cursor="hand2", padx=15, relief="flat").pack(side="right", padx=(10, 0))

        def create():
            name = name_entry.get().strip()
            path = path_entry.get().strip()

            if not name:
                messagebox.showwarning("Внимание", "Введите название проекта!")
                return

            name = re.sub(r'[<>:"/\\|?*]', '_', name)
            full_path = os.path.join(path, name)

            try:
                if not os.path.exists(full_path):
                    os.makedirs(full_path)

                    files = {
                        "index.html": f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>✨ {name}</h1>
        <p>Добро пожаловать в ваш новый проект!</p>
        <button onclick="showMessage()">Нажми меня</button>
    </div>
    <script src="script.js"></script>
</body>
</html>''',
                        "style.css": """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    background: white;
    border-radius: 20px;
    padding: 50px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    text-align: center;
    animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

h1 {
    color: #333;
    margin-bottom: 20px;
    font-size: 2.5em;
}

p {
    color: #666;
    margin-bottom: 30px;
    line-height: 1.6;
}

button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 25px;
    font-size: 16px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

button:hover {
    transform: scale(1.05);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}""",
                        "script.js": f"""// {name} - JavaScript код
function showMessage() {{
    alert("Привет из {name}!");
    console.log("Кнопка была нажата");
}}

console.log("Проект {name} успешно загружен!");"""
                    }

                    for filename, content in files.items():
                        with open(os.path.join(full_path, filename), 'w', encoding='utf-8') as f:
                            f.write(content)

                    ProjectManager.save_project(full_path, name)

                    messagebox.showinfo("Успех", f"Проект '{name}' успешно создан!")
                    dialog.destroy()

                    ProjectWindow(self.root, full_path, name)
                else:
                    messagebox.showerror("Ошибка", "Папка с таким именем уже существует!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать проект:\n{e}")

        btn_frame = tk.Frame(dialog, bg="#2D2D30")
        btn_frame.pack(pady=30)

        tk.Button(btn_frame, text="✅ Создать", command=create, bg="#0E639C", fg="white",
                  font=("Segoe UI", 11), cursor="hand2", padx=30, pady=8, relief="flat").pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Отмена", command=dialog.destroy, bg="#555555", fg="white",
                  font=("Segoe UI", 11), cursor="hand2", padx=30, pady=8, relief="flat").pack(side="left", padx=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()