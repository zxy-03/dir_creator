"""
目录结构创建工具 - GUI版本
可直接打包成EXE，支持粘贴目录树并自动创建文件和文件夹
"""

import os
import re
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
import threading


class DirectoryCreator:
    """从目录树文本创建文件和文件夹"""
    
    def __init__(self, base_path='.', callback=None):
        self.base_path = Path(base_path)
        self.callback = callback  # 用于GUI回调
        self.stats = {'dirs': 0, 'files': 0, 'errors': 0}
    
    def log(self, message):
        """日志输出"""
        if self.callback:
            self.callback(message)
        else:
            print(message)
    
    def create_from_text(self, tree_text):
        """从文本格式的目录树创建结构"""
        lines = tree_text.strip().split('\n')
        path_stack = []
        prev_indent = -1
        
        for line in lines:
            # 跳过空行
            if not line.strip():
                continue
            
            # 提取名称和缩进
            name, indent_level = self._parse_line(line)
            
            if not name:
                continue
            
            # 判断是文件还是目录
            is_dir = name.endswith('/') or name.endswith('\\') or '.' not in os.path.basename(name.rstrip('/\\'))
            clean_name = name.rstrip('/\\')
            
            # 计算路径
            if indent_level == 0:
                current_path = self.base_path / clean_name
                path_stack = [current_path]
            else:
                # 调整路径栈
                if indent_level <= len(path_stack) - 1:
                    path_stack = path_stack[:indent_level]
                
                parent = path_stack[-1] if path_stack else self.base_path
                current_path = parent / clean_name
                
                if is_dir and indent_level < len(path_stack):
                    path_stack[indent_level] = current_path
                elif is_dir:
                    path_stack.append(current_path)
            
            # 创建目录或文件
            try:
                if is_dir:
                    current_path.mkdir(parents=True, exist_ok=True)
                    self.stats['dirs'] += 1
                    self.log(f"[目录] {current_path}")
                else:
                    current_path.parent.mkdir(parents=True, exist_ok=True)
                    # 创建空文件
                    with open(current_path, 'w', encoding='utf-8') as f:
                        pass
                    self.stats['files'] += 1
                    self.log(f"[文件] {current_path}")
            except Exception as e:
                self.stats['errors'] += 1
                self.log(f"[错误] {current_path}: {str(e)}")
    
    def _parse_line(self, line):
        """解析单行，返回(名称, 缩进级别)"""
        # 计算缩进级别（每2个空格或1个制表符为一级）
        indent = 0
        content_start = 0
        
        for i, char in enumerate(line):
            if char == ' ':
                indent += 1
            elif char == '\t':
                indent += 2  # 制表符算2个空格
            else:
                content_start = i
                break
        
        indent_level = indent // 2
        content = line[content_start:].strip()
        
        # 移除树形符号
        content = re.sub(r'^[├└]──?\s*', '', content)
        content = re.sub(r'^[│┃]\s*', '', content)
        content = re.sub(r'^[├└][─\-]\s*', '', content)
        content = re.sub(r'^[\│\|\+]\s*', '', content)
        
        # 移除注释（# 后面的内容）
        content = re.sub(r'\s+#.*$', '', content).strip()
        
        return content if content else None, indent_level


class Application(tk.Tk):
    """主应用程序窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.title("目录结构创建工具 v2.0")
        self.geometry("800x650")
        self.minsize(700, 500)
        
        # 设置图标（如果有的话）
        try:
            self.iconbitmap('icon.ico')
        except:
            pass
        
        # 配置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 创建界面
        self._create_widgets()
        
        # 居中窗口
        self.center_window()
    
    def center_window(self):
        """窗口居中"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """创建界面组件"""
        
        # ===== 顶部标题 =====
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        ttk.Label(
            header_frame,
            text="📁 目录结构创建工具",
            font=("Microsoft YaHei", 16, "bold")
        ).pack(anchor=tk.W)
        
        ttk.Label(
            header_frame,
            text="粘贴目录树结构文本，自动创建对应的文件和文件夹",
            foreground="gray"
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # ===== 目标目录选择 =====
        dir_frame = ttk.LabelFrame(self, text="目标目录", padding=10)
        dir_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        dir_inner = ttk.Frame(dir_frame)
        dir_inner.pack(fill=tk.X)
        
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        self.output_entry = ttk.Entry(
            dir_inner,
            textvariable=self.output_dir_var,
            font=("Consolas", 10)
        )
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            dir_inner,
            text="浏览...",
            command=self._browse_directory,
            width=10
        ).pack(side=tk.RIGHT)
        
        # ===== 目录树输入区域 =====
        input_frame = ttk.LabelFrame(self, text="目录树结构", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # 工具栏
        toolbar = ttk.Frame(input_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            toolbar,
            text="清空",
            command=self._clear_input,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar,
            text="粘贴示例",
            command=self._paste_example,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar,
            text="从文件加载",
            command=self._load_from_file,
            width=12
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            toolbar,
            text="支持格式：├── file.txt, └── dir/",
            foreground="gray"
        ).pack(side=tk.RIGHT)
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            font=("Consolas", 10),
            wrap=tk.NONE,
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # ===== 创建按钮 =====
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.create_btn = ttk.Button(
            btn_frame,
            text="🚀 开始创建",
            command=self._start_creation,
            style="Accent.TButton"
        )
        self.create_btn.pack(fill=tk.X, ipady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(
            btn_frame,
            mode='indeterminate'
        )
        
        # ===== 日志输出区域 =====
        log_frame = ttk.LabelFrame(self, text="输出日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            height=8,
            state=tk.DISABLED,
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志文本颜色标签
        self.log_text.tag_configure("success", foreground="#4ec9b0")
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("info", foreground="#569cd6")
        
        # ===== 状态栏 =====
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            foreground="gray"
        ).pack(side=tk.LEFT)
        
        self.stats_var = tk.StringVar(value="")
        ttk.Label(
            status_frame,
            textvariable=self.stats_var,
            foreground="gray"
        ).pack(side=tk.RIGHT)
    
    def _browse_directory(self):
        """选择目标目录"""
        directory = filedialog.askdirectory(
            title="选择目标目录",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def _clear_input(self):
        """清空输入"""
        self.input_text.delete(1.0, tk.END)
    
    def _paste_example(self):
        """粘贴示例目录树"""
        example = """MyProject/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/
