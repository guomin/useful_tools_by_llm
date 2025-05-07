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
        self.page_orientation = tk.StringVar(value="纵向")  # 新增：页面方向选项
        
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
        
        # 新增：页面方向选择
        orientation_frame = ttk.Frame(self.original_options_frame)
        orientation_frame.pack(side=tk.LEFT, padx=25, pady=5)
        ttk.Label(orientation_frame, text="页面方向:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(orientation_frame, text="纵向", value="纵向", 
                       variable=self.page_orientation).pack(side=tk.LEFT)
        ttk.Radiobutton(orientation_frame, text="横向", value="横向", 
                       variable=self.page_orientation).pack(side=tk.LEFT)
        
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
        
    def on_layout_mode_change(self, *args):
        """处理版面模式变化"""
        if self.layout_mode.get() == "手动调整":
            self.manual_frame.pack(fill="x", padx=10, pady=5, after=self.file_listbox.master)
        else:
            self.manual_frame.pack_forget()
    
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
        
        # 更新界面状态
        self.status_label.config(text="正在合并文件...")
        self.progress["value"] = 0
        
        # 使用线程执行合并，避免界面卡顿
        def merge_thread():
            try:
                mode = self.layout_mode.get()
                if mode == "原样":
                    self.merge_original_size(output_path)
                elif mode == "自动调整":
                    self.merge_auto_adjust(output_path)
                else:  # 手动调整
                    self.merge_manual_adjust(output_path)
                
                # 合并完成后在主线程更新UI
                self.parent.after(0, lambda path=output_path: self.show_success_message(path))
            except Exception as error:
                # 修复：将异常变量传递给lambda函数
                error_msg = str(error)  # 在当前作用域捕获错误消息
                self.parent.after(0, lambda msg=error_msg: self.show_error_message(msg))
            finally:
                # 重置进度条和状态
                self.parent.after(0, self.reset_ui)
        
        # 启动线程执行合并
        threading.Thread(target=merge_thread).start()
    
    def show_success_message(self, output_path):
        """显示成功消息"""
        self.status_label.config(text="合并完成")
        messagebox.showinfo("成功", f"文件已成功合并为: {output_path}")
    
    def show_error_message(self, error_msg):
        """显示错误消息"""
        self.status_label.config(text="合并失败")
        messagebox.showerror("错误", f"合并失败: {error_msg}")
    
    def reset_ui(self):
        """重置界面状态"""
        self.progress["value"] = 0
        self.status_label.config(text="就绪")
    
    def merge_original_size(self, output_path):
        """以原始尺寸合并文件"""
        # 检查是否强制使用A4尺寸
        if self.force_a4.get():
            # 使用修改后的方法合并为A4尺寸
            self.merge_to_a4_size(output_path)
            return
        
        # 原始的合并代码
        merger = PdfMerger()
        
        # 更新进度条设置
        total_files = len(self.file_paths)
        self.parent.after(0, lambda: self.progress.config(maximum=total_files))
        
        for i, file_path in enumerate(self.file_paths):
            # 更新进度条
            self.parent.after(0, lambda v=i+1: self.progress.config(value=v))
            self.parent.after(0, lambda p=file_path: self.status_label.config(text=f"处理: {os.path.basename(p)}"))
            
            if file_path.lower().endswith(('.pdf')):
                # 处理PDF文件
                try:
                    # 尝试打开PDF以验证它是有效的
                    with open(file_path, 'rb') as f:
                        reader = PdfReader(f)
                        # 如果能读取页面，则PDF文件有效
                        _ = len(reader.pages)
                    merger.append(file_path)
                except Exception as e:
                    error_msg = f"'{os.path.basename(file_path)}' 不是有效的PDF文件: {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    raise Exception(f"文件 '{os.path.basename(file_path)}' 不是有效的PDF文件")
            else:
                # 处理图片文件
                try:
                    img = Image.open(file_path)
                    pdf_bytes = io.BytesIO()
                    
                    if img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    
                    dpi = (300, 300)
                    if hasattr(img, 'info') and 'dpi' in img.info:
                        original_dpi = img.info['dpi']
                        dpi = (max(original_dpi[0], 300), max(original_dpi[1], 300))
                    
                    img.convert('RGB').save(pdf_bytes, format='PDF', resolution=dpi[0], quality=100)
                    pdf_bytes.seek(0)
                    merger.append(pdf_bytes)
                except Exception as e:
                    error_msg = f"无法打开图片文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
        
        # 最终保存
        merger.write(output_path)
        merger.close()
    
    def merge_to_a4_size(self, output_path):
        """以A4尺寸合并文件，保持内容原样"""
        # A4尺寸（点）- 确保使用准确的标准尺寸
        is_landscape = self.page_orientation.get() == "横向"
        
        # 根据方向设置A4尺寸（精确值）
        if is_landscape:
            a4_width = 841.89  # 297mm in points (精确值)
            a4_height = 595.28  # 210mm in points (精确值)
        else:
            a4_width = 595.28  # 210mm in points (精确值)
            a4_height = 841.89  # 297mm in points (精确值)
        
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
    
    def merge_auto_adjust(self, output_path):
        """自动调整尺寸合并文件"""
        writer = PdfWriter()
        
        total_files = len(self.file_paths)
        total_pages = 0
        for file_path in self.file_paths:
            if file_path.lower().endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as file:
                        reader = PdfReader(file)
                        total_pages += len(reader.pages)
                except Exception as e:
                    error_msg = f"无法打开PDF文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    raise Exception(f"文件 '{os.path.basename(file_path)}' 不是有效的PDF文件")
            else:
                total_pages += 1
        
        self.parent.after(0, lambda: self.progress.config(maximum=total_pages))
        processed_pages = 0
        
        for file_path in self.file_paths:
            self.parent.after(0, lambda p=file_path: self.status_label.config(text=f"处理: {os.path.basename(p)}"))
            
            if file_path.lower().endswith('.pdf'):
                try:
                    doc = fitz.open(file_path)
                except Exception as e:
                    error_msg = f"无法打开PDF文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    pdf_bytes = io.BytesIO()
                    img.convert('RGB').save(pdf_bytes, format='PDF', resolution=300, quality=100)
                    pdf_bytes.seek(0)
                    
                    temp_reader = PdfReader(pdf_bytes)
                    writer.add_page(temp_reader.pages[0])
                    
                    processed_pages += 1
                    self.parent.after(0, lambda v=processed_pages: self.progress.config(value=v))
            else:
                try:
                    img = Image.open(file_path)
                except Exception as e:
                    error_msg = f"无法打开图片文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
                
                pdf_bytes = io.BytesIO()
                img.convert('RGB').save(pdf_bytes, format='PDF', resolution=300, quality=100)
                pdf_bytes.seek(0)
                
                temp_reader = PdfReader(pdf_bytes)
                writer.add_page(temp_reader.pages[0])
                
                processed_pages += 1
                self.parent.after(0, lambda v=processed_pages: self.progress.config(value=v))
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
    def merge_manual_adjust(self, output_path):
        """根据手动设置合并文件"""
        writer = PdfWriter()
        
        page_size = self.page_size_var.get()
        width_mm = float(self.width_var.get())
        height_mm = float(self.height_var.get())
        margin_mm = float(self.margin_var.get())
        
        width_pt = width_mm * 72 / 25.4
        height_pt = height_mm * 72 / 25.4
        margin_pt = margin_mm * 72 / 25.4
        
        is_landscape = self.page_orientation.get() == "横向"
        
        if page_size == "A4":
            if is_landscape:
                width_pt = 841.89
                height_pt = 595.28
            else:
                width_pt = 595.28
                height_pt = 841.89
        elif page_size == "A5":
            if is_landscape:
                width_pt = 595.28
                height_pt = 419.53
            else:
                width_pt = 419.53
                height_pt = 595.28
        elif page_size == "Letter":
            if is_landscape:
                width_pt = 792.0
                height_pt = 612.0
            else:
                width_pt = 612.0
                height_pt = 792.0
        elif page_size == "Legal":
            if is_landscape:
                width_pt = 1008.0
                height_pt = 612.0
            else:
                width_pt = 612.0
                height_pt = 1008.0
        
        total_files = len(self.file_paths)
        total_pages = 0
        for file_path in self.file_paths:
            if file_path.lower().endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as file:
                        reader = PdfReader(file)
                        total_pages += len(reader.pages)
                except Exception as e:
                    error_msg = f"无法打开PDF文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    raise Exception(f"文件 '{os.path.basename(file_path)}' 不是有效的PDF文件")
            else:
                total_pages += 1
        
        self.parent.after(0, lambda: self.progress.config(maximum=total_pages))
        processed_pages = 0
        
        for file_path in self.file_paths:
            self.parent.after(0, lambda p=file_path: self.status_label.config(text=f"处理: {os.path.basename(p)}"))
            
            if file_path.lower().endswith('.pdf'):
                try:
                    doc = fitz.open(file_path)
                except Exception as e:
                    error_msg = f"无法打开PDF文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    available_width = width_pt - 2 * margin_pt
                    available_height = height_pt - 2 * margin_pt
                    
                    img_width, img_height = img.size
                    scale = min(available_width / img_width, available_height / img_height)
                    
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    new_img = Image.new("RGB", (int(width_pt), int(height_pt)), "white")
                    paste_x = int((width_pt - new_width) / 2)
                    paste_y = int((height_pt - new_height) / 2)
                    new_img.paste(img, (paste_x, paste_y))
                    
                    pdf_bytes = io.BytesIO()
                    new_img.save(pdf_bytes, format='PDF', resolution=300, quality=100)
                    pdf_bytes.seek(0)
                    
                    temp_reader = PdfReader(pdf_bytes)
                    writer.add_page(temp_reader.pages[0])
                    
                    processed_pages += 1
                    self.parent.after(0, lambda v=processed_pages: self.progress.config(value=v))
            else:
                try:
                    img = Image.open(file_path)
                except Exception as e:
                    error_msg = f"无法打开图片文件 '{os.path.basename(file_path)}': {str(e)}"
                    self.parent.after(0, lambda msg=error_msg: messagebox.showerror("错误", msg))
                    continue
                
                available_width = width_pt - 2 * margin_pt
                available_height = height_pt - 2 * margin_pt
                
                img_width, img_height = img.size
                scale = min(available_width / img_width, available_height / img_height)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
                new_img = Image.new("RGB", (int(width_pt), int(height_pt)), "white")
                paste_x = int((width_pt - new_width) / 2)
                paste_y = int((height_pt - new_height) / 2)
                new_img.paste(img, (paste_x, paste_y))
                
                pdf_bytes = io.BytesIO()
                new_img.save(pdf_bytes, format='PDF', resolution=300, quality=100)
                pdf_bytes.seek(0)
                
                temp_reader = PdfReader(pdf_bytes)
                writer.add_page(temp_reader.pages[0])
                
                processed_pages += 1
                self.parent.after(0, lambda v=processed_pages: self.progress.config(value=v))
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)