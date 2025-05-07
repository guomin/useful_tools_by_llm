"""
为PDF工具创建一个简单的图标文件
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_icon():
    """创建一个简单的图标文件"""
    # 创建一个512x512的图标（这是常用的图标尺寸）
    icon_size = 512
    icon = Image.new('RGBA', (icon_size, icon_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(icon)
    
    # 绘制背景
    draw.rectangle([(0, 0), (icon_size, icon_size)], fill=(52, 152, 219, 255))
    
    # 绘制PDF字样
    try:
        # 尝试使用一个常见字体
        font = ImageFont.truetype("arial.ttf", int(icon_size/2))
    except IOError:
        # 如果找不到字体，使用默认字体
        font = ImageFont.load_default()
    
    # 在图标中央绘制文字
    draw.text((icon_size/2, icon_size/2), "PDF", fill=(255, 255, 255, 255), 
              font=font, anchor="mm")
    
    # 保存为ICO文件
    icon.save("icon.ico")
    print(f"图标已创建: {os.path.abspath('icon.ico')}")

if __name__ == "__main__":
    create_simple_icon()