│   │   │       ├── MainActivity.java
│   │   │       ├── data/
│   │   │       │   ├── model/
│   │   │       │   │   ├── User.java
│   │   │       │   │   └── Product.java
│   │   │       │   └── api/
│   │   │       │       └── ApiService.java
│   │   │       └── view/
│   │   │           └── adapter/
│   │   │               └── UserAdapter.java
│   │   └── res/
│   │       ├── layout/
│   │       │   └── activity_main.xml
│   │       └── values/
│   │           ├── strings.xml
│   │           └── colors.xml
│   └── test/
├── build.gradle
└── README.md"""
        
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, example)
    
    def _load_from_file(self):
        """从文件加载目录树"""
        filepath = filedialog.askopenfilename(
            title="选择目录树文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(1.0, content)
                self.log_message(f"已加载文件: {filepath}", "info")
            except Exception as e:
                messagebox.showerror("错误", f"无法读取文件: {str(e)}")
    
    def log_message(self, message, tag=""):
        """在日志区域显示消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _start_creation(self):
        """开始创建目录结构"""
        # 获取输入
        tree_text = self.input_text.get(1.0, tk.END).strip()
        if not tree_text:
            messagebox.showwarning("警告", "请先粘贴目录树结构！")
            return
        
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("警告", "请指定目标目录！")
            return
        
        # 检查目录是否存在
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建目标目录: {str(e)}")
                return
        
        # 禁用按钮，显示进度条
        self.create_btn.config(state=tk.DISABLED, text="⏳ 正在创建...")
        self.progress.pack(fill=tk.X, pady=(5, 0))
        self.progress.start(10)
        self.status_var.set("正在处理...")
        
        # 清空日志
        self.clear_log()
        self.log_message(f"目标目录: {output_dir}", "info")
        self.log_message("="*50, "info")
        
        # 在新线程中执行创建操作
        thread = threading.Thread(
            target=self._do_creation,
            args=(tree_text, output_dir),
            daemon=True
        )
        thread.start()
    
    def _do_creation(self, tree_text, output_dir):
        """执行创建操作（在线程中运行）"""
        creator = DirectoryCreator(
            base_path=output_dir,
            callback=lambda msg: self.after(0, self._on_log, msg)
        )
        
        try:
            creator.create_from_text(tree_text)
            
            # 更新UI（在主线程中）
            self.after(0, self._on_complete, creator.stats)
        except Exception as e:
            self.after(0, self._on_error, str(e))
    
    def _on_log(self, message):
        """处理日志回调"""
        if "错误" in message or "error" in message.lower():
            self.log_message(message, "error")
        elif "目录" in message:
            self.log_message(message, "info")
        else:
            self.log_message(message, "success")
    
    def _on_complete(self, stats):
        """创建完成回调"""
        self.progress.stop()
        self.progress.pack_forget()
        self.create_btn.config(state=tk.NORMAL, text="🚀 开始创建")
        
        self.log_message("="*50, "info")
        self.log_message(f"✅ 创建完成！", "success")
        self.log_message(f"   目录: {stats['dirs']} 个", "info")
        self.log_message(f"   文件: {stats['files']} 个", "info")
        if stats['errors'] > 0:
            self.log_message(f"   错误: {stats['errors']} 个", "error")
        
        self.status_var.set("完成")
        self.stats_var.set(f"目录:{stats['dirs']} | 文件:{stats['files']} | 错误:{stats['errors']}")
        
        # 询问是否打开目录
        if messagebox.askyesno("完成", f"创建完成！\n目录: {stats['dirs']} 个\n文件: {stats['files']} 个\n\n是否打开目标文件夹？"):
            os.startfile(self.output_dir_var.get())
    
    def _on_error(self, error_msg):
        """错误回调"""
        self.progress.stop()
        self.progress.pack_forget()
        self.create_btn.config(state=tk.NORMAL, text="🚀 开始创建")
        
        self.log_message(f"❌ 发生错误: {error_msg}", "error")
        self.status_var.set("错误")
        messagebox.showerror("错误", f"创建过程中发生错误:\n{error_msg}")


def main():
    """程序入口"""
    app = Application()
    app.mainloop()


if __name__ == '__main__':
    main()