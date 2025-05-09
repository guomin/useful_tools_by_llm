"""
打包PDF工具为EXE文件
使用方法: 执行此脚本，将在dist目录下生成EXE文件
"""
import os
import subprocess
import sys
import shutil
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入版本号
try:
    from pdf_tool_gui import VERSION
except ImportError:
    VERSION = "v0.0.1"  # 如果导入失败，使用默认版本号

def build_exe():
    """使用PyInstaller打包应用程序为EXE文件"""
    print("开始打包PDF工具为可执行文件...")
    print(f"应用版本: {VERSION}")

    # 确保必要的依赖已安装
    required_packages = [
        "PyInstaller", 
        "PyPDF2", 
        "Pillow", 
        "PyMuPDF", 
        "ttkthemes"
    ]
    
    for package in required_packages:
        try:
            __import__(package.lower())
            print(f"检测到 {package} 已安装")
        except ImportError:
            print(f"未检测到 {package}，尝试安装...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"{package} 安装完成")
            except Exception as e:
                print(f"安装 {package} 失败: {str(e)}")
                print("尝试从 requirements_for_build.txt 安装所有依赖...")
                if os.path.exists("requirements_for_build.txt"):
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_for_build.txt"])
                        print("依赖安装完成")
                        break
                    except Exception as e:
                        print(f"安装依赖失败: {str(e)}")
                        sys.exit(1)
                else:
                    print("未找到 requirements_for_build.txt 文件")
                    sys.exit(1)

    # 清理之前的构建文件
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 检查是否有图标文件，如果没有尝试使用 create_icon.py 创建
    if not os.path.exists("icon.ico"):
        print("未找到icon.ico文件，尝试创建默认图标...")
        try:
            # 优先使用专用的图标创建模块
            if os.path.exists("create_icon.py"):
                print("使用 create_icon.py 创建图标...")
                subprocess.check_call([sys.executable, "create_icon.py"])
                if os.path.exists("icon.ico"):
                    print("成功创建默认图标")
                    use_icon = True
                else:
                    raise Exception("图标创建失败")
            else:
                # 如果没有专用模块，使用内置方法创建
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
                use_icon = True
        except Exception as e:
            print(f"创建图标失败: {str(e)}")
            print("将使用无图标方式打包")
            use_icon = False
    else:
        use_icon = True
    
    # 创建spec文件内容
    if use_icon:
        # 使用图标的spec配置
        spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdf_tool_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['ttkthemes'],
    hookspath=[],
    hooksconfig={{}},
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
    name='PDF工具_{VERSION}',
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
        spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pdf_tool_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['ttkthemes'],
    hookspath=[],
    hooksconfig={{}},
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
    name='PDF工具_{VERSION}',
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
    try:
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "PyInstaller", 
            "--clean", 
            "pdf_tool.spec"
        ])
        
        print("\n打包完成! 可执行文件已生成在dist目录中。")
        print(f"您可以在dist文件夹中找到 'PDF工具_{VERSION}.exe' 文件")
        
        # 检查是否成功创建了EXE文件
        exe_path = os.path.join("dist", f"PDF工具_{VERSION}.exe")
        if os.path.exists(exe_path):
            print(f"\n成功创建可执行文件: {os.path.abspath(exe_path)}")
            print(f"文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        else:
            print("\n警告: 未找到生成的可执行文件，请检查打包过程是否有错误")
        
        print("\n注意事项:")
        print("1. 首次启动可能较慢，这是正常现象")
        print("2. 杀毒软件可能会对生成的EXE进行检查，这是因为打包工具的特性")
        print("3. 确保最终用户电脑上安装了适当的字体，否则可能会影响界面显示")
        print("4. 如果程序无法启动，请尝试安装 Microsoft Visual C++ Redistributable")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {str(e)}")
        print("请检查上述错误信息，解决问题后重试")
        return False

if __name__ == "__main__":
    build_exe()
