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

# 尝试导入ttkthemes，如果不存在则使用标准主题
try:
    from ttkthemes import ThemedTk, ThemedStyle
    HAS_THEMED_TK = True
except ImportError:
    HAS_THEMED_TK = False

class PDFToolGUI:
    def __init__(self, root):
        self.root = root
        # 设置应用标题
        self.root.title("高级PDF工具箱")
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

        # 应用主题
        if HAS_THEMED_TK and isinstance(root, ThemedTk):
            self.style = ThemedStyle(root)
            self.style.set_theme("arc")  # 使用arc主题，也可以选择其他如"plastik", "clearlooks", "radiance"等
        else:
            self.style = ttk.Style()
            if sys.platform.startswith("win"):
                self.style.theme_use("vista")
            
        # 定义颜色
        self.bg_color = "#f5f5f5"  # 背景颜色
        self.accent_color = "#3498db"  # 强调色
        self.text_color = "#2c3e50"  # 文本颜色
        self.button_bg = "#4b6584"  # 按钮背景色
        
        # 配置通用样式
        self.style.configure("TButton", padding=5, font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10), foreground=self.text_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabelframe", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TLabelframe.Label", font=("Arial", 10, "bold"), foreground=self.text_color)
        self.style.configure("TNotebook", background=self.bg_color, tabposition="n")
        self.style.configure("TNotebook.Tab", padding=[12, 4], font=("Arial", 10, "bold"))
        
        # 设置根窗口背景
        self.root.configure(bg=self.bg_color)
        
        # 文件列表和版面模式
        self.file_paths = []
        self.layout_mode = tk.StringVar(value="原样")
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建GUI组件"""
        # 创建标签页
        notebook = ttk.Notebook(self.root)
        merge_frame = ttk.Frame(notebook)
        convert_frame = ttk.Frame(notebook)
        img_convert_frame = ttk.Frame(notebook)  # 新增图片转换标签页
        
        notebook.add(merge_frame, text="合并PDF和图片")
        notebook.add(convert_frame, text="PDF转图片")
        notebook.add(img_convert_frame, text="图片格式转换")  # 添加新标签页
        notebook.pack(expand=1, fill="both", padx=15, pady=15)
        
        # 合并PDF和图片页面
        self.setup_merge_frame(merge_frame)
        
        # PDF转图片页面
        self.setup_convert_frame(convert_frame)
        
        # 图片格式转换页面
        self.setup_img_convert_frame(img_convert_frame)
        
        # 添加状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor="w", padding=(5, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 10))

    def setup_merge_frame(self, frame):
        """设置合并PDF和图片页面"""
        # 版面模式选择 - 使用更美观的选项卡样式
        mode_frame = ttk.LabelFrame(frame, text="版面模式")
        mode_frame.pack(fill="x", padx=15, pady=10)
        
        modes = ["原样", "自动调整", "手动调整"]
        mode_container = ttk.Frame(mode_frame)
        mode_container.pack(fill="x", padx=5, pady=8)
        
        for mode in modes:
            ttk.Radiobutton(mode_container, text=mode, value=mode,
                          variable=self.layout_mode).pack(side=tk.LEFT, padx=25, pady=5)
        
        # 文件列表
        file_frame = ttk.LabelFrame(frame, text="文件列表")
        file_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 文件列表显示 - 添加边框和颜色
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, 
                                      font=("Arial", 10), 
                                      bg="white", fg=self.text_color,
                                      selectbackground=self.accent_color,
                                      relief=tk.SUNKEN, bd=1,
                                      highlightthickness=1)
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=8, pady=8)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y", pady=8, padx=(0, 8))
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # 文件操作按钮 - 使用图标按钮
        file_btn_frame = ttk.Frame(frame)
        file_btn_frame.pack(fill="x", padx=15, pady=10)
        
        # 自定义按钮样式
        self.style.configure("Action.TButton", font=("Arial", 10, "bold"))
        self.style.map("Action.TButton", 
                      background=[('active', self.accent_color)],
                      foreground=[('active', 'white')])
        
        buttons_info = [
            ("添加文件", self.add_files),
            ("移除选中", self.remove_selected),
            ("上移", lambda: self.move_item(-1)),
            ("下移", lambda: self.move_item(1)),
            ("清空列表", self.clear_list)
        ]
        
        for text, command in buttons_info:
            ttk.Button(file_btn_frame, text=text, command=command, style="Action.TButton").pack(
                side=tk.LEFT, padx=5, pady=5)
        
        # 手动调整面板（默认隐藏）- 添加更多视觉指导
        self.manual_frame = ttk.LabelFrame(frame, text="手动调整设置")
        
        settings_frame = ttk.Frame(self.manual_frame)
        settings_frame.pack(fill="x", padx=8, pady=8)
        
        ttk.Label(settings_frame, text="页面尺寸:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.page_size_var = tk.StringVar(value="A4")
        page_sizes = ["A4", "A5", "Letter", "Legal", "自定义"]
        size_combo = ttk.Combobox(settings_frame, textvariable=self.page_size_var, values=page_sizes, width=15)
        size_combo.grid(row=0, column=1, padx=8, pady=8)
        
        ttk.Label(settings_frame, text="宽度(mm):").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.width_var = tk.StringVar(value="210")
        ttk.Entry(settings_frame, textvariable=self.width_var, width=8).grid(row=1, column=1, padx=8, pady=8)
        
        ttk.Label(settings_frame, text="高度(mm):").grid(row=1, column=2, padx=8, pady=8, sticky="w")
        self.height_var = tk.StringVar(value="297")
        ttk.Entry(settings_frame, textvariable=self.height_var, width=8).grid(row=1, column=3, padx=8, pady=8)
        
        ttk.Label(settings_frame, text="页边距(mm):").grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.margin_var = tk.StringVar(value="10")
        ttk.Entry(settings_frame, textvariable=self.margin_var, width=8).grid(row=2, column=1, padx=8, pady=8)
        
        # 合并按钮 - 更突出的按钮样式
        merge_btn_frame = ttk.Frame(frame)
        merge_btn_frame.pack(fill="x", padx=15, pady=15)
        
        # 创建主操作按钮样式
        self.style.configure("Primary.TButton", 
                           font=("Arial", 11, "bold"),
                           background=self.accent_color, 
                           foreground="white")
        self.style.map("Primary.TButton", 
                      background=[('active', '#2980b9')],
                      foreground=[('active', 'white')])
                           
        ttk.Button(merge_btn_frame, text="合并文件", command=self.merge_files, 
                 style="Primary.TButton").pack(side=tk.RIGHT, padx=8, pady=5)
        
        # 绑定版面模式变化事件
        self.layout_mode.trace("w", self.on_layout_mode_change)
        
    def setup_convert_frame(self, frame):
        """设置PDF转图片页面"""
        # PDF文件选择
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(select_frame, text="PDF文件:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # 改用按钮组来选择PDF文件和文件夹
        buttons_frame = ttk.Frame(select_frame)
        buttons_frame.pack(side=tk.LEFT, fill="x", expand=True)
        
        ttk.Button(buttons_frame, text="选择文件", command=self.select_pdf_files).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="选择文件夹", command=self.select_pdf_folder).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="清空列表", command=self.clear_pdf_list).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 文件列表显示区域
        file_list_frame = ttk.LabelFrame(frame, text="PDF文件列表")
        file_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # PDF文件列表
        self.pdf_listbox = tk.Listbox(file_list_frame, selectmode=tk.EXTENDED, height=6)
        self.pdf_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=self.pdf_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.pdf_listbox.config(yscrollcommand=scrollbar.set)
        
        # 移除选中的文件按钮
        ttk.Button(file_list_frame, text="移除选中", command=self.remove_selected_pdfs).pack(side=tk.BOTTOM, padx=5, pady=5)
        
        # 初始化PDF文件路径列表
        self.pdf_file_paths = []
        
        # 输出格式
        format_frame = ttk.Frame(frame)
        format_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT, padx=5, pady=5)
        self.output_format = tk.StringVar(value="JPG")
        formats = ["JPG", "PNG", "TIFF", "BMP"]
        ttk.Combobox(format_frame, textvariable=self.output_format, values=formats, width=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(format_frame, text="DPI:").pack(side=tk.LEFT, padx=5, pady=5)
        self.dpi_var = tk.StringVar(value="300")
        ttk.Entry(format_frame, textvariable=self.dpi_var, width=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 页面范围
        range_frame = ttk.Frame(frame)
        range_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(range_frame, text="页面范围:").pack(side=tk.LEFT, padx=5, pady=5)
        self.range_var = tk.StringVar(value="全部")
        ttk.Radiobutton(range_frame, text="全部", value="全部", variable=self.range_var).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Radiobutton(range_frame, text="自定义", value="自定义", variable=self.range_var).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(range_frame, text="页码(如1-3,5,7-9):").pack(side=tk.LEFT, padx=5, pady=5)
        self.page_range = tk.StringVar()
        self.page_range_entry = ttk.Entry(range_frame, textvariable=self.page_range, width=15)
        self.page_range_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.page_range_entry.config(state="disabled")
        
        # 绑定范围选择变化
        self.range_var.trace("w", self.on_range_change)
        
        # 输出目录
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT, padx=5, pady=5)
        self.output_dir = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        ttk.Button(output_frame, text="浏览", command=self.select_output_dir).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 转换按钮和进度条
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress = ttk.Progressbar(action_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", side=tk.LEFT, expand=True, padx=5, pady=5)
        
        ttk.Button(action_frame, text="转换", command=self.convert_pdf_to_images).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="处理日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = ScrolledText(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def setup_img_convert_frame(self, frame):
        """设置图片格式转换页面"""
        # 图片文件选择
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(select_frame, text="图片文件:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # 按钮组来选择图片文件和文件夹
        buttons_frame = ttk.Frame(select_frame)
        buttons_frame.pack(side=tk.LEFT, fill="x", expand=True)
        
        ttk.Button(buttons_frame, text="选择文件", command=self.select_image_files).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="选择文件夹", command=self.select_image_folder).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="清空列表", command=self.clear_image_list).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 文件列表显示区域
        file_list_frame = ttk.LabelFrame(frame, text="图片文件列表")
        file_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 图片文件列表
        self.img_listbox = tk.Listbox(file_list_frame, selectmode=tk.EXTENDED, height=8)
        self.img_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=self.img_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.img_listbox.config(yscrollcommand=scrollbar.set)
        
        # 移除选中的文件按钮
        ttk.Button(file_list_frame, text="移除选中", command=self.remove_selected_images).pack(side=tk.BOTTOM, padx=5, pady=5)
        
        # 初始化图片文件路径列表
        self.img_file_paths = []
        
        # 输入格式和输出格式
        format_frame = ttk.Frame(frame)
        format_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(format_frame, text="源格式:").pack(side=tk.LEFT, padx=5, pady=5)
        self.input_format = tk.StringVar(value="全部")
        input_formats = ["全部", "JPG", "PNG", "TIFF", "BMP", "GIF"]
        ttk.Combobox(format_frame, textvariable=self.input_format, values=input_formats, width=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(format_frame, text="目标格式:").pack(side=tk.LEFT, padx=5, pady=5)
        self.img_output_format = tk.StringVar(value="JPG")
        output_formats = ["JPG", "PNG", "TIFF", "BMP", "GIF"]
        ttk.Combobox(format_frame, textvariable=self.img_output_format, values=output_formats, width=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 图像质量和尺寸选项
        quality_frame = ttk.Frame(frame)
        quality_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(quality_frame, text="图像质量(1-100):").pack(side=tk.LEFT, padx=5, pady=5)
        self.quality_var = tk.StringVar(value="85")
        ttk.Entry(quality_frame, textvariable=self.quality_var, width=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 调整尺寸选项
        resize_frame = ttk.Frame(frame)
        resize_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(resize_frame, text="调整尺寸:").pack(side=tk.LEFT, padx=5, pady=5)
        self.resize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(resize_frame, text="启用", variable=self.resize_var, command=self.toggle_resize_options).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.resize_options_frame = ttk.Frame(resize_frame)
        ttk.Label(self.resize_options_frame, text="宽度:").pack(side=tk.LEFT, padx=5, pady=5)
        self.width_var = tk.StringVar()
        ttk.Entry(self.resize_options_frame, textvariable=self.width_var, width=6).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(self.resize_options_frame, text="高度:").pack(side=tk.LEFT, padx=5, pady=5)
        self.height_var = tk.StringVar()
        ttk.Entry(self.resize_options_frame, textvariable=self.height_var, width=6).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(self.resize_options_frame, text="保持比例:").pack(side=tk.LEFT, padx=5, pady=5)
        self.keep_ratio = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.resize_options_frame, variable=self.keep_ratio).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 输出目录
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT, padx=5, pady=5)
        self.img_output_dir = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.img_output_dir, width=50).pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        ttk.Button(output_frame, text="浏览", command=self.select_img_output_dir).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 转换按钮和进度条
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.img_progress = ttk.Progressbar(action_frame, orient="horizontal", length=100, mode="determinate")
        self.img_progress.pack(fill="x", side=tk.LEFT, expand=True, padx=5, pady=5)
        
        ttk.Button(action_frame, text="转换", command=self.convert_images).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="处理日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.img_log_text = ScrolledText(log_frame, height=8)
        self.img_log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 初始时禁用调整尺寸选项
        self.resize_options_frame.pack_forget()
    
    def toggle_resize_options(self):
        """切换调整尺寸选项的可见性"""
        if self.resize_var.get():
            self.resize_options_frame.pack(side=tk.LEFT, padx=5, pady=5)
        else:
            self.resize_options_frame.pack_forget()
    
    def select_image_files(self):
        """选择多个图片文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tif")]
        )
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.img_file_paths:
                    self.img_file_paths.append(file_path)
                    self.img_listbox.insert(tk.END, os.path.basename(file_path))
    
    def select_image_folder(self):
        """选择包含图片文件的文件夹"""
        folder_path = filedialog.askdirectory(title="选择包含图片文件的文件夹")
        if folder_path:
            # 搜索文件夹中的所有图片文件
            image_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif')):
                        full_path = os.path.join(root, file)
                        image_files.append(full_path)
            
            # 添加到列表中
            for file_path in image_files:
                if file_path not in self.img_file_paths:
                    self.img_file_paths.append(file_path)
                    self.img_listbox.insert(tk.END, os.path.basename(file_path))
            
            if not image_files:
                messagebox.showinfo("提示", "所选文件夹中没有找到图片文件")
    
    def remove_selected_images(self):
        """移除选中的图片文件"""
        selected_indices = self.img_listbox.curselection()
        for index in reversed(selected_indices):
            self.img_listbox.delete(index)
            self.img_file_paths.pop(index)
    
    def clear_image_list(self):
        """清空图片文件列表"""
        self.img_listbox.delete(0, tk.END)
        self.img_file_paths = []
    
    def select_img_output_dir(self):
        """选择图片输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.img_output_dir.set(dir_path)
    
    def convert_images(self):
        """转换图片格式"""
        if not self.img_file_paths:
            messagebox.showwarning("警告", "请选择至少一个图片文件")
            return
        
        output_dir = self.img_output_dir.get()
        
        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 获取转换参数
        input_format = self.input_format.get().lower()
        output_format = self.img_output_format.get().lower()
        quality = int(self.quality_var.get())
        
        # 检查质量参数
        if quality < 1 or quality > 100:
            messagebox.showwarning("警告", "图像质量必须在1-100范围内")
            return
        
        # 获取调整尺寸的选项
        resize_enabled = self.resize_var.get()
        width = None
        height = None
        if resize_enabled:
            try:
                if self.width_var.get():
                    width = int(self.width_var.get())
                if self.height_var.get():
                    height = int(self.height_var.get())
                
                if not width and not height:
                    messagebox.showwarning("警告", "请至少指定宽度或高度")
                    return
            except ValueError:
                messagebox.showwarning("警告", "宽度和高度必须是整数")
                return
        
        # 准备线程
        def conversion_thread():
            try:
                self.img_log_text.delete(1.0, tk.END)
                self.img_log_text.insert(tk.END, "开始批量转换图片格式...\n")
                
                total_files = len(self.img_file_paths)
                success_count = 0
                
                # 设置进度条
                self.img_progress["maximum"] = total_files
                self.img_progress["value"] = 0
                
                # 对每个文件进行处理
                for i, file_path in enumerate(self.img_file_paths):
                    # 获取文件扩展名和不带扩展名的文件名
                    file_ext = os.path.splitext(file_path)[1].lower()
                    base_filename = os.path.splitext(os.path.basename(file_path))[0]
                    
                    # 检查输入格式筛选
                    if input_format != "全部":
                        if input_format == "jpg" and file_ext not in ['.jpg', '.jpeg']:
                            self.img_log_text.insert(tk.END, f"跳过非{input_format}文件: {file_path}\n")
                            continue
                        elif file_ext != f".{input_format}" and not (input_format == "jpg" and file_ext in ['.jpg', '.jpeg']):
                            self.img_log_text.insert(tk.END, f"跳过非{input_format}文件: {file_path}\n")
                            continue
                    
                    try:
                        # 打开图片
                        img = Image.open(file_path)
                        
                        # 如果是PNG带透明通道，并且转为JPG，需要处理背景
                        if img.mode == 'RGBA' and output_format in ['jpg', 'jpeg']:
                            # 创建白色背景
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            # 合并图层
                            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                            img = background
                        
                        # 调整图像大小
                        if resize_enabled and (width or height):
                            current_width, current_height = img.size
                            new_width, new_height = width, height
                            
                            # 如果保持比例且只指定了宽度或高度
                            if self.keep_ratio.get():
                                if width and not height:
                                    ratio = width / current_width
                                    new_height = int(current_height * ratio)
                                elif height and not width:
                                    ratio = height / current_height
                                    new_width = int(current_width * ratio)
                                elif width and height:
                                    # 使用较小的缩放比例以确保图像完全适合指定的尺寸
                                    ratio_width = width / current_width
                                    ratio_height = height / current_height
                                    ratio = min(ratio_width, ratio_height)
                                    new_width = int(current_width * ratio)
                                    new_height = int(current_height * ratio)
                            
                            # 调整大小
                            img = img.resize((new_width, new_height), Image.LANCZOS)
                        
                        # 构建输出文件名
                        output_filename = f"{base_filename}.{output_format}"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        # 如果文件已存在，添加序号
                        counter = 1
                        while os.path.exists(output_path):
                            output_filename = f"{base_filename}_{counter}.{output_format}"
                            output_path = os.path.join(output_dir, output_filename)
                            counter += 1
                        
                        # 根据输出格式保存
                        if output_format in ['jpg', 'jpeg']:
                            img.save(output_path, format='JPEG', quality=quality, optimize=True)
                        elif output_format == 'png':
                            img.save(output_path, format='PNG', optimize=True)
                        elif output_format == 'gif':
                            img.save(output_path, format='GIF')
                        elif output_format == 'bmp':
                            img.save(output_path, format='BMP')
                        elif output_format in ['tiff', 'tif']:
                            img.save(output_path, format='TIFF')
                        else:
                            img.save(output_path)
                        
                        success_count += 1
                        self.img_log_text.insert(tk.END, f"已转换: {os.path.basename(file_path)} -> {output_filename}\n")
                        self.img_log_text.see(tk.END)
                        
                    except Exception as e:
                        self.img_log_text.insert(tk.END, f"转换失败 {os.path.basename(file_path)}: {str(e)}\n")
                        self.img_log_text.see(tk.END)
                    
                    # 更新进度条
                    self.img_progress["value"] = i + 1
                    self.root.update_idletasks()
                
                self.img_log_text.insert(tk.END, f"\n转换完成! 成功转换 {success_count}/{total_files} 个文件\n")
                self.img_log_text.see(tk.END)
                messagebox.showinfo("成功", f"成功转换 {success_count}/{total_files} 个图片文件，保存在: {output_dir}")
                
            except Exception as e:
                self.img_log_text.insert(tk.END, f"错误: {str(e)}\n")
                self.img_log_text.see(tk.END)
                messagebox.showerror("错误", f"转换失败: {str(e)}")
            finally:
                # 重置进度条
                self.img_progress["value"] = 0
        
        # 使用线程执行转换，避免界面卡顿
        threading.Thread(target=conversion_thread).start()
    
    def on_range_change(self, *args):
        """处理页面范围选择变化"""
        if self.range_var.get() == "自定义":
            self.page_range_entry.config(state="normal")
        else:
            self.page_range_entry.config(state="disabled")
            
    def on_layout_mode_change(self, *args):
        """处理版面模式变化"""
        if self.layout_mode.get() == "手动调整":
            self.manual_frame.pack(fill="x", padx=10, pady=5, after=self.file_listbox.master)
        else:
            self.manual_frame.pack_forget()
    
    def add_files(self):
        """添加文件到列表"""
        file_paths = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("PDF和图片", "*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.tif")]
        )
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.file_paths:
                    self.file_paths.append(file_path)
                    self.file_listbox.insert(tk.END, os.path.basename(file_path))
    
    def remove_selected(self):
        """移除选中的文件"""
        selected_indices = self.file_listbox.curselection()
        for index in reversed(selected_indices):
            self.file_listbox.delete(index)
            self.file_paths.pop(index)
    
    def move_item(self, direction):
        """移动列表项"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
            
        index = selected_indices[0]
        if direction == -1 and index > 0:
            # 上移
            self.swap_items(index, index-1)
        elif direction == 1 and index < len(self.file_paths) - 1:
            # 下移
            self.swap_items(index, index+1)
    
    def swap_items(self, pos1, pos2):
        """交换两个列表项"""
        # 交换文件路径
        self.file_paths[pos1], self.file_paths[pos2] = self.file_paths[pos2], self.file_paths[pos1]
        
        # 更新显示
        item1 = self.file_listbox.get(pos1)
        item2 = self.file_listbox.get(pos2)
        self.file_listbox.delete(pos1)
        self.file_listbox.insert(pos1, item2)
        self.file_listbox.delete(pos2)
        self.file_listbox.insert(pos2, item1)
        
        # 保持选中状态
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(pos2)
    
    def clear_list(self):
        """清空文件列表"""
        self.file_listbox.delete(0, tk.END)
        self.file_paths = []
    
    def select_pdf_files(self):
        """选择多个PDF文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf")]
        )
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.pdf_file_paths:
                    self.pdf_file_paths.append(file_path)
                    self.pdf_listbox.insert(tk.END, os.path.basename(file_path))
    
    def select_pdf_folder(self):
        """选择包含PDF文件的文件夹"""
        folder_path = filedialog.askdirectory(title="选择包含PDF文件的文件夹")
        if folder_path:
            # 搜索文件夹中的所有PDF文件
            pdf_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file)
                        pdf_files.append(full_path)
            
            # 添加到列表中
            for file_path in pdf_files:
                if file_path not in self.pdf_file_paths:
                    self.pdf_file_paths.append(file_path)
                    self.pdf_listbox.insert(tk.END, os.path.basename(file_path))
            
            if not pdf_files:
                messagebox.showinfo("提示", "所选文件夹中没有找到PDF文件")
    
    def remove_selected_pdfs(self):
        """移除选中的PDF文件"""
        selected_indices = self.pdf_listbox.curselection()
        for index in reversed(selected_indices):
            self.pdf_listbox.delete(index)
            self.pdf_file_paths.pop(index)
    
    def clear_pdf_list(self):
        """清空PDF文件列表"""
        self.pdf_listbox.delete(0, tk.END)
        self.pdf_file_paths = []
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)
    
    def merge_files(self):
        """合并文件"""
        if len(self.file_paths) < 2:
            messagebox.showwarning("警告", "请至少添加两个文件进行合并")
            return
        
        output_path = filedialog.asksaveasfilename(
            title="保存合并后的PDF",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        
        if not output_path:
            return
            
        try:
            mode = self.layout_mode.get()
            if mode == "原样":
                self.merge_original_size(output_path)
            elif mode == "自动调整":
                self.merge_auto_adjust(output_path)
            else:  # 手动调整
                self.merge_manual_adjust(output_path)
                
            messagebox.showinfo("成功", f"文件已成功合并为: {output_path}")
        except Exception as e:
            messagebox.showerror("错误", f"合并失败: {str(e)}")
    
    def merge_original_size(self, output_path):
        """以原始尺寸合并文件"""
        merger = PdfMerger()
        
        for file_path in self.file_paths:
            if file_path.lower().endswith(('.pdf')):
                # 处理PDF文件
                merger.append(file_path)
            else:
                # 处理图片文件
                img = Image.open(file_path)
                pdf_bytes = io.BytesIO()
                img.convert('RGB').save(pdf_bytes, format='PDF')
                pdf_bytes.seek(0)
                merger.append(pdf_bytes)
        
        merger.write(output_path)
        merger.close()
    
    def merge_auto_adjust(self, output_path):
        """自动调整尺寸合并文件"""
        writer = PdfWriter()
        
        # 获取第一个文件的尺寸作为标准
        standard_width = None
        standard_height = None
        
        # 尝试从第一个PDF获取尺寸
        for file_path in self.file_paths:
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    reader = PdfReader(file)
                    if reader.pages:
                        mediabox = reader.pages[0].mediabox
                        standard_width = mediabox.width
                        standard_height = mediabox.height
                        break
        
        # 如果没有PDF文件，尝试从第一个图片获取尺寸
        if standard_width is None:
            for file_path in self.file_paths:
                if not file_path.lower().endswith('.pdf'):
                    img = Image.open(file_path)
                    standard_width = img.width * 72.0 / 96.0  # 转换为点
                    standard_height = img.height * 72.0 / 96.0
                    break
        
        # 如果仍然没有尺寸，使用A4尺寸
        if standard_width is None:
            standard_width = 595  # A4宽度（点）
            standard_height = 842  # A4高度（点）
        
        # 处理每个文件
        for file_path in self.file_paths:
            if file_path.lower().endswith('.pdf'):
                # 处理PDF文件
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # 创建新页面并调整图像
                    pdf_bytes = io.BytesIO()
                    img.convert('RGB').save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    
                    temp_reader = PdfReader(pdf_bytes)
                    writer.add_page(temp_reader.pages[0])
            else:
                # 处理图片文件
                img = Image.open(file_path)
                pdf_bytes = io.BytesIO()
                img.convert('RGB').save(pdf_bytes, format='PDF')
                pdf_bytes.seek(0)
                
                temp_reader = PdfReader(pdf_bytes)
                writer.add_page(temp_reader.pages[0])
        
        # 保存合并后的文件
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
    def merge_manual_adjust(self, output_path):
        """根据手动设置合并文件"""
        writer = PdfWriter()
        
        # 获取手动设置的页面尺寸
        page_size = self.page_size_var.get()
        width_mm = float(self.width_var.get())
        height_mm = float(self.height_var.get())
        margin_mm = float(self.margin_var.get())
        
        # 转换为点（1英寸=72点=25.4毫米）
        width_pt = width_mm * 72 / 25.4
        height_pt = height_mm * 72 / 25.4
        margin_pt = margin_mm * 72 / 25.4
        
        # 根据页面尺寸设置
        if page_size == "A4":
            width_pt = 595
            height_pt = 842
        elif page_size == "A5":
            width_pt = 420
            height_pt = 595
        elif page_size == "Letter":
            width_pt = 612
            height_pt = 792
        elif page_size == "Legal":
            width_pt = 612
            height_pt = 1008
        
        # 处理每个文件
        for file_path in self.file_paths:
            if file_path.lower().endswith('.pdf'):
                # 处理PDF文件
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # 调整图像大小以适应页面，考虑边距
                    available_width = width_pt - 2 * margin_pt
                    available_height = height_pt - 2 * margin_pt
                    
                    # 计算缩放比例
                    img_width, img_height = img.size
                    scale = min(available_width / img_width, available_height / img_height)
                    
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    # 调整图像大小
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # 创建空白页面并粘贴图像
                    new_img = Image.new("RGB", (int(width_pt), int(height_pt)), "white")
                    paste_x = int((width_pt - new_width) / 2)
                    paste_y = int((height_pt - new_height) / 2)
                    new_img.paste(img, (paste_x, paste_y))
                    
                    # 转换为PDF页面
                    pdf_bytes = io.BytesIO()
                    new_img.save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    
                    temp_reader = PdfReader(pdf_bytes)
                    writer.add_page(temp_reader.pages[0])
            else:
                # 处理图片文件
                img = Image.open(file_path)
                
                # 调整图像大小以适应页面，考虑边距
                available_width = width_pt - 2 * margin_pt
                available_height = height_pt - 2 * margin_pt
                
                # 计算缩放比例
                img_width, img_height = img.size
                scale = min(available_width / img_width, available_height / img_height)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # 调整图像大小
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # 创建空白页面并粘贴图像
                new_img = Image.new("RGB", (int(width_pt), int(height_pt)), "white")
                paste_x = int((width_pt - new_width) / 2)
                paste_y = int((height_pt - new_height) / 2)
                new_img.paste(img, (paste_x, paste_y))
                
                # 转换为PDF页面
                pdf_bytes = io.BytesIO()
                new_img.save(pdf_bytes, format='PDF')
                pdf_bytes.seek(0)
                
                temp_reader = PdfReader(pdf_bytes)
                writer.add_page(temp_reader.pages[0])
        
        # 保存合并后的文件
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
    def convert_pdf_to_images(self):
        """将PDF转换为图片"""
        if not self.pdf_file_paths:
            messagebox.showwarning("警告", "请选择至少一个PDF文件")
            return
        
        output_dir = self.output_dir.get()
        
        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 获取转换参数
        output_format = self.output_format.get().lower()
        dpi = int(self.dpi_var.get())
        
        # 获取页面范围
        page_range_mode = self.range_var.get()
        
        # 准备线程
        def conversion_thread():
            try:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, "开始批量转换...\n")
                
                total_files = len(self.pdf_file_paths)
                total_pages_converted = 0
                
                # 对每个文件进行处理
                for file_index, pdf_path in enumerate(self.pdf_file_paths):
                    # 获取不带扩展名的文件名
                    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
                    
                    self.log_text.insert(tk.END, f"\n处理文件 {file_index+1}/{total_files}: {os.path.basename(pdf_path)}\n")
                    self.log_text.see(tk.END)
                    
                    # 打开PDF
                    try:
                        pdf_doc = fitz.open(pdf_path)
                        total_pages = len(pdf_doc)
                    except Exception as e:
                        self.log_text.insert(tk.END, f"错误: 无法打开 {pdf_path}: {str(e)}\n")
                        self.log_text.see(tk.END)
                        continue
                    
                    # 确定需要转换的页面
                    pages_to_convert = []
                    if page_range_mode == "全部":
                        pages_to_convert = range(total_pages)
                    else:
                        # 解析页码范围，例如 "1-3,5,7-9"
                        page_range_str = self.page_range.get()
                        
                        try:
                            for part in page_range_str.split(','):
                                part = part.strip()
                                if '-' in part:
                                    start, end = map(int, part.split('-'))
                                    # PDF页码通常从1开始，但PyMuPDF从0开始
                                    pages_to_convert.extend(range(start-1, end))
                                else:
                                    # 单页
                                    pages_to_convert.append(int(part)-1)
                        except ValueError:
                            self.log_text.insert(tk.END, "错误: 页码范围格式不正确，将转换全部页面\n")
                            self.log_text.see(tk.END)
                            pages_to_convert = range(total_pages)
                    
                    # 设置当前文件的进度条
                    self.progress["maximum"] = len(pages_to_convert)
                    self.progress["value"] = 0
                    
                    # 转换每一页
                    for i, page_num in enumerate(pages_to_convert):
                        if page_num >= total_pages or page_num < 0:
                            self.log_text.insert(tk.END, f"跳过无效页码 {page_num+1}\n")
                            self.log_text.see(tk.END)
                            continue
                        
                        # 获取页面
                        page = pdf_doc.load_page(page_num)
                        
                        # 设置渲染参数
                        matrix = fitz.Matrix(dpi/72, dpi/72)
                        pix = page.get_pixmap(matrix=matrix)
                        
                        # 转换为PIL图像
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        # 使用"原文件名_页码.格式"命名输出文件
                        filename = f"{base_filename}_{page_num+1}.{output_format}"
                        output_path = os.path.join(output_dir, filename)
                        
                        # 保存图像
                        img.save(output_path)
                        
                        # 更新日志
                        self.log_text.insert(tk.END, f"页面 {page_num+1} 已转换为 {filename}\n")
                        self.log_text.see(tk.END)
                        
                        # 更新进度条
                        self.progress["value"] = i + 1
                        self.root.update_idletasks()
                        
                        total_pages_converted += 1
                    
                    # 关闭当前PDF文档
                    pdf_doc.close()
                
                self.log_text.insert(tk.END, f"\n批量转换完成! 共处理 {total_files} 个文件, {total_pages_converted} 页\n")
                self.log_text.see(tk.END)
                messagebox.showinfo("成功", f"共处理 {total_files} 个PDF文件, {total_pages_converted} 页，保存在: {output_dir}")
                
            except Exception as e:
                self.log_text.insert(tk.END, f"错误: {str(e)}\n")
                self.log_text.see(tk.END)
                messagebox.showerror("错误", f"转换失败: {str(e)}")
            finally:
                # 重置进度条
                self.progress["value"] = 0
        
        # 使用线程执行转换，避免界面卡顿
        threading.Thread(target=conversion_thread).start()

if __name__ == "__main__":
    # 检查是否可以使用主题化的Tk
    if HAS_THEMED_TK:
        root = ThemedTk(theme="arc")
    else:
        root = tk.Tk()
    
    app = PDFToolGUI(root)
    root.mainloop()
