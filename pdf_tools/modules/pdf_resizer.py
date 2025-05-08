import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
import threading
from datetime import datetime
import sys

class PDFResizerTab:
    """处理PDF页面尺寸转换的标签页"""
    
    def __init__(self, parent, theme_manager=None):
        self.parent = parent
        self.theme_manager = theme_manager
        self.frame = ttk.Frame(parent)
        
        # 预定义尺寸，格式为 {名称: (宽度mm, 高度mm)}
        self.predefined_sizes = {
            "A4": (210, 297),
            "A3": (297, 420),
            "A5": (148, 210),
            "B4": (250, 353),
            "B5": (176, 250),
            "Letter": (215.9, 279.4),
            "Legal": (215.9, 355.6),
            "Executive": (184.1, 266.7)
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 输入文件部分
        input_frame = ttk.LabelFrame(self.frame, text="选择输入PDF文件")
        input_frame.pack(fill="x", padx=10, pady=5, expand=False)
        
        self.input_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path_var, width=70).pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill="x")
        ttk.Button(input_frame, text="浏览...", command=self.select_input_file).pack(side=tk.RIGHT, padx=5, pady=10)
        
        # 输出目录部分
        output_frame = ttk.LabelFrame(self.frame, text="选择输出目录")
        output_frame.pack(fill="x", padx=10, pady=5, expand=False)
        
        self.output_path_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path_var, width=70).pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill="x")
        ttk.Button(output_frame, text="浏览...", command=self.select_output_directory).pack(side=tk.RIGHT, padx=5, pady=10)
        
        # 尺寸设置部分
        size_frame = ttk.LabelFrame(self.frame, text="页面尺寸设置")
        size_frame.pack(fill="x", padx=10, pady=5, expand=False)
        
        # 尺寸选择方式
        size_selection_frame = ttk.Frame(size_frame)
        size_selection_frame.pack(fill="x", padx=5, pady=5)
        
        self.size_selection = tk.StringVar(value="predefined")
        ttk.Radiobutton(size_selection_frame, text="预定义尺寸", variable=self.size_selection, 
                        value="predefined", command=self.toggle_size_input).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(size_selection_frame, text="自定义尺寸", variable=self.size_selection, 
                        value="custom", command=self.toggle_size_input).pack(side=tk.LEFT, padx=5)
        
        # 预定义尺寸选择
        self.predefined_frame = ttk.Frame(size_frame)
        self.predefined_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.predefined_frame, text="选择页面规格:").pack(side=tk.LEFT, padx=5)
        self.size_combo = ttk.Combobox(self.predefined_frame, values=list(self.predefined_sizes.keys()), state="readonly")
        self.size_combo.pack(side=tk.LEFT, padx=5)
        self.size_combo.current(0)  # 默认选择A4
        
        # 自定义尺寸输入
        self.custom_frame = ttk.Frame(size_frame)
        
        ttk.Label(self.custom_frame, text="宽度 (mm):").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.StringVar(value="210")
        ttk.Entry(self.custom_frame, textvariable=self.width_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.custom_frame, text="高度 (mm):").pack(side=tk.LEFT, padx=5)
        self.height_var = tk.StringVar(value="297")
        ttk.Entry(self.custom_frame, textvariable=self.height_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 说明文本
        ttk.Label(size_frame, text="注意: 页面方向(横/竖)将保持与原PDF一致").pack(pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill="x", padx=10, pady=15)
        
        ttk.Button(button_frame, text="转换PDF尺寸", command=self.resize_pdf, style="Primary.TButton").pack(pady=10)
        
        # 进度显示
        progress_frame = ttk.Frame(self.frame)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(padx=5)
        
        # 初始化界面状态
        self.toggle_size_input()
    
    def toggle_size_input(self):
        """切换尺寸输入模式"""
        mode = self.size_selection.get()
        if mode == "predefined":
            self.predefined_frame.pack(fill="x", padx=5, pady=5)
            self.custom_frame.pack_forget()
        else:
            self.predefined_frame.pack_forget()
            self.custom_frame.pack(fill="x", padx=5, pady=5)
    
    def select_input_file(self):
        """选择输入PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_path_var.set(file_path)
            # 自动设置默认输出目录
            dir_path = os.path.dirname(file_path)
            self.output_path_var.set(dir_path)
    
    def select_output_directory(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_path_var.set(dir_path)
    
    def get_target_size(self):
        """获取目标尺寸（宽度和高度），单位为毫米"""
        if self.size_selection.get() == "predefined":
            size_name = self.size_combo.get()
            return self.predefined_sizes.get(size_name, (210, 297))  # 默认A4
        else:
            try:
                width = float(self.width_var.get())
                height = float(self.height_var.get())
                return (width, height)
            except ValueError:
                messagebox.showerror("输入错误", "请输入有效的宽度和高度数值")
                return None
    
    def resize_pdf(self):
        """执行PDF尺寸转换"""
        input_path = self.input_path_var.get()
        output_dir = self.output_path_var.get()
        
        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror("错误", "请选择有效的PDF文件")
            return
        
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        target_size = self.get_target_size()
        if not target_size:
            return
        
        # 开始转换
        threading.Thread(target=self._resize_pdf_thread, args=(input_path, output_dir, target_size)).start()
    
    def _resize_pdf_thread(self, input_path, output_dir, target_size):
        """在后台线程中执行PDF尺寸转换"""
        try:
            self.status_var.set("正在处理，请稍候...")
            
            # 准备输出文件名
            file_name = os.path.basename(input_path)
            name, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"{name}_resized_{timestamp}.pdf")
            
            # 打开输入PDF
            pdf_doc = fitz.open(input_path)
            # 创建新PDF
            new_doc = fitz.open()
            
            # 设置目标尺寸（毫米转换为点）
            target_width_pt = target_size[0] * 2.83465  # 1mm = 2.83465pt
            target_height_pt = target_size[1] * 2.83465
            
            total_pages = len(pdf_doc)
            for i, page in enumerate(pdf_doc):
                # 检查页面方向
                is_landscape = page.rect.width > page.rect.height
                
                # 根据原始页面方向决定目标页面方向
                if is_landscape:
                    # 如果原页面是横向，交换宽高
                    rect = fitz.Rect(0, 0, 
                                    int(max(target_width_pt, target_height_pt)), 
                                    int(min(target_width_pt, target_height_pt)))
                else:
                    # 如果原页面是纵向，正常设置宽高
                    rect = fitz.Rect(0, 0, 
                                    int(min(target_width_pt, target_height_pt)), 
                                    int(max(target_width_pt, target_height_pt)))
                
                # 创建新页面
                new_page = new_doc.new_page(width=int(rect.width), height=int(rect.height))
                
                # 缩放内容到新页面大小
                mat = fitz.Matrix(rect.width/page.rect.width, rect.height/page.rect.height)
                
                # 修复: 处理不同版本PyMuPDF的API差异
                try:
                    # 旧版PyMuPDF API (不使用命名参数)
                    new_page.show_pdf_page(rect, pdf_doc, i, mat)
                except TypeError:
                    try:
                        # 如果失败，尝试不同参数顺序
                        new_page.show_pdf_page(rect, pdf_doc, page.number, mat)
                    except TypeError:
                        try:
                            # 再尝试一种不带矩阵的方式，但会导致不精确的缩放
                            new_page.show_pdf_page(rect, pdf_doc, i)
                        except:
                            # 如果所有方法都失败，尝试直接复制页面然后进行缩放变形
                            new_page = new_doc.new_page(-1, width=rect.width, height=rect.height)
                            new_page.insert_pdf(pdf_doc, from_page=i, to_page=i)
                
                # 更新进度
                progress = (i + 1) / total_pages * 100
                self.progress_var.set(progress)
                self.status_var.set(f"处理页面 {i+1}/{total_pages}")
            
            # 保存新PDF
            new_doc.save(output_path)
            new_doc.close()
            pdf_doc.close()
            
            self.status_var.set(f"完成! 输出文件保存至: {output_path}")
            messagebox.showinfo("完成", f"PDF尺寸转换成功!\n输出文件:\n{output_path}")
            
        except Exception as e:
            self.status_var.set(f"处理过程中出错: {str(e)}")
            messagebox.showerror("错误", f"处理PDF时出错:\n{str(e)}")
            # 打印更详细的错误信息以便调试
            import traceback
            traceback.print_exc()
