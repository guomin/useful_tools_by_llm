import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import math
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
import datetime

class PDFPropertiesTab:
    """用于查看PDF文件属性的标签页"""
    
    # 定义标准纸张尺寸（单位：毫米）
    # ISO 216标准的A系列纸张
    STANDARD_PAPER_SIZES = {
        "A0": (841, 1189),
        "A1": (594, 841),
        "A2": (420, 594),
        "A3": (297, 420),
        "A4": (210, 297),
        "A5": (148, 210),
        "A6": (105, 148),
        "A7": (74, 105),
        "A8": (52, 74),
        # B系列
        "B0": (1000, 1414),
        "B1": (707, 1000),
        "B2": (500, 707),
        "B3": (353, 500),
        "B4": (250, 353),
        "B5": (176, 250),
        # C系列
        "C0": (917, 1297),
        "C1": (648, 917),
        "C2": (458, 648),
        "C3": (324, 458),
        "C4": (229, 324),
        "C5": (162, 229),
        "C6": (114, 162),
        # 美国标准尺寸
        "Letter": (216, 279),
        "Legal": (216, 356),
        "Tabloid": (279, 432),
        "Executive": (184, 267),
        # 中国标准尺寸
        "16K": (194, 267),
        "8K": (267, 388),
    }
    
    # 允许的误差（毫米）
    SIZE_TOLERANCE = 3
    
    def __init__(self, parent, theme_manager=None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.frame = ttk.Frame(parent)
        
        # 创建界面组件
        self.create_widgets()
        
    def create_widgets(self):
        """创建标签页上的组件"""
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="选择PDF文件")
        file_frame.pack(fill="x", expand=False, padx=5, pady=5)
        
        self.file_path_var = tk.StringVar()
        file_path_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=70)
        file_path_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        browse_button = ttk.Button(
            file_frame, 
            text="浏览", 
            command=self.browse_pdf_file,
            style="Action.TButton"
        )
        browse_button.grid(row=0, column=1, padx=5, pady=5)
        
        analyze_button = ttk.Button(
            file_frame, 
            text="分析PDF属性", 
            command=self.analyze_pdf_properties,
            style="Primary.TButton"
        )
        analyze_button.grid(row=0, column=2, padx=5, pady=5)
        
        file_frame.columnconfigure(0, weight=1)
        
        # 属性显示区域
        properties_frame = ttk.LabelFrame(main_frame, text="PDF文件属性")
        properties_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建属性显示文本区
        self.properties_text = ScrolledText(properties_frame, wrap=tk.WORD, height=20)
        self.properties_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.properties_text.config(font=("Consolas", 10), state="disabled")
        
        # 页面缩略图预览区
        preview_frame = ttk.LabelFrame(main_frame, text="页面预览")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建预览控件
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", height=300)
        self.preview_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 页面选择控件
        page_control_frame = ttk.Frame(preview_frame)
        page_control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(page_control_frame, text="页码:").pack(side=tk.LEFT, padx=5)
        
        self.page_var = tk.StringVar(value="1")
        self.page_spinbox = ttk.Spinbox(
            page_control_frame, 
            from_=1, 
            to=1, 
            textvariable=self.page_var,
            width=5,
            command=self.update_page_preview
        )
        self.page_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            page_control_frame, 
            text="上一页",
            command=self.prev_page
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            page_control_frame, 
            text="下一页",
            command=self.next_page
        ).pack(side=tk.LEFT, padx=5)

    def browse_pdf_file(self):
        """浏览并选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
    
    def format_file_size(self, size_in_bytes):
        """格式化文件大小显示"""
        if size_in_bytes < 1024:
            return f"{size_in_bytes} 字节"
        elif size_in_bytes < 1024 * 1024:
            return f"{size_in_bytes/1024:.2f} KB"
        elif size_in_bytes < 1024 * 1024 * 1024:
            return f"{size_in_bytes/(1024*1024):.2f} MB"
        else:
            return f"{size_in_bytes/(1024*1024*1024):.2f} GB"
    
    def format_date(self, date_str):
        """格式化日期显示"""
        if not date_str:
            return "未知"
        
        try:
            # 尝试将PDF日期格式转换为可读格式
            if isinstance(date_str, str) and date_str.startswith("D:"):
                # 处理D:YYYYMMDDHHmmSS格式
                date_str = date_str[2:]
                if len(date_str) >= 14:
                    year = date_str[0:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    hour = date_str[8:10]
                    minute = date_str[10:12]
                    second = date_str[12:14]
                    return f"{year}-{month}-{day} {hour}:{minute}:{second}"
            return str(date_str)
        except:
            return str(date_str)
    
    def analyze_pdf_properties(self):
        """分析PDF文件属性"""
        file_path = self.file_path_var.get()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "请选择有效的PDF文件")
            return
            
        try:
            # 使用线程执行分析，避免界面冻结
            threading.Thread(target=self._do_analyze_properties, args=(file_path,), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"分析PDF属性时出错: {str(e)}")
    
    def _do_analyze_properties(self, file_path):
        """实际执行PDF属性分析的方法"""
        try:
            # 获取基本文件信息
            file_size = os.path.getsize(file_path)
            file_mod_time = os.path.getmtime(file_path)
            mod_time_str = datetime.datetime.fromtimestamp(file_mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # 使用PyPDF2获取PDF信息
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            # 获取文档信息
            info = reader.metadata
            creator = info.creator if hasattr(info, 'creator') else "未知"
            producer = info.producer if hasattr(info, 'producer') else "未知"
            creation_date = self.format_date(info.creation_date if hasattr(info, 'creation_date') else None)
            mod_date = self.format_date(info.modification_date if hasattr(info, 'modification_date') else None)
            
            # 获取页面信息
            first_page = reader.pages[0]
            width_pts = first_page.mediabox.width
            height_pts = first_page.mediabox.height
            
            # 点转毫米 (1 点 = 0.353 毫米)
            width_mm = width_pts * 0.353
            height_mm = height_pts * 0.353
            
            # 检测是否为标准尺寸
            paper_size = self.identify_paper_size(width_mm, height_mm)
            paper_size_info = f"{paper_size}" if paper_size else "非标准尺寸"
            
            # 使用PyMuPDF获取更多信息
            doc = fitz.open(file_path)
            has_toc = "有" if doc.get_toc() else "无"
            form_fields = "有" if doc.is_form_pdf else "无"
            
            # 检查是否所有页面都是同一尺寸
            uniform_size = True
            page_sizes = []
            size_distribution = {}
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_rect = page.rect
                w_mm = page_rect.width * 0.353
                h_mm = page_rect.height * 0.353
                size = (round(w_mm, 1), round(h_mm, 1))
                page_sizes.append(size)
                
                # 记录尺寸分布
                size_key = f"{size[0]:.1f}x{size[1]:.1f}"
                size_distribution[size_key] = size_distribution.get(size_key, 0) + 1
                
                if page_num > 0 and abs(w_mm - page_sizes[0][0]) > 1 or abs(h_mm - page_sizes[0][1]) > 1:
                    uniform_size = False
            
            # 统计图片数量
            image_count = 0
            for page_num in range(doc.page_count):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                image_count += len(image_list)
            
            # 准备尺寸分布信息
            size_info = ""
            if not uniform_size:
                size_info = "\n\n页面尺寸分布:\n"
                for size_key, count in size_distribution.items():
                    # 对每种尺寸检测是否为标准尺寸
                    w, h = map(float, size_key.split('x'))
                    std_size = self.identify_paper_size(w, h)
                    size_desc = f"{std_size}" if std_size else "非标准尺寸"
                    size_info += f"  - {size_key} 毫米 ({size_desc}): {count}页\n"
            
            # 更新界面
            self.update_properties_display({
                "文件名": os.path.basename(file_path),
                "文件路径": file_path,
                "文件大小": self.format_file_size(file_size),
                "修改时间": mod_time_str,
                "页数": total_pages,
                "页面尺寸": f"{width_pts:.2f} × {height_pts:.2f} 点 ({width_mm:.2f} × {height_mm:.2f} 毫米)",
                "纸张规格": paper_size_info,
                "页面尺寸统一": "是" if uniform_size else "否" + size_info,
                "创建者": creator,
                "生成器": producer,
                "创建日期": creation_date,
                "修改日期": mod_date,
                "目录": has_toc,
                "表单字段": form_fields,
                "图片数量": image_count
            })
            
            # 更新页面预览
            self.update_page_spinbox(1, total_pages)
            self.doc = doc  # 保存文档引用以便预览使用
            self.update_page_preview()
            
        except Exception as e:
            # 更新UI需要在主线程中进行
            self.frame.after(0, lambda: messagebox.showerror("错误", f"分析PDF属性时出错: {str(e)}"))
    
    def identify_paper_size(self, width_mm, height_mm):
        """识别标准纸张尺寸
        
        Args:
            width_mm: 宽度（毫米）
            height_mm: 高度（毫米）
        
        Returns:
            str: 标准纸张尺寸名称，如果不匹配则返回None
        """
        # 确保宽度小于高度，以便正确匹配（横向/纵向都可以）
        w, h = min(width_mm, height_mm), max(width_mm, height_mm)
        
        # 检查是否匹配标准尺寸（考虑误差范围）
        for name, (std_width, std_height) in self.STANDARD_PAPER_SIZES.items():
            # 标准化尺寸（宽度小于高度）
            std_w, std_h = min(std_width, std_height), max(std_width, std_height)
            
            # 检查是否在误差范围内
            if (abs(w - std_w) <= self.SIZE_TOLERANCE and 
                abs(h - std_h) <= self.SIZE_TOLERANCE):
                orientation = "纵向" if width_mm < height_mm else "横向"
                return f"{name} ({orientation})"
        
        return None
    
    def update_properties_display(self, properties_dict):
        """更新属性显示区域"""
        def _update():
            self.properties_text.config(state="normal")
            self.properties_text.delete(1.0, tk.END)
            
            # 添加属性信息
            for key, value in properties_dict.items():
                self.properties_text.insert(tk.END, f"{key}: {value}\n\n")
                
            self.properties_text.config(state="disabled")
        
        # 确保在主线程中更新UI
        self.frame.after(0, _update)
    
    def update_page_spinbox(self, current, maximum):
        """更新页面选择器的范围"""
        def _update():
            self.page_spinbox.config(from_=1, to=maximum)
            self.page_var.set(str(current))
        
        # 确保在主线程中更新UI
        self.frame.after(0, _update)
    
    def update_page_preview(self):
        """更新当前选定页面的预览"""
        try:
            if not hasattr(self, 'doc'):
                return
                
            page_num = int(self.page_var.get()) - 1
            if page_num < 0 or page_num >= self.doc.page_count:
                return
            
            # 获取页面
            page = self.doc[page_num]
            
            # 渲染页面到图像
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # 缩放系数
            
            # 将图像转换为tkinter可用格式
            img_data = pix.tobytes("ppm")
            
            # 创建PhotoImage对象
            image = tk.PhotoImage(data=img_data)
            
            # 保存引用以防止垃圾回收
            self.current_image = image
            
            # 清除先前的内容并显示新图像
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=image)
            
            # 调整画布大小以适应图像
            self.preview_canvas.config(width=pix.width, height=pix.height)
            self.preview_canvas.config(scrollregion=(0, 0, pix.width, pix.height))
            
        except Exception as e:
            messagebox.showerror("错误", f"无法预览页面: {str(e)}")
    
    def next_page(self):
        """显示下一页"""
        try:
            current = int(self.page_var.get())
            if hasattr(self, 'doc') and current < self.doc.page_count:
                self.page_var.set(str(current + 1))
                self.update_page_preview()
        except:
            pass
    
    def prev_page(self):
        """显示上一页"""
        try:
            current = int(self.page_var.get())
            if current > 1:
                self.page_var.set(str(current - 1))
                self.update_page_preview()
        except:
            pass
