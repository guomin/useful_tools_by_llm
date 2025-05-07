# filepath: d:\projects\useful_tools_by_llm\pdf_tools\modules\image_converter.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from PIL import Image

class ImageConvertTab:
    """图片格式转换标签页类"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.style = theme_manager.style
        self.img_file_paths = []
        
        # 创建界面
        self.frame = ttk.Frame(parent)
        self.create_widgets()
        
    def create_widgets(self):
        """设置图片格式转换页面"""
        # 图片文件选择
        select_frame = ttk.Frame(self.frame)
        select_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(select_frame, text="图片文件:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # 按钮组来选择图片文件和文件夹
        buttons_frame = ttk.Frame(select_frame)
        buttons_frame.pack(side=tk.LEFT, fill="x", expand=True)
        
        ttk.Button(buttons_frame, text="选择文件", command=self.select_image_files).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="选择文件夹", command=self.select_image_folder).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(buttons_frame, text="清空列表", command=self.clear_image_list).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 文件列表显示区域
        file_list_frame = ttk.LabelFrame(self.frame, text="图片文件列表")
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
        
        # 输入格式和输出格式
        format_frame = ttk.Frame(self.frame)
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
        quality_frame = ttk.Frame(self.frame)
        quality_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(quality_frame, text="图像质量(1-100):").pack(side=tk.LEFT, padx=5, pady=5)
        self.quality_var = tk.StringVar(value="85")
        ttk.Entry(quality_frame, textvariable=self.quality_var, width=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 调整尺寸选项
        resize_frame = ttk.Frame(self.frame)
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
        output_frame = ttk.Frame(self.frame)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT, padx=5, pady=5)
        self.img_output_dir = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.img_output_dir, width=50).pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        ttk.Button(output_frame, text="浏览", command=self.select_img_output_dir).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 转换按钮和进度条
        action_frame = ttk.Frame(self.frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.img_progress = ttk.Progressbar(action_frame, orient="horizontal", length=100, mode="determinate")
        self.img_progress.pack(fill="x", side=tk.LEFT, expand=True, padx=5, pady=5)
        
        ttk.Button(action_frame, text="转换", command=self.convert_images).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.frame, text="处理日志")
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
                    self.parent.update_idletasks()
                
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
