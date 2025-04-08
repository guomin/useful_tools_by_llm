import pandas as pd
import seaborn as sns
import os
import requests
import json
import io
import base64
from IPython.display import display, HTML


# 功能：根据对话内容生成数据分析结果
# 1. 使用deepseek库作为大模型后端
# 2. 使用pandas库进行数据分析
# 3. 用户输入自然语言问题，大模型转化为代码，执行代码，返回结果
##   3.1 问话示例：输出年龄最大的5个人
##   3.2 问话示例：输出年龄最大的5个人的姓名和年龄，等等
# 4. 支持数据可视化，生成图表
# 注意：
# 1. 不要调用pandasai库，自己拆解和实现功能
# 2. deepseek文档：https://api-docs.deepseek.com/zh-cn/

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.font_manager import FontProperties

# 设置中文字体支持
def set_chinese_font():
    """设置支持中文显示的字体"""
    # 尝试设置中文字体
    font_names = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
    font_found = False
    
    for font_name in font_names:
        try:
            font_prop = FontProperties(fname=mpl.font_manager.findfont(font_name))
            plt.rcParams['font.family'] = font_prop.get_name()
            font_found = True
            break
        except:
            continue
    
    # 如果没有找到合适的字体，使用系统默认字体并设置支持中文
    if not font_found:
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Bitstream Vera Sans',
                                           'Computer Modern Sans Serif', 'Lucida Grande', 'Verdana',
                                           'Geneva', 'Lucid', 'Arial', 'Helvetica', 'Avant Garde', 
                                           'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# 初始化时设置字体
