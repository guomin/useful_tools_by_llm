"""
打包PDF工具为EXE文件
使用方法: 执行此脚本，将在dist目录下生成EXE文件
"""
import os
import subprocess
import sys
import shutil

def build_exe():
    """使用PyInstaller打包应用程序为EXE文件"""
    print("开始打包PDF工具为可执行文件...")

    # 确保PyInstaller已安装
    try:
        import PyInstaller
        print(f"检测到PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("未检测到PyInstaller，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装完成")

    # 清理之前的构建文件
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 检查是否有图标文件，如果没有尝试创建一个
    if not os.path.exists("icon.ico"):
        print("未找到icon.ico文件，尝试创建默认图标...")
        try:
            # 如果有PIL库，尝试创建一个图标
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建一个512x512的图标
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
            print("成功创建默认图标")
        except Exception as e:
            print(f"创建图标失败: {str(e)}")
            print("将使用无图标方式打包")
            use_icon = False
        else:
            use_icon = True
    else:
        use_icon = True
    
    # 创建spec文件内容
    if use_icon:
        # 使用图标的spec配置
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdf_tool_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
"""
    else:
        # 不使用图标的spec配置
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdf_tool_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # 写入spec文件
    with open("pdf_tool.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("生成配置文件完成，开始打包...")
    
    # 执行PyInstaller命令
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "--clean", 
        "pdf_tool.spec"
    ])
    
    print("\n打包完成! 可执行文件已生成在dist目录中。")
    print("您可以在dist文件夹中找到 'PDF工具.exe' 文件")
    print("\n注意事项:")
    print("1. 首次启动可能较慢，这是正常现象")
    print("2. 杀毒软件可能会对生成的EXE进行检查，这是因为打包工具的特性")
    print("3. 确保最终用户电脑上安装了适当的字体，否则可能会影响界面显示")

if __name__ == "__main__":
    build_exe()
