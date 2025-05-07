import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import fitz  # PyMuPDF
import io
import tempfile
import shutil
import time

class PDFCompressorTab:
    def __init__(self, parent):
        self.parent = parent
        
        # 初始化PDF文件路径列表
        self.pdf_file_paths = []
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置PDF压缩页面"""
        # PDF文件选择
        select_frame = ttk.Frame(self.frame)
        select_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(select_frame, text="PDF文件:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # 按钮组来选择PDF文件和文件夹
        buttons_frame = ttk.Frame(select_frame)
        buttons_frame.pack(side=tk.LEFT, fill="x", expand=True)
        
        ttk.Button(buttons_frame, text="选择文件", command=self.select_pdf_files).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="选择文件夹", command=self.select_pdf_folder).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="清空列表", command=self.clear_pdf_list).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 文件列表显示区域
        file_list_frame = ttk.LabelFrame(self.frame, text="PDF文件列表")
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
        
        # 压缩设置区域
        settings_frame = ttk.LabelFrame(self.frame, text="压缩设置")
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # 压缩级别
        level_frame = ttk.Frame(settings_frame)
        level_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(level_frame, text="压缩级别:").pack(side=tk.LEFT, padx=5, pady=5)
        self.compression_level = tk.StringVar(value="标准")
        levels = ["低", "标准", "高", "最高"]
        ttk.Combobox(level_frame, textvariable=self.compression_level, values=levels, width=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(level_frame, text="图像DPI:").pack(side=tk.LEFT, padx=20, pady=5)
        self.dpi_var = tk.StringVar(value="150")
        ttk.Entry(level_frame, textvariable=self.dpi_var, width=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 图像质量设置
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(quality_frame, text="图像质量(1-100):").pack(side=tk.LEFT, padx=5, pady=5)
        self.quality_var = tk.StringVar(value="75")
        ttk.Entry(quality_frame, textvariable=self.quality_var, width=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 优化选项
        options_frame = ttk.Frame(settings_frame)
        options_frame.pack(fill="x", padx=5, pady=5)
        
        self.optimize_images = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="优化图像", variable=self.optimize_images).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.remove_metadata = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="移除元数据", variable=self.remove_metadata).pack(side=tk.LEFT, padx=20, pady=5)
        
        self.keep_page_size = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="保持页面尺寸", variable=self.keep_page_size).pack(side=tk.LEFT, padx=20, pady=5)
        
        # 输出设置
        output_frame = ttk.Frame(self.frame)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(output_frame, text="输出方式:").pack(side=tk.LEFT, padx=5, pady=5)
        self.output_mode = tk.StringVar(value="新文件")
        ttk.Radiobutton(output_frame, text="生成新文件", value="新文件", variable=self.output_mode).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Radiobutton(output_frame, text="替换原文件", value="替换", variable=self.output_mode).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 输出目录
        output_dir_frame = ttk.Frame(self.frame)
        output_dir_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_dir_frame, text="输出目录:").pack(side=tk.LEFT, padx=5, pady=5)
        self.output_dir = tk.StringVar()
        self.output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir, width=50)
        self.output_dir_entry.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        self.output_dir_button = ttk.Button(output_dir_frame, text="浏览", command=self.select_output_dir)
        self.output_dir_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 绑定输出方式变化事件
        self.output_mode.trace("w", self.on_output_mode_change)
        
        # 压缩按钮和进度条
        action_frame = ttk.Frame(self.frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress = ttk.Progressbar(action_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", side=tk.LEFT, expand=True, padx=5, pady=5)
        
        ttk.Button(action_frame, text="压缩", command=self.compress_pdfs, style="Primary.TButton").pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.frame, text="处理日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = ScrolledText(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 初始设置：如果选择替换原文件，禁用输出目录
        if self.output_mode.get() == "替换":
            self.output_dir_entry.configure(state="disabled")
            self.output_dir_button.configure(state="disabled")
    
    def on_output_mode_change(self, *args):
        """处理输出方式变化"""
        if self.output_mode.get() == "新文件":
            self.output_dir_entry.configure(state="normal")
            self.output_dir_button.configure(state="normal")
        else:
            self.output_dir_entry.configure(state="disabled")
            self.output_dir_button.configure(state="disabled")
    
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
    
    def get_compression_params(self):
        """根据选择的压缩级别返回压缩参数"""
        # 获取界面选择的压缩级别
        level = self.compression_level.get()
        image_quality = int(self.quality_var.get())
        image_dpi = int(self.dpi_var.get())
        
        # 根据压缩级别调整参数
        if level == "低":
            image_dpi = max(image_dpi, 200)
            image_quality = max(image_quality, 85)
        elif level == "标准":
            # 使用界面设置的默认值
            pass
        elif level == "高":
            image_dpi = min(image_dpi, 120)
            image_quality = min(image_quality, 65)
        elif level == "最高":
            image_dpi = min(image_dpi, 96)
            image_quality = min(image_quality, 45)
        
        return {
            "image_quality": image_quality,
            "image_dpi": image_dpi,
            "optimize_images": self.optimize_images.get(),
            "remove_metadata": self.remove_metadata.get(),
            "keep_page_size": self.keep_page_size.get()
        }
    
    def compress_pdfs(self):
        """压缩PDF文件"""
        if not self.pdf_file_paths:
            messagebox.showwarning("警告", "请选择至少一个PDF文件")
            return
        
        # 如果是生成新文件，检查输出目录
        if self.output_mode.get() == "新文件":
            output_dir = self.output_dir.get()
            if not output_dir:
                messagebox.showwarning("警告", "请选择输出目录")
                return
            
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except Exception as e:
                    messagebox.showerror("错误", f"无法创建输出目录: {str(e)}")
                    return
        
        # 获取压缩参数
        compression_params = self.get_compression_params()
        
        # 准备线程
        def compression_thread():
            try:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, "开始压缩PDF文件...\n")
                
                total_files = len(self.pdf_file_paths)
                processed_files = 0
                success_count = 0
                total_size_before = 0
                total_size_after = 0
                
                # 设置进度条
                self.progress["maximum"] = total_files
                self.progress["value"] = 0
                
                # 处理每个文件
                for file_index, pdf_path in enumerate(self.pdf_file_paths):
                    try:
                        self.log_text.insert(tk.END, f"\n处理文件 [{file_index+1}/{total_files}]: {os.path.basename(pdf_path)}\n")
                        self.log_text.see(tk.END)
                        
                        # 记录原始文件大小
                        size_before = os.path.getsize(pdf_path)
                        total_size_before += size_before
                        self.log_text.insert(tk.END, f"原始大小: {self.format_size(size_before)}\n")
                        
                        # 确定输出文件路径
                        if self.output_mode.get() == "新文件":
                            output_dir = self.output_dir.get()
                            output_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_compressed.pdf"
                            output_path = os.path.join(output_dir, output_filename)
                        else:  # 替换原文件
                            output_path = f"{pdf_path}.temp.pdf"
                        
                        # 压缩PDF
                        start_time = time.time()
                        self.compress_pdf_file(pdf_path, output_path, compression_params)
                        end_time = time.time()
                        
                        # 获取压缩后的文件大小
                        if os.path.exists(output_path):
                            size_after = os.path.getsize(output_path)
                            total_size_after += size_after
                            
                            # 计算压缩比
                            if size_before > 0:
                                reduction_percent = ((size_before - size_after) / size_before) * 100
                                self.log_text.insert(tk.END, f"压缩后大小: {self.format_size(size_after)} "
                                                           f"(减小了 {reduction_percent:.2f}%)\n")
                                self.log_text.insert(tk.END, f"处理用时: {end_time - start_time:.2f} 秒\n")
                            
                            # 如果是替换原文件模式，进行替换
                            if self.output_mode.get() == "替换":
                                # 创建原文件的备份
                                backup_path = f"{pdf_path}.bak"
                                try:
                                    shutil.copy2(pdf_path, backup_path)
                                    # 替换原文件
                                    os.remove(pdf_path)
                                    os.rename(output_path, pdf_path)
                                    # 删除备份
                                    os.remove(backup_path)
                                except Exception as e:
                                    self.log_text.insert(tk.END, f"替换文件时出错: {str(e)}\n")
                                    # 尝试恢复原文件
                                    if os.path.exists(backup_path):
                                        try:
                                            if not os.path.exists(pdf_path):
                                                os.rename(backup_path, pdf_path)
                                            else:
                                                os.remove(backup_path)
                                        except:
                                            pass
                                    continue
                            
                            success_count += 1
                    except Exception as e:
                        self.log_text.insert(tk.END, f"处理文件时出错: {str(e)}\n")
                    
                    # 更新进度条
                    processed_files += 1
                    self.progress["value"] = processed_files
                    self.parent.update_idletasks()
                
                # 显示总体结果
                self.log_text.insert(tk.END, f"\n压缩完成! 成功处理 {success_count}/{total_files} 个文件\n")
                
                if success_count > 0:
                    # 计算总体压缩比
                    if total_size_before > 0:
                        total_reduction_percent = ((total_size_before - total_size_after) / total_size_before) * 100
                        self.log_text.insert(tk.END, 
                            f"总体压缩效果: {self.format_size(total_size_before)} -> {self.format_size(total_size_after)} "
                            f"(减小了 {total_reduction_percent:.2f}%)\n")
                
                self.log_text.see(tk.END)
                
                if self.output_mode.get() == "新文件" and success_count > 0:
                    messagebox.showinfo("成功", f"成功压缩 {success_count} 个PDF文件，保存在: {self.output_dir.get()}")
                elif success_count > 0:
                    messagebox.showinfo("成功", f"成功压缩并替换 {success_count} 个PDF文件")
                
            except Exception as e:
                self.log_text.insert(tk.END, f"压缩过程中出错: {str(e)}\n")
                self.log_text.see(tk.END)
                messagebox.showerror("错误", f"压缩失败: {str(e)}")
            finally:
                # 重置进度条
                self.progress["value"] = 0
        
        # 使用线程执行压缩，避免界面卡顿
        threading.Thread(target=compression_thread).start()
    
    def compress_pdf_file(self, input_path, output_path, params):
        """压缩单个PDF文件"""
        # 创建临时目录用于处理图像
        with tempfile.TemporaryDirectory() as temp_dir:
            # 打开PDF文件
            pdf_doc = fitz.open(input_path)
            
            # 创建新的PDF写入器
            pdf_writer = PdfWriter()
            
            # 处理每一页
            for page_num in range(len(pdf_doc)):
                # 更新日志
                self.log_text.insert(tk.END, f"处理第 {page_num + 1}/{len(pdf_doc)} 页...\n")
                self.log_text.see(tk.END)
                self.parent.update_idletasks()
                
                # 获取页面
                page = pdf_doc.load_page(page_num)
                
                # 判断该页是否包含图像
                image_list = page.get_images()
                
                if image_list and params["optimize_images"]:
                    # 创建临时PDF写入器来存储这一页
                    temp_writer = PdfWriter()
                    
                    # 获取原始页面尺寸
                    page_rect = page.rect
                    original_width = page_rect.width
                    original_height = page_rect.height
                    
                    # 根据是否保持页面尺寸设置渲染参数
                    if params["keep_page_size"]:
                        # 计算适合的矩阵以保持原始尺寸但使用指定的DPI
                        zoom_factor = params["image_dpi"] / 72  # 72是PDF的基准DPI
                        pix = page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor))
                    else:
                        # 直接使用DPI值进行渲染
                        pix = page.get_pixmap(matrix=fitz.Matrix(params["image_dpi"]/72, params["image_dpi"]/72))
                    
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # 保存压缩后的图像到临时PDF
                    img_temp = io.BytesIO()
                    img.save(img_temp, format='JPEG', quality=params["image_quality"], optimize=True)
                    img_temp.seek(0)
                    
                    # 从压缩后的图像创建新的PDF页面
                    temp_pdf_path = os.path.join(temp_dir, f"temp_page_{page_num}.pdf")
                    
                    if params["keep_page_size"]:
                        # 创建特定大小的PDF
                        c = fitz.open()
                        new_page = c.new_page(width=original_width, height=original_height)
                        
                        # 将图像放置在页面上并调整大小以适应原始尺寸
                        rect = fitz.Rect(0, 0, original_width, original_height)
                        new_page.insert_image(rect, stream=img_temp.getvalue())
                        
                        c.save(temp_pdf_path)
                        c.close()
                    else:
                        # 直接保存为PDF，尺寸会根据图像大小确定
                        img.save(temp_pdf_path, format='PDF')
                    
                    # 打开临时PDF并添加到写入器
                    with open(temp_pdf_path, 'rb') as f:
                        temp_reader = PdfReader(f)
                        pdf_writer.add_page(temp_reader.pages[0])
                else:
                    # 如果页面没有图像或不优化图像，则保持原样
                    pdf_reader = PdfReader(open(input_path, 'rb'))
                    pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # 处理元数据
            if not params["remove_metadata"]:
                # 复制原PDF的元数据
                pdf_reader = PdfReader(open(input_path, 'rb'))
                if pdf_reader.metadata:
                    pdf_writer.add_metadata(pdf_reader.metadata)
            
            # 保存压缩后的PDF
            with open(output_path, 'wb') as f:
                pdf_writer.write(f)
    
    def format_size(self, size_in_bytes):
        """格式化文件大小为易读的形式"""
        # 转换为KB
        size_in_kb = size_in_bytes / 1024.0
        if size_in_kb < 1024:
            return f"{size_in_kb:.2f} KB"
        
        # 转换为MB
        size_in_mb = size_in_kb / 1024.0
        if size_in_mb < 1024:
            return f"{size_in_mb:.2f} MB"
        
        # 转换为GB
        size_in_gb = size_in_mb / 1024.0
        return f"{size_in_gb:.2f} GB"