set_chinese_font()

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
print("DeepSeek API Key:", DEEPSEEK_API_KEY)  # 调试输出，确保密钥已加载
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class PandasAnalyzer:
    def __init__(self, dataframe=None, file_path=None):
        """初始化分析器，可以接受DataFrame对象或文件路径"""
        if dataframe is not None:
            self.df = dataframe
        elif file_path is not None:
            self._load_data(file_path)
        else:
            self.df = None
        
        self.df_name = "df"  # 默认DataFrame变量名
        self.last_code = None
        self.last_result = None
        self.last_figure = None
        
    def _load_data(self, file_path):
        """根据文件扩展名加载数据"""
        extension = os.path.splitext(file_path)[1].lower()
        if extension == '.csv':
            self.df = pd.read_csv(file_path)
        elif extension in ['.xlsx', '.xls']:
            self.df = pd.read_excel(file_path)
        elif extension == '.json':
            self.df = pd.read_json(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {extension}")
    
    def _call_deepseek(self, prompt):
        """调用DeepSeek API获取代码响应"""
        if not DEEPSEEK_API_KEY:
            raise ValueError("未设置DeepSeek API密钥")
        
        # 准备数据描述
        df_info = f"DataFrame信息:\n"
        df_info += f"列名和数据类型: {self.df.dtypes.to_dict()}\n"
        df_info += f"数据示例(前5行):\n{self.df.head().to_string()}\n"
        df_info += f"数据统计摘要:\n{self.df.describe().to_string()}\n"
        
        # 构建完整提示
        full_prompt = f"""你是一个数据分析专家，请根据以下问题，生成仅包含Python代码的回答，不要有任何解释性文字。
生成的代码必须严格遵循Python语法规则，确保所有使用的变量在使用前已经定义，避免任何名称错误。
代码需要使用pandas，如果需要可视化图表，使用基础的matplotlib来分析和可视化数据。

这是在命令行环境中运行的程序，请确保生成图表代码遵循以下规则：

1. 使用简单可靠的matplotlib语法
2. 在绘图代码前明确调用 plt.figure(figsize=(10, 6))
3. 设置清晰可读的标题、坐标轴标签
4. 确保图表中包含实际数据，不要返回空白图表
5. 增加 plt.tight_layout() 优化布局
6. 所有变量必须先定义后使用
7. 不要使用plt.show()，系统会自动保存图表

分析要求: {prompt}

可用的DataFrame如下:
{df_info}

以下是简单的图表代码示例：

示例(条形图):
```python
# 计算各部门的平均收入
dept_avg = df.groupby('部门')['收入'].mean().sort_values(ascending=False)

# 创建条形图
plt.figure(figsize=(10, 6))
plt.bar(range(len(dept_avg)), dept_avg.values, color='skyblue')
plt.xticks(range(len(dept_avg)), dept_avg.index, rotation=45)

plt.title('各部门平均收入对比', fontsize=16)
plt.xlabel('部门', fontsize=14)
plt.ylabel('平均收入（元）', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
```

请确保你的代码是可直接执行的，所有变量在使用前都已定义，不包含任何解释性文字。
"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        payload = {
            "model": "deepseek-coder",
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            code = result["choices"][0]["message"]["content"].strip()
            
            # 移除可能的代码块标记
            code = code.replace('```python', '').replace('```', '').strip()
            return code
        except Exception as e:
            return f"API调用错误: {str(e)}"
    
    def execute_code(self, code):
        """执行生成的代码并返回结果"""
        self.last_code = code
        
        # 创建本地变量环境
        local_vars = {"df": self.df, "pd": pd, "plt": plt, "sns": sns}
        
        try:
            # 执行代码前关闭所有图形，避免影响
            plt.close('all')
            
            # 执行用户代码
            exec(code, globals(), local_vars)
            
            # 检查是否创建了图形
            if plt.get_fignums():
                # 确保有目录保存图表
                output_dir = os.path.join(os.getcwd(), 'output_charts')
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成不重复的文件名
                chart_filename = os.path.join(output_dir, f'chart_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png')
                
                # 获取当前图形并保存
                fig = plt.gcf()  # 获取当前图形
                fig.tight_layout()  # 调整布局
                fig.savefig(chart_filename, format='png', bbox_inches='tight', dpi=100)
                
                # 同时保存到内存供可能的显示使用
                buf = io.BytesIO()
                fig.savefig(buf, format='png')
                buf.seek(0)
                self.last_figure = base64.b64encode(buf.read()).decode('utf-8')
                
                plt.close(fig)  # 关闭图形释放内存
                
                return {"type": "figure", "content": self.last_figure, "file_path": chart_filename}
            
            # 获取最后一个变量作为结果
            for var_name, var_value in local_vars.items():
                if var_name != "df" and not var_name.startswith("__") and var_name not in ["pd", "plt", "sns"]:
                    self.last_result = var_value
                    return {"type": "data", "content": var_value}
            
            # 如果没有明确的结果变量，尝试返回DataFrame
            if "result" in local_vars:
                self.last_result = local_vars["result"]
                return {"type": "data", "content": self.last_result}
            
            return {"type": "message", "content": "代码执行成功，但没有返回结果"}
        except Exception as e:
            return {"type": "error", "content": str(e)}
    
    def analyze(self, question):
        """根据自然语言问题生成并执行数据分析代码"""
        if self.df is None:
            return "未加载数据，请先加载数据"
        
        code = self._call_deepseek(question)
        result = self.execute_code(code)
        
        # 格式化输出
        if result["type"] == "figure":
            return HTML(f'<img src="data:image/png;base64,{result["content"]}" />')
        elif result["type"] == "data":
            if isinstance(result["content"], pd.DataFrame):
                return result["content"]
            else:
                return result["content"]
        else:
            return result["content"]
    
    def show_code(self):
        """显示最后执行的代码"""
        return self.last_code
        
    def run_interactive(self):
        """启动交互式对话模式"""
        print("欢迎使用交互式数据分析助手！")
        print("请输入您的数据分析问题，输入'退出'结束对话。")
        print("输入'显示代码'可查看上一次执行的代码。")
        
        while True:
            try:
                question = input("\n请输入您的问题：")
                if question.lower() in ['退出', 'exit', 'quit']:
                    print("感谢使用，再见！")
                    break
                elif question.lower() in ['显示代码', 'show code']:
                    code = self.show_code()
                    if code:
                        print("\n上一次执行的代码：")
                        print(code)
                    else:
                        print("还未执行任何代码")
                else:
                    print("\n正在分析您的问题...")
                    result = self.analyze(question)
                    print("\n分析结果：")
                    
                    # 处理不同类型的结果
                    if isinstance(result, dict) and result.get("type") == "figure":
                        print(f"已生成图表并保存到：{result.get('file_path')}")
                        print("在命令行环境中无法直接显示图表，请查看保存的文件")
                    elif isinstance(result, HTML):
                        print("生成了图表，已保存到output_charts目录")
                        file_path = result.data.split('base64,')[0].split('"')[0]
                        if file_path:
                            print(f"图表已保存到：{file_path}")
                    else:
                        print(result)
            except KeyboardInterrupt:
                print("\n操作被中断，感谢使用！")
                break
            except Exception as e:
                print(f"处理问题时出错：{str(e)}")

# 示例使用
if __name__ == "__main__":
    # 创建示例数据
    data = {
        "姓名": ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"],
        "年龄": [45, 32, 56, 28, 67, 39, 51, 42],
        "收入": [8000, 15000, 12000, 20000, 9000, 30000, 18000, 25000],
        "部门": ["销售", "技术", "销售", "技术", "行政", "技术", "行政", "销售"]
    }
    sample_df = pd.DataFrame(data)
    
    # 初始化分析器
    analyzer = PandasAnalyzer(dataframe=sample_df)
    
    # 启动交互式模式
    print("启动交互式数据分析对话...")
    analyzer.run_interactive()
    
    # 以下是非交互式示例（可以注释掉）
    """
    print("示例1: 年龄最大的5个人")
    result1 = analyzer.analyze("输出年龄最大的5个人")
    print(result1)
    print("\n示例2: 年龄最大的5个人的姓名和年龄")
    result2 = analyzer.analyze("输出年龄最大的5个人的姓名和年龄")
    print(result2)
    print("\n示例3: 各部门平均收入可视化")
    result3 = analyzer.analyze("创建各部门的平均收入柱状图")
    # 如果在支持显示的环境中，会显示图表
    if isinstance(result3, HTML):
        print("生成了图表，请在支持HTML显示的环境中查看")
    else:
        print(result3)
    """
