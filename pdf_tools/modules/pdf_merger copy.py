import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import fitz  # PyMuPDF
import io

class MergePDFTab:
    """PDF合并标签页类"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.style = theme_manager.style
        self.file_paths = []
        self.layout_mode = tk.StringVar(value="原样")
        self.force_a4 = tk.BooleanVar(value=False)  # 强制使用A4纸张大小选项
        self.page_orientation = tk.StringVar(value="纵向")  # 页面方向选项
        self.file_orientations = {}  # 存储每个文件的页面方向
        
        # 创建界面
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        
    def create_widgets(self):
        """创建合并PDF标签页的组件"""
        # 版面模式选择 - 使用更美观的选项卡样式
        mode_frame = ttk.LabelFrame(self.frame, text="版面模式")
        mode_frame.pack(fill="x", padx=15, pady=10)
        
        modes = ["原样", "自动调整", "手动调整"]
        mode_container = ttk.Frame(mode_frame)
        mode_container.pack(fill="x", padx=5, pady=8)
        
        for mode in modes:
            ttk.Radiobutton(mode_container, text=mode, value=mode,
                          variable=self.layout_mode).pack(side=tk.LEFT, padx=25, pady=5)
        
        # 原样模式下的A4选项
        self.original_options_frame = ttk.Frame(mode_frame)
        self.original_options_frame.pack(fill="x", padx=5, pady=0)
        ttk.Checkbutton(self.original_options_frame, text="强制使用A4纸张大小", 
                      variable=self.force_a4).pack(side=tk.LEFT, padx=25, pady=5)
        
        # 页面方向选择，增加混合选项
        orientation_frame = ttk.Frame(self.original_options_frame)
        orientation_frame.pack(side=tk.LEFT, padx=25, pady=5)
        ttk.Label(orientation_frame, text="页面方向:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(orientation_frame, text="纵向", value="纵向", 
                       variable=self.page_orientation).pack(side=tk.LEFT)
        ttk.Radiobutton(orientation_frame, text="横向", value="横向", 
                       variable=self.page_orientation).pack(side=tk.LEFT)
        ttk.Radiobutton(orientation_frame, text="混合", value="混合", 
                       variable=self.page_orientation,
                       command=self.show_orientation_manager).pack(side=tk.LEFT)
        
        # 文件列表
        file_frame = ttk.LabelFrame(self.frame, text="文件列表")
        file_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 文件列表显示 - 添加边框和颜色
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, 
                                      font=("Arial", 10), 
                                      bg="white", fg=self.theme_manager.text_color,
                                      selectbackground=self.theme_manager.accent_color,
                                      relief=tk.SUNKEN, bd=1,
                                      highlightthickness=1)
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=8, pady=8)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y", pady=8, padx=(0, 8))
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # 文件操作按钮
        file_btn_frame = ttk.Frame(self.frame)
        file_btn_frame.pack(fill="x", padx=15, pady=10)
        
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
        
        # 手动调整面板（默认隐藏）
        self.manual_frame = ttk.LabelFrame(self.frame, text="手动调整设置")
        
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
        
        # 合并按钮和进度条
        merge_btn_frame = ttk.Frame(self.frame)
        merge_btn_frame.pack(fill="x", padx=15, pady=15)
        
        # 添加进度条
        self.progress = ttk.Progressbar(merge_btn_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", side=tk.LEFT, expand=True, padx=8, pady=5)
        
        ttk.Button(merge_btn_frame, text="合并文件", command=self.merge_files, 
                 style="Primary.TButton").pack(side=tk.RIGHT, padx=8, pady=5)
        
        # 绑定版面模式变化事件
        self.layout_mode.trace("w", self.on_layout_mode_change)
        
        # 添加状态标签
        self.status_label = ttk.Label(self.frame, text="就绪")
        self.status_label.pack(fill="x", padx=15, pady=0, side=tk.BOTTOM)
    
    def show_orientation_manager(self):
        """显示混合页面方向管理器"""
        if not self.file_paths:
            messagebox.showinfo("提示", "请先添加文件后再设置混合页面方向")
            return
            
        # 创建一个新窗口来管理每个文件的页面方向
        orientation_window = tk.Toplevel(self.parent)
        orientation_window.title("设置页面方向")
        orientation_window.geometry("500x400")
        orientation_window.transient(self.parent)  # 设置为父窗口的临时窗口
        orientation_window.grab_set()  # 模态窗口
        
        # 创建说明标签
        ttk.Label(orientation_window, 
                 text="请为每个文件选择页面方向",
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # 创建滚动视图
        container = ttk.Frame(orientation_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 为每个文件创建方向选择界面
        for i, file_path in enumerate(self.file_paths):
            file_frame = ttk.Frame(scrollable_frame)
            file_frame.pack(fill="x", pady=5)
            
            file_name = os.path.basename(file_path)
            # 显示文件名，限制长度以防止UI溢出
            if len(file_name) > 30:
                display_name = file_name[:27] + "..."
            else:
                display_name = file_name
                
            ttk.Label(file_frame, text=display_name).pack(side=tk.LEFT, padx=5)
            
            # 获取该文件当前的方向设置，默认为纵向
            current_orientation = self.file_orientations.get(file_path, "纵向")
            orientation_var = tk.StringVar(value=current_orientation)
            
            ttk.Radiobutton(file_frame, text="纵向", value="纵向", 
                           variable=orientation_var).pack(side=tk.LEFT, padx=10)
            ttk.Radiobutton(file_frame, text="横向", value="横向", 
                           variable=orientation_var).pack(side=tk.LEFT, padx=10)
            
            # 将变量存储到字典中以便后续使用
            self.file_orientations[file_path] = orientation_var.get()
            
            # 添加跟踪，当选项改变时更新字典
            def update_orientation(var, index, mode, path=file_path, orient_var=orientation_var):
                self.file_orientations[path] = orient_var.get()
            
            orientation_var.trace_add("write", update_orientation)
        
        # 确定按钮
        ttk.Button(orientation_window, text="确定", 
                  command=orientation_window.destroy).pack(pady=15)
    
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
                    # 默认使用当前选中的页面方向
                    if self.page_orientation.get() != "混合":
                        self.file_orientations[file_path] = self.page_orientation.get()
    
    def remove_selected(self):
        """移除选中的文件"""
        selected_indices = self.file_listbox.curselection()
        for index in reversed(selected_indices):
            file_path = self.file_paths[index]
            self.file_listbox.delete(index)
            self.file_paths.pop(index)
            # 同时移除对应的方向设置
            if file_path in self.file_orientations:
                del self.file_orientations[file_path]
    
    def clear_list(self):
        """清空文件列表"""
        self.file_listbox.delete(0, tk.END)
        self.file_paths = []
        self.file_orientations = {}  # 清空方向设置
    
    def merge_to_a4_size(self, output_path):
        """以A4尺寸合并文件，支持混合页面方向"""
        # 更新进度条和状态
        total_pages = 0
        for file_path in self.file_paths:
            if file_path.lower().endswith('.pdf'):
                try:
                    pdf_doc = fitz.open(file_path)
                    total_pages += len(pdf_doc)
                    pdf_doc.close()
                except Exception as e:
                    error_msg = f"无法打开文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    raise Exception(f"文件 '{os.path.basename(file_path)}' 不是有效的PDF文件")
            else:
                total_pages += 1
        
        self.parent.after(0, lambda: self.progress.config(maximum=total_pages))
        processed_pages = 0
        
        # 创建一个新的输出PDF文档
        output_pdf = fitz.open()
        
        for file_path in self.file_paths:
            self.parent.after(0, lambda p=file_path: self.status_label.config(text=f"处理: {os.path.basename(p)}"))
            
            # 确定当前文件的页面方向
            # 如果是混合模式，从file_orientations获取方向；否则使用全局方向
            is_landscape = False
            if self.page_orientation.get() == "混合":
                file_orientation = self.file_orientations.get(file_path, "纵向")
                is_landscape = file_orientation == "横向"
            else:
                is_landscape = self.page_orientation.get() == "横向"
            
            # 根据方向设置A4尺寸（精确值）
            if is_landscape:
                a4_width = 841.89  # 297mm in points (精确值)
                a4_height = 595.28  # 210mm in points (精确值)
            else:
                a4_width = 595.28  # 210mm in points (精确值)
                a4_height = 841.89  # 297mm in points (精确值)
            
            # PDF文件处理
            if file_path.lower().endswith('.pdf'):
                try:
                    pdf_doc = fitz.open(file_path)
                    for page_num in range(len(pdf_doc)):
                        # 创建新A4页面
                        # 使用整数值避免浮点数问题
                        new_page = output_pdf.new_page(width=int(a4_width), height=int(a4_height))
                        
                        # 从源文档获取页面
                        src_page = pdf_doc[page_num]
                        
                        # 计算缩放比例以适应A4，同时保持内容
                        src_rect = src_page.rect
                        dest_rect = new_page.rect
                        
                        # 计算合适的缩放比例
                        scale_x = dest_rect.width / src_rect.width
                        scale_y = dest_rect.height / src_rect.height
                        scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
                        
                        # 计算居中偏移量
                        offset_x = (dest_rect.width - src_rect.width * scale) / 2
                        offset_y = (dest_rect.height - src_rect.height * scale) / 2
                        
                        # 创建转换矩阵
                        matrix = fitz.Matrix(scale, scale).preTranslate(offset_x/scale, offset_y/scale)
                        
                        # 将源文档内容绘制到新页面上
                        new_page.show_pdf_page(dest_rect, pdf_doc, page_num, matrix=matrix)
                        
                        # 更新进度
                        processed_pages += 1
                        self.parent.after(0, lambda v=processed_pages: self.progress.config(value=v))
                    
                    pdf_doc.close()
                except Exception as e:
                    error_msg = f"处理PDF文件时出错 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
                    
            # 图片文件处理
            else:
                try:
                    # 打开图像
                    img = Image.open(file_path)
                    if hasattr(img, 'draft'):
                        img.draft(None, img.size)  # 取消草图模式
                    
                    # 如果有透明通道，添加白色背景
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    
                    # 计算图片与A4页面的比例
                    img_width, img_height = img.size
                    img_ratio = img_width / img_height
                    a4_ratio = a4_width / a4_height
                    
                    # 计算适当的缩放以适应A4
                    if img_ratio > a4_ratio:  # 图片更宽
                        new_width = int(a4_width - 40)  # 留出边距，确保转为整数
                        new_height = int(new_width / img_ratio)
                    else:  # 图片更高或等比例
                        new_height = int(a4_height - 40)  # 留出边距，确保转为整数
                        new_width = int(new_height * img_ratio)
                    
                    # 调整图像大小
                    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # 将图像转换为临时PDF
                    temp_pdf_path = f"{output_path}.temp_img.pdf"
                    
                    # 创建A4大小的临时PDF
                    temp_pdf = fitz.open()
                    # 使用整数值避免浮点数问题
                    temp_page = temp_pdf.new_page(width=int(a4_width), height=int(a4_height))
                    
                    # 将图像数据转换为PNG字节流
                    img_bytes = io.BytesIO()
                    img_resized.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    # 插入图像到中心位置，确保使用整数坐标
                    rect = fitz.Rect(
                        int((a4_width - new_width) / 2),
                        int((a4_height - new_height) / 2),
                        int((a4_width + new_width) / 2),
                        int((a4_height + new_height) / 2)
                    )
                    temp_page.insert_image(rect, stream=img_bytes.getvalue())
                    
                    # 保存临时PDF
                    temp_pdf.save(temp_pdf_path)
                    temp_pdf.close()
                    
                    # 将临时PDF的页面添加到输出PDF
                    temp_doc = fitz.open(temp_pdf_path)
                    output_pdf.insert_pdf(temp_doc)
                    temp_doc.close()
                    
                    # 删除临时文件
                    os.remove(temp_pdf_path)
                    
                    # 更新进度
                    processed_pages += 1
                    self.parent.after(0, lambda v=processed_pages: self.progress.config(value=v))
                    
                except Exception as e:
                    error_msg = f"处理图片文件时出错 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
        
        # 保存最终合并后的PDF
        output_pdf.save(output_path)
        output_pdf.close()