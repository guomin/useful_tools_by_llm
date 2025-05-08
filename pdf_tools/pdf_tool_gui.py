import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import io
import sys

# 应用版本号
VERSION = "v0.0.1.21"

# 尝试导入ttkthemes，如果不存在则使用标准主题
try:
    from ttkthemes import ThemedTk, ThemedStyle
    HAS_THEMED_TK = True
except ImportError:
    HAS_THEMED_TK = False

class UIThemeManager:
    """用于管理应用主题和样式的类"""
    
    def __init__(self, root):
        self.root = root
        # 定义颜色
        self.bg_color = "#f5f5f5"  # 背景颜色
        self.accent_color = "#3498db"  # 强调色
        self.text_color = "#2c3e50"  # 文本颜色
        self.button_bg = "#4b6584"  # 按钮背景色
        
        # 设置主题
        if HAS_THEMED_TK and isinstance(root, ThemedTk):
            self.style = ThemedStyle(root)
            self.style.set_theme("arc")  # 使用arc主题
        else:
            self.style = ttk.Style()
            if sys.platform.startswith("win"):
                self.style.theme_use("vista")
        
        # 配置通用样式
        self.configure_styles()
        
        # 设置根窗口背景
        self.root.configure(bg=self.bg_color)
        
    def configure_styles(self):
        """配置通用样式"""
        self.style.configure("TButton", padding=5, font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10), foreground=self.text_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabelframe", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TLabelframe.Label", font=("Arial", 10, "bold"), foreground=self.text_color)
        self.style.configure("TNotebook", background=self.bg_color, tabposition="n")
        self.style.configure("TNotebook.Tab", padding=[12, 4], font=("Arial", 10, "bold"))
        
        # 自定义按钮样式
        self.style.configure("Action.TButton", font=("Arial", 10, "bold"))
        self.style.map("Action.TButton", 
                      background=[('active', self.accent_color)],
                      foreground=[('active', 'white')])
                      
        # 创建主操作按钮样式 - 增强颜色区分度
        self.style.configure("Primary.TButton", 
                           font=("Arial", 11, "bold")
                           )
        self.style.map("Primary.TButton", 
                      background=[('active', '#1a5276'), ('pressed', '#154360')],  # 使用更深的蓝色增强对比度
                      foreground=[('pressed', '#f0f0f0')])  # 确保文本在所有状态下保持可见


class BaseFileOperations:
    """文件操作的基类，提供共享的文件操作功能"""
    
    @staticmethod
    def select_output_directory(title="选择输出目录"):
        """选择输出目录并返回路径"""
        dir_path = filedialog.askdirectory(title=title)
        return dir_path if dir_path else None
    
    @staticmethod
    def ensure_directory(dir_path):
        """确保目录存在，如果不存在则创建"""
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path


# 导入PDF压缩模块
from modules.pdf_compressor import PDFCompressorTab
from modules.pdf_merger import MergePDFTab
from modules.pdf_to_image import PDFToImageTab
from modules.image_convert import ImageConvertTab
from modules.pdf_properties import PDFPropertiesTab  # 导入新的PDF属性查看模块
from modules.pdf_resizer import PDFResizerTab  # 导入新的PDF页面尺寸转换模块

class PDFToolGUI:
    """PDF工具箱主类"""
    
    def __init__(self, root):
        self.root = root
        # 设置应用标题
        self.root.title(f"高级PDF工具箱 {VERSION}")
        self.root.geometry("950x720")
        
        # 尝试设置应用图标
        try:
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件，使用不同的路径
                application_path = os.path.dirname(sys.executable)
                icon_path = os.path.join(application_path, "icon.ico")
            else:
                icon_path = "icon.ico"
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # 如果无法设置图标，则忽略错误

        # 初始化主题管理器
        self.theme_manager = UIThemeManager(root)
        
        # 创建界面组件
        self.create_widgets()
        
    def create_widgets(self):
        """创建GUI组件"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        
        # 创建各个功能标签页
        self.merge_tab = MergePDFTab(self.notebook, self.theme_manager)
        self.pdf_to_image_tab = PDFToImageTab(self.notebook, self.theme_manager)
        self.image_convert_tab = ImageConvertTab(self.notebook, self.theme_manager)
        self.pdf_compressor_tab = PDFCompressorTab(self.notebook)  # PDF压缩标签页
        self.pdf_properties_tab = PDFPropertiesTab(self.notebook, self.theme_manager)  # PDF属性查看标签页
        self.pdf_resizer_tab = PDFResizerTab(self.notebook, self.theme_manager)  # PDF页面尺寸转换标签页
        
        # 添加标签页到notebook
        self.notebook.add(self.merge_tab.frame, text="合并PDF和图片")
        self.notebook.add(self.pdf_to_image_tab.frame, text="PDF转图片")
        self.notebook.add(self.image_convert_tab.frame, text="图片格式转换")
        self.notebook.add(self.pdf_compressor_tab.frame, text="PDF压缩")
        self.notebook.add(self.pdf_properties_tab.frame, text="PDF属性查看")
        self.notebook.add(self.pdf_resizer_tab.frame, text="PDF页面尺寸转换")  # 添加PDF页面尺寸转换标签页
        
        self.notebook.pack(expand=1, fill="both", padx=15, pady=15)
        
        # 添加状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor="w", padding=(5, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 10))


if __name__ == "__main__":
    # 检查是否可以使用主题化的Tk
    if HAS_THEMED_TK:
        root = ThemedTk(theme="arc")
    else:
        root = tk.Tk()
    
    app = PDFToolGUI(root)
    root.mainloop()
