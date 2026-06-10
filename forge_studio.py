import ast
import io
import math
import os
import queue
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk


APP_NAME = "Forge Studio"
APP_VERSION = "1.5"

PY_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
}

SNIPPETS = {
    "Starter Script": 'def main():\n    print("Hello from Forge Studio")\n\n\nif __name__ == "__main__":\n    main()\n',
    "Calculator": 'def add(a, b):\n    return a + b\n\n\ndef subtract(a, b):\n    return a - b\n\n\nprint("2 + 3 =", add(2, 3))\nprint("10 - 4 =", subtract(10, 4))\n',
    "Text Adventure": 'name = input("Hero name: ")\nprint(f"{name} enters the old terminal room.")\nchoice = input("Open the glowing door? yes/no: ").lower()\n\nif choice == "yes":\n    print("You found a hidden compiler core.")\nelse:\n    print("You live to debug another day.")\n',
    "Tkinter App": 'import tkinter as tk\n\nroot = tk.Tk()\nroot.title("My App")\nroot.geometry("360x220")\n\nlabel = tk.Label(root, text="Built in Forge Studio", font=("Segoe UI", 16, "bold"))\nlabel.pack(expand=True)\n\nroot.mainloop()\n',
    "2D Game Preview": 'player = {"x": 360, "y": 230, "speed": 260}\ncoins = [{"x": 120, "y": 120}, {"x": 540, "y": 330}, {"x": 690, "y": 150}]\nscore = 0\n\n\ndef update(dt):\n    global score\n    if key("Left") or key("a"):\n        player["x"] -= player["speed"] * dt\n    if key("Right") or key("d"):\n        player["x"] += player["speed"] * dt\n    if key("Up") or key("w"):\n        player["y"] -= player["speed"] * dt\n    if key("Down") or key("s"):\n        player["y"] += player["speed"] * dt\n\n    player["x"] = max(20, min(width() - 20, player["x"]))\n    player["y"] = max(20, min(height() - 20, player["y"]))\n\n    for coin in coins[:]:\n        if distance(player["x"], player["y"], coin["x"], coin["y"]) < 34:\n            coins.remove(coin)\n            score += 1\n\n\ndef draw():\n    clear(\"#091018\")\n    text(20, 22, \"2D Preview: move with WASD or arrow keys\", color=\"#dff8ff\", size=14)\n    text(20, 48, f\"Score: {score}\", color=\"#7dff9b\", size=16)\n\n    for coin in coins:\n        circle(coin["x"], coin["y"], 13, fill=\"#ffd166\", outline=\"#fff3b0\")\n\n    circle(player["x"], player["y"], 20, fill=\"#27c7d8\", outline=\"#b8fbff\")\n',
    "3D Game Preview": 'angle = 0\n\n\ndef update(dt):\n    global angle\n    angle += dt\n\n\ndef draw():\n    clear(\"#080b12\")\n    text(20, 24, \"3D Studio Viewport\", color=\"#dff8ff\", size=14)\n    text(20, 50, \"Mouse: rotate/pan/zoom | WASD + Q/E: fly camera\", color=\"#7dff9b\", size=11)\n    grid3d(size=10, step=1, color=\"#26384a\")\n    cube3d(-2.2, 0, 3.5, 1.4, color=\"#27c7d8\", yaw=angle)\n    cube3d(1.9, .2, 5.2, 1.2, color=\"#78e08f\", yaw=-angle * 1.4)\n    cube3d(0, -1.1, 4.2, .9, color=\"#ffc766\", yaw=angle * .8)\n    cube3d(0, 1.2, 7.0, 1.1, color=\"#ff6b6b\", yaw=angle * 1.7)\n',
}

THEMES = {
    "Forge": {
        "bg": "#0f131a",
        "panel": "#171c24",
        "panel2": "#202734",
        "text": "#eef4f8",
        "muted": "#9ba9b7",
        "accent": "#27c7d8",
        "accent2": "#78e08f",
        "warn": "#ffc766",
        "danger": "#ff6b6b",
        "editor_bg": "#0b0f14",
        "editor_fg": "#edf3f7",
        "select": "#28495c",
        "keyword": "#66d9ef",
        "string": "#9fe870",
        "comment": "#718093",
        "number": "#ffc766",
    },
    "Neon": {
        "bg": "#07080d",
        "panel": "#10111c",
        "panel2": "#1b1d2f",
        "text": "#f8fbff",
        "muted": "#aab1c7",
        "accent": "#00f5d4",
        "accent2": "#fee440",
        "warn": "#ffb703",
        "danger": "#ff4d6d",
        "editor_bg": "#05060a",
        "editor_fg": "#f6f7fb",
        "select": "#362d63",
        "keyword": "#00bbf9",
        "string": "#80ff72",
        "comment": "#7b819c",
        "number": "#fee440",
    },
    "Calm": {
        "bg": "#101417",
        "panel": "#1a2125",
        "panel2": "#263138",
        "text": "#f4f8f7",
        "muted": "#a8b6b2",
        "accent": "#7dd3c7",
        "accent2": "#f2c078",
        "warn": "#f2c078",
        "danger": "#ef767a",
        "editor_bg": "#0d1113",
        "editor_fg": "#f4f8f7",
        "select": "#33484b",
        "keyword": "#7dd3c7",
        "string": "#c3e88d",
        "comment": "#81908c",
        "number": "#f2c078",
    },
}


