# PDF工具箱

一个功能强大的PDF处理工具集合，包含多种常用PDF操作功能，界面简洁直观，使用方便。

## 功能特点

PDF工具箱提供以下主要功能：

1. **PDF合并**
   - 支持合并多个PDF文件
   - 支持将图片(JPG, PNG等)与PDF混合合并
   - 提供三种合并模式：原样、自动调整和手动调整
   - 支持设置不同的页面尺寸和方向

2. **PDF转图片**
   - 将PDF文档转换为多种图片格式(JPG, PNG, TIFF, BMP)
   - 支持自定义DPI设置
   - 支持选择指定页面范围进行转换

3. **图片格式转换**
   - 支持主流图片格式之间的互相转换
   - 支持图片尺寸调整
   - 支持质量参数调整

4. **PDF压缩**
   - 提供多级压缩选项以减小PDF文件大小
   - 支持图像优化、元数据移除等操作
   - 可选择替换原文件或创建新文件

5. **PDF属性查看**
   - 查看PDF文件的详细属性信息
   - 分析纸张规格和尺寸
   - 页面预览功能

6. **PDF页面尺寸转换**
   - 将PDF转换为标准尺寸(A4、A3等)
   - 支持自定义尺寸设置
   - 保持原始内容比例

## 安装说明

### 方法一：直接运行Python脚本

1. 确保已安装Python 3.6或更高版本
2. 安装所需依赖库：
   ```
   pip install -r requirements.txt
   ```
3. 运行主程序：
   ```
   python pdf_tool_gui.py
   ```

### 方法二：使用可执行文件

1. 从Release页面下载最新版本的可执行文件
2. 或者自行构建可执行文件：
   ```
   python build_exe.py
   ```
   构建完成后，可执行文件将位于`dist`目录中

## 使用说明

### PDF合并

1. 在"合并PDF和图片"标签页中点击"添加文件"选择要合并的PDF文件或图片
2. 使用"上移"和"下移"按钮调整文件顺序
3. 选择合并模式：
   - 原样：保持原始页面尺寸
   - 自动调整：统一调整页面尺寸
   - 手动调整：按指定参数调整页面
4. 点击"合并文件"按钮并选择保存位置

### PDF转图片

1. 在"PDF转图片"标签页中选择要转换的PDF文件
2. 设置输出格式、DPI和页面范围
3. 选择输出目录
4. 点击"转换"按钮开始处理

### 图片格式转换

1. 在"图片格式转换"标签页中选择要转换的图片文件
2. 设置目标格式和质量参数
3. 可选择是否调整图片尺寸
4. 选择输出目录
5. 点击"转换"按钮开始处理

### PDF压缩

1. 在"PDF压缩"标签页中选择要压缩的PDF文件
2. 选择压缩级别和相关选项
3. 选择输出方式和目录
4. 点击"压缩"按钮开始处理

### PDF属性查看

1. 在"PDF属性查看"标签页中选择要分析的PDF文件
2. 点击"分析PDF属性"按钮
3. 查看文件详细属性和页面预览

### PDF页面尺寸转换

1. 在"PDF页面尺寸转换"标签页中选择要转换的PDF文件
2. 选择目标尺寸或输入自定义尺寸
3. 选择输出目录
4. 点击"转换PDF尺寸"按钮开始处理

## 系统要求

- 操作系统：Windows 7/8/10/11
- 内存：至少2GB RAM
- 硬盘空间：至少100MB可用空间
- 屏幕分辨率：建议1280x720或更高

## 技术栈

- Python 3.6+
- GUI: Tkinter/ttk
- PDF处理: PyPDF2, PyMuPDF (fitz)
- 图像处理: Pillow (PIL)
- 界面主题: ttkthemes

## 常见问题

**Q: 为什么合并大文件时程序会变慢？**  
A: 处理大型PDF文件需要更多内存和CPU资源，请耐心等待或尝试分批处理。

**Q: 转换后的图片质量不佳？**  
A: 尝试增加DPI值和质量参数以提高输出质量，但这也会增加文件大小。

**Q: 压缩后的PDF无法打开或内容丢失？**  
A: 尝试降低压缩级别，某些含有特殊元素的PDF可能与高压缩不兼容。

## Todo列表
- [ ] 测试小功能，减少bug
  - [x] 修改主操作按钮配色
  - [ ] pdf合并功能测试及bugfix
- [ ] 代码优化，减少冗余

## 许可证

本项目使用MIT许可证。详见LICENSE文件。

## 更新日志

### v0.0.1.20
- 初始版本发布
- 实现基本PDF处理功能
- 添加多种格式转换支持

## 贡献指南

欢迎提交问题报告、功能请求或代码贡献。请使用GitHub的Issue和Pull Request功能。

## 鸣谢

- 感谢所有开源库的贡献者
- 特别感谢PyPDF2、PyMuPDF和Pillow项目
