# filepath: d:\projects\useful_tools_by_llm\pdf_tools\modules\pdf_to_image.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from PIL import Image
import fitz  # PyMuPDF

class PDFToImageTab:
    """PDF转图片标签页类"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.style = theme_manager.style
        self.pdf_file_paths = []
        
        # 创建界面
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        
    def create_widgets(self):
        """创建PDF转图片标签页的组件"""
        # PDF文件选择
        select_frame = ttk.Frame(self.frame)
        select_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(select_frame, text="PDF文件:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # 改用按钮组来选择PDF文件和文件夹
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
        
        # 输出格式
        format_frame = ttk.Frame(self.frame)
        format_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT, padx=5, pady=5)
        self.output_format = tk.StringVar(value="JPG")
        formats = ["JPG", "PNG", "TIFF", "BMP"]
        ttk.Combobox(format_frame, textvariable=self.output_format, values=formats, width=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(format_frame, text="DPI:").pack(side=tk.LEFT, padx=5, pady=5)
        self.dpi_var = tk.StringVar(value="300")
        ttk.Entry(format_frame, textvariable=self.dpi_var, width=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 页面范围
        range_frame = ttk.Frame(self.frame)
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
        output_frame = ttk.Frame(self.frame)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT, padx=5, pady=5)
        self.output_dir = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        ttk.Button(output_frame, text="浏览", command=self.select_output_dir).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 转换按钮和进度条
        action_frame = ttk.Frame(self.frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress = ttk.Progressbar(action_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", side=tk.LEFT, expand=True, padx=5, pady=5)
        
        ttk.Button(action_frame, text="转换", command=self.convert_pdf_to_images).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.frame, text="处理日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = ScrolledText(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def on_range_change(self, *args):
        """处理页面范围选择变化"""
        if self.range_var.get() == "自定义":
            self.page_range_entry.config(state="normal")
        else:
            self.page_range_entry.config(state="disabled")
            
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
                        self.parent.update_idletasks()
                        
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