def resource_path(name: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / name
    return Path(__file__).with_name(name)


class GamePreviewAPI:
    def __init__(self, canvas: tk.Canvas, keys: set[str], camera: dict[str, float]):
        self.canvas = canvas
        self.keys = keys
        self.camera = camera

    def width(self) -> int:
        return max(1, self.canvas.winfo_width())

    def height(self) -> int:
        return max(1, self.canvas.winfo_height())

    def key(self, name: str) -> bool:
        return name.lower() in self.keys

    def clear(self, color: str = "#080b12") -> None:
        self.canvas.delete("all")
        self.canvas.configure(bg=color)

    def rect(self, x: float, y: float, w: float, h: float, fill: str = "#27c7d8", outline: str = "") -> None:
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline)

    def circle(self, x: float, y: float, radius: float, fill: str = "#27c7d8", outline: str = "") -> None:
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=outline)

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str = "#eef4f8", width: int = 2) -> None:
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

    def text(self, x: float, y: float, value: object, color: str = "#eef4f8", size: int = 12) -> None:
        self.canvas.create_text(x, y, text=str(value), fill=color, anchor="nw", font=("Segoe UI", size, "bold"))

    def distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        return math.hypot(x2 - x1, y2 - y1)

    def set_camera(self, x: float = 0, y: float = 0, z: float = -7, yaw: float = 0, pitch: float = 0) -> None:
        self.camera.update({"x": x, "y": y, "z": z, "yaw": yaw, "pitch": pitch})

    def move_camera(self, dx: float = 0, dy: float = 0, dz: float = 0, dyaw: float = 0, dpitch: float = 0) -> None:
        self.camera["x"] += dx
        self.camera["y"] += dy
        self.camera["z"] += dz
        self.camera["yaw"] += dyaw
        self.camera["pitch"] = max(-1.2, min(1.2, self.camera["pitch"] + dpitch))

    def _project(self, x: float, y: float, z: float, yaw: float = 0) -> tuple[float, float] | None:
        x -= self.camera["x"]
        y -= self.camera["y"]
        z -= self.camera["z"]

        cos_y = math.cos(self.camera["yaw"])
        sin_y = math.sin(self.camera["yaw"])
        x, z = x * cos_y - z * sin_y, x * sin_y + z * cos_y

        cos_p = math.cos(self.camera["pitch"])
        sin_p = math.sin(self.camera["pitch"])
        y, z = y * cos_p - z * sin_p, y * sin_p + z * cos_p

        if yaw:
            cos_o = math.cos(yaw)
            sin_o = math.sin(yaw)
            x, z = x * cos_o - z * sin_o, x * sin_o + z * cos_o

        if z <= 0.15:
            return None
        focal = min(self.width(), self.height()) * 0.85
        return (self.width() / 2 + x * focal / z, self.height() / 2 - y * focal / z)

    def cube3d(self, x: float, y: float, z: float, size: float = 1, color: str = "#27c7d8", yaw: float = 0) -> None:
        half = size / 2
        points = [
            (-half, -half, -half), (half, -half, -half), (half, half, -half), (-half, half, -half),
            (-half, -half, half), (half, -half, half), (half, half, half), (-half, half, half),
        ]
        rotated = []
        for px, py, pz in points:
            cos_o = math.cos(yaw)
            sin_o = math.sin(yaw)
            rx = px * cos_o - pz * sin_o
            rz = px * sin_o + pz * cos_o
            rotated.append(self._project(x + rx, y + py, z + rz))
        edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
        for start, end in edges:
            p1 = rotated[start]
            p2 = rotated[end]
            if p1 and p2:
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=3)

    def grid3d(self, size: int = 8, step: int = 1, color: str = "#26384a") -> None:
        for i in range(-size, size + 1, step):
            a = self._project(i, -1.8, 1)
            b = self._project(i, -1.8, size * 1.5)
            c = self._project(-size, -1.8, i + size)
            d = self._project(size, -1.8, i + size)
            if a and b:
                self.canvas.create_line(a[0], a[1], b[0], b[1], fill=color)
            if c and d:
                self.canvas.create_line(c[0], c[1], d[0], d[1], fill=color)


class ForgeStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1320x820")
        self.minsize(1000, 660)

        icon = resource_path("forge_studio_icon.ico")
        if icon.exists():
            try:
                self.iconbitmap(default=str(icon))
            except tk.TclError:
                pass

        self.current_theme_name = "Forge"
        self.theme = THEMES[self.current_theme_name]
        self.project_dir = Path.cwd()
        self.current_file: Path | None = None
        self.dirty = False
        self.runner: subprocess.Popen | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.focus_mode = False
        self.teach_mode = True
        self.preview_running = False
        self.preview_namespace: dict | None = None
        self.preview_last_time = 0.0
        self.preview_keys: set[str] = set()
        self.preview_camera = {"x": 0.0, "y": 0.0, "z": -7.0, "yaw": 0.0, "pitch": 0.0}
        self.preview_mouse = {"x": 0, "y": 0, "button": ""}

        self._setup_style()
        self._build_menu()
        self._build_layout()
        self._bind_events()
        self._load_project_tree()
        self._open_startup_target()
        self.after(200, self._draw_empty_viewport)
        self._poll_output()

    def _open_startup_target(self) -> None:
        if len(sys.argv) > 1:
            target = Path(sys.argv[1])
            if target.is_file():
                self._load_file(target)
                return
            if target.is_dir():
                self.project_dir = target
                self._load_project_tree()
                self._new_file()
                return
        self._new_file()

    def _setup_style(self) -> None:
        self.configure(bg=self.theme["bg"])
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.theme["bg"])
        style.configure("Panel.TFrame", background=self.theme["panel"])
        style.configure("Toolbar.TFrame", background=self.theme["panel2"])
        style.configure("TLabel", background=self.theme["bg"], foreground=self.theme["text"])
        style.configure("Panel.TLabel", background=self.theme["panel"], foreground=self.theme["text"])
        style.configure("Muted.TLabel", background=self.theme["panel"], foreground=self.theme["muted"])
        style.configure("Toolbar.TLabel", background=self.theme["panel2"], foreground=self.theme["text"])
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Accent.TButton", background=self.theme["accent"], foreground="#071014")
        style.configure("Danger.TButton", background=self.theme["danger"], foreground="#fffafa")
        style.configure("Treeview", background=self.theme["panel"], fieldbackground=self.theme["panel"], foreground=self.theme["text"], rowheight=27)
        style.configure("Treeview.Heading", background=self.theme["panel2"], foreground=self.theme["text"])
        style.map("Treeview", background=[("selected", self.theme["select"])])

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New File", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open File", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Folder", command=self._open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        run_menu = tk.Menu(menubar, tearoff=False)
        run_menu.add_command(label="Run Code", command=self._run_code, accelerator="F5")
        run_menu.add_command(label="Stop Code", command=self._stop_code)
        run_menu.add_command(label="Play Game Preview", command=self._start_game_preview, accelerator="F6")
        run_menu.add_command(label="Stop Game Preview", command=self._stop_game_preview)
        run_menu.add_command(label="Check Syntax", command=self._check_syntax, accelerator="Ctrl+Shift+B")
        menubar.add_cascade(label="Run", menu=run_menu)

        insert_menu = tk.Menu(menubar, tearoff=False)
        for name in SNIPPETS:
            insert_menu.add_command(label=name, command=lambda item=name: self._insert_snippet(item))
        menubar.add_cascade(label="Templates", menu=insert_menu)

        mode_menu = tk.Menu(menubar, tearoff=False)
        mode_menu.add_command(label="Forge Theme", command=lambda: self._apply_theme("Forge"))
        mode_menu.add_command(label="Neon Theme", command=lambda: self._apply_theme("Neon"))
        mode_menu.add_command(label="Calm Theme", command=lambda: self._apply_theme("Calm"))
        mode_menu.add_separator()
        mode_menu.add_command(label="Focus Mode", command=self._toggle_focus)
        mode_menu.add_command(label="Teach Mode", command=self._toggle_teach)
        menubar.add_cascade(label="Modes", menu=mode_menu)

    def _build_layout(self) -> None:
        self.toolbar = ttk.Frame(self, style="Toolbar.TFrame", padding=(12, 10))
        self.toolbar.pack(fill="x")

        ttk.Label(self.toolbar, text=APP_NAME, style="Toolbar.TLabel", font=("Segoe UI", 15, "bold")).pack(side="left", padx=(0, 16))
        ttk.Button(self.toolbar, text="New", command=self._new_file).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Open", command=self._open_file).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Folder", command=self._open_folder).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Save", command=self._save_file).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Run", style="Accent.TButton", command=self._run_code).pack(side="left", padx=(14, 3))
        ttk.Button(self.toolbar, text="Play Preview", style="Accent.TButton", command=self._start_game_preview).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Stop", style="Danger.TButton", command=self._stop_code).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Stop Preview", style="Danger.TButton", command=self._stop_game_preview).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Check", command=self._check_syntax).pack(side="left", padx=3)
        ttk.Button(self.toolbar, text="Focus", command=self._toggle_focus).pack(side="right", padx=3)
        ttk.Button(self.toolbar, text="Neon", command=lambda: self._apply_theme("Neon")).pack(side="right", padx=3)
        ttk.Button(self.toolbar, text="Forge", command=lambda: self._apply_theme("Forge")).pack(side="right", padx=3)
        ttk.Label(self.toolbar, text=f"v{APP_VERSION}", style="Toolbar.TLabel", font=("Segoe UI", 10, "bold")).pack(side="right", padx=(8, 12))

        self.main = ttk.PanedWindow(self, orient="horizontal")
        self.main.pack(fill="both", expand=True)

        self.sidebar = ttk.Frame(self.main, style="Panel.TFrame", padding=10)
        self.main.add(self.sidebar, weight=1)
        ttk.Label(self.sidebar, text="Project", style="Panel.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.project_label = ttk.Label(self.sidebar, text="", style="Muted.TLabel", wraplength=220)
        self.project_label.pack(anchor="w", pady=(4, 8))
        tree_frame = ttk.Frame(self.sidebar, style="Panel.TFrame")
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        ttk.Button(self.sidebar, text="New Python File", command=self._new_project_file).pack(fill="x", pady=(10, 0))

        self.editor_pane = ttk.PanedWindow(self.main, orient="vertical")
        self.main.add(self.editor_pane, weight=5)

        self.preview_panel = ttk.Frame(self.main, style="Panel.TFrame", padding=10)
        self.main.add(self.preview_panel, weight=2)
        self.preview_panel.rowconfigure(2, weight=1)
        self.preview_panel.columnconfigure(0, weight=1)
        ttk.Label(self.preview_panel, text="Game Preview", style="Panel.TLabel", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        preview_tools = ttk.Frame(self.preview_panel, style="Panel.TFrame")
        preview_tools.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        ttk.Button(preview_tools, text="Play", style="Accent.TButton", command=self._start_game_preview).pack(side="left", padx=(0, 5))
        ttk.Button(preview_tools, text="Stop", style="Danger.TButton", command=self._stop_game_preview).pack(side="left", padx=5)
        ttk.Button(preview_tools, text="Reset Cam", command=self._reset_preview_camera).pack(side="left", padx=5)
        ttk.Button(preview_tools, text="2D", command=lambda: self._replace_with_snippet("2D Game Preview")).pack(side="left", padx=5)
        ttk.Button(preview_tools, text="3D", command=lambda: self._replace_with_snippet("3D Game Preview")).pack(side="left", padx=5)
        self.preview_canvas = tk.Canvas(self.preview_panel, bg="#080b12", highlightthickness=0)
        self.preview_canvas.grid(row=2, column=0, sticky="nsew")
        self.preview_status = ttk.Label(
            self.preview_panel,
            text="3D viewport: left-drag rotates, right-drag pans, wheel zooms, WASD moves while playing.",
            style="Muted.TLabel",
            wraplength=300,
        )
        self.preview_status.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        editor_shell = ttk.Frame(self.editor_pane, style="Panel.TFrame", padding=(10, 10, 10, 0))
        self.editor_pane.add(editor_shell, weight=4)
        self.file_title = ttk.Label(editor_shell, text="Untitled", style="Panel.TLabel", font=("Segoe UI", 12, "bold"))
        self.file_title.pack(anchor="w", pady=(0, 8))

        text_frame = tk.Frame(editor_shell, bg=self.theme["panel"])
        text_frame.pack(fill="both", expand=True)
        self.line_numbers = tk.Text(text_frame, width=5, padx=6, pady=8, takefocus=0, border=0, state="disabled", font=("Consolas", 11))
        self.line_numbers.pack(side="left", fill="y")
        self.editor = tk.Text(text_frame, undo=True, wrap="none", padx=12, pady=8, border=0, insertwidth=2, font=("Consolas", 12))
        self.editor.pack(side="left", fill="both", expand=True)
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self._scroll_editor)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(editor_shell, orient="horizontal", command=self.editor.xview)
        x_scroll.pack(fill="x")
        self.editor.configure(yscrollcommand=lambda first, last: self._on_editor_scroll(first, last, y_scroll), xscrollcommand=x_scroll.set)

        bottom = ttk.Frame(self.editor_pane, style="Panel.TFrame", padding=10)
        self.editor_pane.add(bottom, weight=1)
        bottom.columnconfigure(0, weight=2)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(1, weight=1)
        ttk.Label(bottom, text="Output", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(bottom, text="Assistant Hints", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.output = tk.Text(bottom, height=8, wrap="word", border=0, padx=10, pady=8, font=("Consolas", 10), state="disabled")
        self.output.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.hints = tk.Text(bottom, height=8, wrap="word", border=0, padx=10, pady=8, font=("Segoe UI", 10), state="disabled")
        self.hints.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(6, 0))

        self.status = ttk.Label(self, text="", anchor="w", padding=(10, 5))
        self.status.pack(fill="x")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_text_colors()

    def _bind_events(self) -> None:
        self.bind("<Control-n>", lambda _event: self._new_file())
        self.bind("<Control-o>", lambda _event: self._open_file())
        self.bind("<Control-s>", lambda _event: self._save_file())
        self.bind("<F5>", lambda _event: self._run_code())
        self.bind("<F6>", lambda _event: self._start_game_preview())
        self.bind("<Control-Shift-B>", lambda _event: self._check_syntax())
        self.bind("<KeyPress>", self._preview_key_down)
        self.bind("<KeyRelease>", self._preview_key_up)
        self.preview_canvas.bind("<ButtonPress-1>", lambda event: self._preview_mouse_down(event, "rotate"))
        self.preview_canvas.bind("<ButtonPress-2>", lambda event: self._preview_mouse_down(event, "pan"))
        self.preview_canvas.bind("<ButtonPress-3>", lambda event: self._preview_mouse_down(event, "pan"))
        self.preview_canvas.bind("<B1-Motion>", self._preview_mouse_drag)
        self.preview_canvas.bind("<B2-Motion>", self._preview_mouse_drag)
        self.preview_canvas.bind("<B3-Motion>", self._preview_mouse_drag)
        self.preview_canvas.bind("<MouseWheel>", self._preview_mouse_wheel)
        self.preview_canvas.bind("<Button-4>", lambda event: self._preview_zoom(-1))
        self.preview_canvas.bind("<Button-5>", lambda event: self._preview_zoom(1))
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<KeyRelease>", lambda _event: self._after_edit())
        self.editor.bind("<ButtonRelease>", lambda _event: self._update_status())
        self.tree.bind("<Double-1>", self._open_tree_selection)

    def _apply_text_colors(self) -> None:
        self.editor.configure(
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["accent"],
            selectbackground=self.theme["select"],
        )
        self.output.configure(bg="#070a0f", fg=self.theme["text"], insertbackground=self.theme["accent"])
        self.hints.configure(bg=self.theme["panel2"], fg=self.theme["text"], insertbackground=self.theme["accent"])
        self.line_numbers.configure(bg=self.theme["panel2"], fg=self.theme["muted"])
        self.preview_canvas.configure(bg="#080b12")
        self.editor.tag_configure("keyword", foreground=self.theme["keyword"])
        self.editor.tag_configure("string", foreground=self.theme["string"])
        self.editor.tag_configure("comment", foreground=self.theme["comment"])
        self.editor.tag_configure("number", foreground=self.theme["number"])
        self.editor.tag_configure("error", background="#4a1f27", foreground="#ffd6dc")

    def _apply_theme(self, name: str) -> None:
        self.current_theme_name = name
        self.theme = THEMES[name]
        self._setup_style()
        self._apply_text_colors()
        self._highlight_syntax()
        self._write_hint(f"{name} mode is active.")

    def _new_file(self) -> None:
        if not self._confirm_discard():
            return
        self.current_file = None
        self._set_editor_text(SNIPPETS["Starter Script"])
        self.dirty = False
        self._refresh_title()
        self._write_hint("Start coding, then press Run. Save when you want the file to live in your project.")

    def _open_file(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self._load_file(Path(path))

    def _open_folder(self) -> None:
        chosen = filedialog.askdirectory(initialdir=str(self.project_dir))
        if chosen:
            self.project_dir = Path(chosen)
            self._load_project_tree()
            self._write_hint(f"Project folder loaded: {self.project_dir}")

    def _load_file(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            messagebox.showerror("Could not open file", str(error))
            return
        self.current_file = path
        self.project_dir = path.parent
        self._set_editor_text(text)
        self.dirty = False
        self._refresh_title()
        self._load_project_tree()

    def _save_file(self) -> bool:
        if self.current_file is None:
            return self._save_as()
        try:
            self.current_file.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Could not save file", str(error))
            return False
        self.dirty = False
        self._refresh_title()
        self._load_project_tree()
        self._write_hint("Saved.")
        return True

    def _save_as(self) -> bool:
        path = filedialog.asksaveasfilename(
            initialdir=str(self.project_dir),
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return False
        self.current_file = Path(path)
        self.project_dir = self.current_file.parent
        return self._save_file()

    def _new_project_file(self) -> None:
        name = simpledialog.askstring("New Python file", "File name:", initialvalue="main.py")
        if not name:
            return
        if not name.endswith(".py"):
            name += ".py"
        path = self.project_dir / name
        if path.exists() and not messagebox.askyesno("Replace file?", f"{name} already exists. Open it instead?"):
            return
        if not path.exists():
            path.write_text(SNIPPETS["Starter Script"], encoding="utf-8")
        self._load_file(path)

    def _load_project_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.project_label.configure(text=str(self.project_dir))
        root_id = self.tree.insert("", "end", text=self.project_dir.name or str(self.project_dir), open=True, values=[str(self.project_dir)])
        self._add_tree_items(root_id, self.project_dir, depth=0)

    def _add_tree_items(self, parent_id: str, directory: Path, depth: int) -> None:
        if depth > 2:
            return
        try:
            items = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        except OSError:
            return
        for item in items:
            if item.name.startswith(".") or item.name in {"__pycache__", "build", "dist"}:
                continue
            if item.is_dir() or item.suffix.lower() in {".py", ".txt", ".md", ".json", ".csv"}:
                node = self.tree.insert(parent_id, "end", text=item.name, open=False, values=[str(item)])
                if item.is_dir():
                    self._add_tree_items(node, item, depth + 1)

    def _open_tree_selection(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        path = Path(values[0])
        if path.is_file():
            if self._confirm_discard():
                self._load_file(path)

    def _set_editor_text(self, text: str) -> None:
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_modified(False)
        self._after_edit()

    def _insert_snippet(self, name: str) -> None:
        self.editor.insert("insert", SNIPPETS[name])
        self._after_edit()

    def _replace_with_snippet(self, name: str) -> None:
        if self.dirty and not messagebox.askyesno("Replace editor contents?", "Replace the current editor contents with this game template?"):
            return
        self._set_editor_text(SNIPPETS[name])
        self.current_file = None
        self.dirty = True
        self._refresh_title()
        self._write_hint(f"{name} loaded. Press Play Preview or F6 to test it inside Forge Studio.")

    def _start_game_preview(self) -> None:
        if self.preview_running:
            self._stop_game_preview()
        if not self._check_syntax(silent=True):
            return

        api = GamePreviewAPI(self.preview_canvas, self.preview_keys, self.preview_camera)
        namespace = {
            "__name__": "__forge_preview__",
            "api": api,
            "math": math,
            "random": random,
            "clear": api.clear,
            "rect": api.rect,
            "circle": api.circle,
            "line": api.line,
            "text": api.text,
            "key": api.key,
            "width": api.width,
            "height": api.height,
            "distance": api.distance,
            "set_camera": api.set_camera,
            "move_camera": api.move_camera,
            "cube3d": api.cube3d,
            "grid3d": api.grid3d,
        }
        code = self.editor.get("1.0", "end-1c")
        try:
            exec(compile(code, "<forge-game-preview>", "exec"), namespace)
            if callable(namespace.get("setup")):
                namespace["setup"]()
        except Exception:
            self._append_output("\nGame preview failed to start:\n" + traceback.format_exc() + "\n")
            self.preview_status.configure(text="Preview error. Check Output.")
            return

        self.preview_namespace = namespace
        self.preview_running = True
        self.preview_last_time = time.perf_counter()
        self.preview_canvas.focus_set()
        self.preview_status.configure(text="Preview running. Left-drag rotate, right-drag pan, wheel zoom, WASD/QE moves camera.")
        self._write_hint("Game Preview scripts can define setup(), update(dt), and draw(). Use key('w'), circle(), rect(), cube3d(), and grid3d().")
        self._preview_tick()

    def _preview_tick(self) -> None:
        if not self.preview_running or self.preview_namespace is None:
            return

        now = time.perf_counter()
        dt = min(0.05, now - self.preview_last_time)
        self.preview_last_time = now

        try:
            self._update_preview_camera_from_keys(dt)
            update = self.preview_namespace.get("update")
            draw = self.preview_namespace.get("draw")
            if callable(update):
                update(dt)
            if callable(draw):
                draw()
            else:
                self.preview_namespace["clear"]("#080b12")
                self.preview_namespace["text"](18, 18, "No draw() function found.", color="#ffc766", size=14)
        except Exception:
            self.preview_running = False
            self.preview_status.configure(text="Preview stopped after an error. Check Output.")
            self._append_output("\nGame preview error:\n" + traceback.format_exc() + "\n")
            return

        self.after(16, self._preview_tick)

    def _update_preview_camera_from_keys(self, dt: float) -> None:
        speed = 5.0 * dt
        fast = 2.2 if self.preview_keys.intersection({"shift_l", "shift_r"}) else 1.0
        speed *= fast
        yaw = self.preview_camera["yaw"]
        forward_x = math.sin(yaw)
        forward_z = math.cos(yaw)
        right_x = math.cos(yaw)
        right_z = -math.sin(yaw)

        if self._preview_key_pressed("w"):
            self.preview_camera["x"] += forward_x * speed
            self.preview_camera["z"] += forward_z * speed
        if self._preview_key_pressed("s"):
            self.preview_camera["x"] -= forward_x * speed
            self.preview_camera["z"] -= forward_z * speed
        if self._preview_key_pressed("a"):
            self.preview_camera["x"] -= right_x * speed
            self.preview_camera["z"] -= right_z * speed
        if self._preview_key_pressed("d"):
            self.preview_camera["x"] += right_x * speed
            self.preview_camera["z"] += right_z * speed
        if self._preview_key_pressed("q"):
            self.preview_camera["y"] -= speed
        if self._preview_key_pressed("e"):
            self.preview_camera["y"] += speed

    def _preview_key_pressed(self, name: str) -> bool:
        return name.lower() in self.preview_keys

    def _stop_game_preview(self) -> None:
        self.preview_running = False
        self.preview_namespace = None
        self.preview_keys.clear()
        if hasattr(self, "preview_canvas"):
            self._draw_empty_viewport()
        if hasattr(self, "preview_status"):
            self.preview_status.configure(text="Preview stopped. Move the viewport or load a 2D/3D template and press Play.")

    def _preview_key_down(self, event: tk.Event) -> None:
        self.preview_keys.add(str(event.keysym).lower())
        if event.char:
            self.preview_keys.add(event.char.lower())

    def _preview_key_up(self, event: tk.Event) -> None:
        self.preview_keys.discard(str(event.keysym).lower())
        if event.char:
            self.preview_keys.discard(event.char.lower())

    def _preview_mouse_down(self, event: tk.Event, button: str) -> None:
        self.preview_canvas.focus_set()
        self.preview_mouse = {"x": event.x, "y": event.y, "button": button}

    def _preview_mouse_drag(self, event: tk.Event) -> None:
        dx = event.x - self.preview_mouse["x"]
        dy = event.y - self.preview_mouse["y"]
        self.preview_mouse["x"] = event.x
        self.preview_mouse["y"] = event.y

        if self.preview_mouse["button"] == "rotate":
            self.preview_camera["yaw"] += dx * 0.008
            self.preview_camera["pitch"] = max(-1.2, min(1.2, self.preview_camera["pitch"] + dy * 0.006))
        else:
            yaw = self.preview_camera["yaw"]
            self.preview_camera["x"] -= math.cos(yaw) * dx * 0.012
            self.preview_camera["z"] += math.sin(yaw) * dx * 0.012
            self.preview_camera["y"] += dy * 0.012

        if not self.preview_running:
            self._draw_empty_viewport()

    def _preview_mouse_wheel(self, event: tk.Event) -> None:
        self._preview_zoom(-1 if event.delta > 0 else 1)

    def _preview_zoom(self, direction: int) -> None:
        yaw = self.preview_camera["yaw"]
        amount = direction * 0.8
        self.preview_camera["x"] += math.sin(yaw) * amount
        self.preview_camera["z"] += math.cos(yaw) * amount
        if not self.preview_running:
            self._draw_empty_viewport()

    def _reset_preview_camera(self) -> None:
        self.preview_camera.update({"x": 0.0, "y": 0.0, "z": -7.0, "yaw": 0.0, "pitch": 0.0})
        self.preview_status.configure(text="Camera reset. Left-drag rotate, right-drag pan, wheel zoom.")
        if not self.preview_running:
            self._draw_empty_viewport()

    def _draw_empty_viewport(self) -> None:
        api = GamePreviewAPI(self.preview_canvas, self.preview_keys, self.preview_camera)
        api.clear("#080b12")
        api.grid3d(size=10, step=1, color="#26384a")
        api.cube3d(0, 0, 4, 1.3, color=self.theme["accent"], yaw=time.perf_counter() * 0.2)
        api.text(16, 16, "Studio Viewport", color=self.theme["text"], size=14)
        api.text(16, 42, "Play a 3D template, or move the camera now.", color=self.theme["muted"], size=11)

    def _run_code(self) -> None:
        if self.runner is not None:
            messagebox.showinfo("Code is running", "Stop the current run before starting another.")
            return
        if not self._check_syntax(silent=True):
            return
        if self.current_file is None:
            run_path = Path(tempfile.gettempdir()) / "forge_studio_temp_run.py"
            run_path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        else:
            if self.dirty and not self._save_file():
                return
            run_path = self.current_file

        self._clear_output()
        self._append_output(f"Running {run_path.name}\n\n")
        runner = self._python_command()
        if runner:
            command = runner + [str(run_path)]
            self.runner = subprocess.Popen(
                command,
                cwd=str(run_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            threading.Thread(target=self._read_process_output, daemon=True).start()
        else:
            threading.Thread(target=self._run_internal, args=(run_path,), daemon=True).start()

    def _python_command(self) -> list[str] | None:
        candidates: list[list[str]] = []
        if not getattr(sys, "frozen", False):
            candidates.append([sys.executable])
        if os.name == "nt":
            candidates.extend([["py", "-3"], ["python"]])
        else:
            candidates.extend([["python3"], ["python"]])
        for command in candidates:
            if shutil.which(command[0]):
                return command
        return None

    def _read_process_output(self) -> None:
        assert self.runner is not None
        assert self.runner.stdout is not None
        for line in self.runner.stdout:
            self.output_queue.put(line)
        code = self.runner.wait()
        self.output_queue.put(f"\nProcess finished with exit code {code}\n")
        self.runner = None

    def _run_internal(self, run_path: Path) -> None:
        buffer = io.StringIO()
        namespace = {"__name__": "__main__", "__file__": str(run_path)}
        try:
            with redirect_stdout(buffer), redirect_stderr(buffer):
                exec(compile(run_path.read_text(encoding="utf-8"), str(run_path), "exec"), namespace)
        except Exception as error:
            buffer.write(f"\n{type(error).__name__}: {error}\n")
        self.output_queue.put(buffer.getvalue())
        self.output_queue.put("\nFinished using internal runner. Install Python for full subprocess runs.\n")

    def _poll_output(self) -> None:
        while True:
            try:
                text = self.output_queue.get_nowait()
            except queue.Empty:
                break
            self._append_output(text)
        self.after(80, self._poll_output)

    def _stop_code(self) -> None:
        if self.runner is None:
            self._append_output("\nNo running process.\n")
            return
        self.runner.terminate()
        self._append_output("\nStop requested.\n")

    def _check_syntax(self, silent: bool = False) -> bool:
        self.editor.tag_remove("error", "1.0", "end")
        code = self.editor.get("1.0", "end-1c")
        try:
            ast.parse(code)
        except SyntaxError as error:
            line = error.lineno or 1
            col = error.offset or 1
            self.editor.tag_add("error", f"{line}.{max(col - 1, 0)}", f"{line}.end")
            message = f"Syntax issue on line {line}: {error.msg}"
            self._write_hint(message)
            if not silent:
                messagebox.showerror("Syntax check", message)
            return False
        self._write_hint("Syntax check passed. Ready to run.")
        if not silent:
            messagebox.showinfo("Syntax check", "No syntax errors found.")
        return True

    def _highlight_syntax(self) -> None:
        for tag in ("keyword", "string", "comment", "number"):
            self.editor.tag_remove(tag, "1.0", "end")
        code = self.editor.get("1.0", "end-1c")
        for match in re_finditer(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code):
            if match.group(0) in PY_KEYWORDS:
                self._tag_match("keyword", match)
        for match in re_finditer(r"#[^\n]*", code):
            self._tag_match("comment", match)
        for match in re_finditer(r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", code):
            self._tag_match("string", match)
        for match in re_finditer(r"\b\d+(\.\d+)?\b", code):
            self._tag_match("number", match)

    def _tag_match(self, tag: str, match) -> None:
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        self.editor.tag_add(tag, start, end)

    def _after_edit(self) -> None:
        self._update_line_numbers()
        self._highlight_syntax()
        self._update_status()

    def _on_modified(self, _event: tk.Event) -> None:
        if self.editor.edit_modified():
            self.dirty = True
            self._refresh_title()
            self.editor.edit_modified(False)

    def _update_line_numbers(self) -> None:
        total = int(self.editor.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, total + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.configure(state="disabled")

    def _scroll_editor(self, *args) -> None:
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def _on_editor_scroll(self, first: str, last: str, scrollbar: ttk.Scrollbar) -> None:
        scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def _write_hint(self, text: str) -> None:
        if not self.teach_mode:
            return
        self.hints.configure(state="normal")
        self.hints.delete("1.0", "end")
        self.hints.insert("1.0", text)
        self.hints.configure(state="disabled")

    def _clear_output(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _append_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _refresh_title(self) -> None:
        name = self.current_file.name if self.current_file else "Untitled"
        marker = " *" if self.dirty else ""
        self.file_title.configure(text=f"{name}{marker}")
        self.title(f"{APP_NAME} {APP_VERSION} - {name}{marker}")

    def _update_status(self) -> None:
        line, col = self.editor.index("insert").split(".")
        file_text = str(self.current_file) if self.current_file else "Unsaved file"
        self.status.configure(text=f"{file_text}    Line {line}, Column {int(col) + 1}    Mode: {self.current_theme_name}")

    def _toggle_focus(self) -> None:
        self.focus_mode = not self.focus_mode
        if self.focus_mode:
            self.main.forget(self.sidebar)
            self._write_hint("Focus mode hides the project panel. Use Modes > Focus Mode to bring it back.")
        else:
            self.main.insert(0, self.sidebar, weight=1)

    def _toggle_teach(self) -> None:
        self.teach_mode = not self.teach_mode
        state = "on" if self.teach_mode else "off"
        self._write_hint(f"Teach mode is {state}.")

    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved changes", "Save your changes first?")
        if answer is None:
            return False
        if answer:
            return self._save_file()
        return True

    def _on_close(self) -> None:
        if self.runner is not None and not messagebox.askyesno("Code is running", "Stop the running code and exit?"):
            return
        if self.runner is not None:
            self._stop_code()
            time.sleep(0.2)
        if self._confirm_discard():
            self.destroy()


def re_finditer(pattern: str, text: str):
    import re

    return re.finditer(pattern, text, flags=re.MULTILINE)


if __name__ == "__main__":
    ForgeStudio().mainloop()
