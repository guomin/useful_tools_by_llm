import tkinter as tk
from tkinter import ttk
import sys

# 尝试导入ttkthemes
try:
    from ttkthemes import ThemedTk, ThemedStyle
    HAS_THEMED_TK = True
except ImportError:
    HAS_THEMED_TK = False

def setup_ui_style(root):
    """设置界面样式，返回样式对象"""
    # 应用主题
    if HAS_THEMED_TK and isinstance(root, ThemedTk):
        style = ThemedStyle(root)
        style.set_theme("arc")  # 使用arc主题，也可以选择其他如"plastik", "clearlooks", "radiance"等
    else:
        style = ttk.Style()
        if sys.platform.startswith("win"):
            style.theme_use("vista")
            
    # 定义颜色
    bg_color = "#f5f5f5"  # 背景颜色
    accent_color = "#3498db"  # 强调色
    text_color = "#2c3e50"  # 文本颜色
    button_bg = "#4b6584"  # 按钮背景色
    
    # 配置通用样式
    style.configure("TButton", padding=5, font=("Arial", 10))
    style.configure("TLabel", font=("Arial", 10), foreground=text_color)
    style.configure("TFrame", background=bg_color)
    style.configure("TLabelframe", background=bg_color, foreground=text_color)
    style.configure("TLabelframe.Label", font=("Arial", 10, "bold"), foreground=text_color)
    style.configure("TNotebook", background=bg_color, tabposition="n")
    style.configure("TNotebook.Tab", padding=[12, 4], font=("Arial", 10, "bold"))
    
    # 创建主操作按钮样式
    style.configure("Primary.TButton", 
                   font=("Arial", 11, "bold"),
                   background=accent_color, 
                   foreground="white")
    style.map("Primary.TButton", 
              background=[('active', '#2980b9')],
              foreground=[('active', 'white')])
    
    # 创建动作按钮样式
    style.configure("Action.TButton", font=("Arial", 10, "bold"))
    style.map("Action.TButton", 
              background=[('active', accent_color)],
              foreground=[('active', 'white')])
    
    # 设置根窗口背景
    root.configure(bg=bg_color)
    
    return style

def create_scrollable_frame(parent, label_text=""):
    """创建带滚动条的框架"""
    if label_text:
        container = ttk.LabelFrame(parent, text=label_text)
    else:
        container = ttk.Frame(parent)
        
    # 创建一个带滚动条的列表框
    listbox = tk.Listbox(container, selectmode=tk.EXTENDED, 
                        font=("Arial", 10), 
                        bg="white", fg="#2c3e50",
                        selectbackground="#3498db",
                        relief=tk.SUNKEN, bd=1,
                        highlightthickness=1)
    listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=8, pady=8)
    
    # 滚动条
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y", pady=8, padx=(0, 8))
    listbox.config(yscrollcommand=scrollbar.set)
    
    return container, listbox
