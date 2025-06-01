import librosa
import numpy as np
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import soundfile as sf
matplotlib.use("TkAgg")

class MP3ToWinsoundApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MP3到Winsound.Beep转换器(此版本mp3格式文件名必须用英文，不然报错！)")
        self.geometry("800x600")
        self.mp3_file = None
        self.output_file = None
        self.function_counter = 0  # 添加这行
        self.setup_ui()
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        ttk.Button(file_frame, text="浏览...", command=self.browse_file).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 转换选项区域
        options_frame = ttk.LabelFrame(main_frame, text="转换选项")
        options_frame.pack(fill=tk.X, pady=5)
        
        # 转换模式选择
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        self.mode_var = tk.StringVar(value="1")
        ttk.Radiobutton(mode_frame, text="单线程转换 (适合简单的单音轨音乐)", variable=self.mode_var, value="1").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="多线程转换 (适合复杂的多音轨音乐)", variable=self.mode_var, value="2").pack(anchor=tk.W, padx=5, pady=2)
        
        # 持续时间模式选择
        duration_mode_frame = ttk.Frame(options_frame)
        duration_mode_frame.pack(fill=tk.X, pady=5)
        
        self.duration_mode_var = tk.StringVar(value="fixed")
        ttk.Radiobutton(duration_mode_frame, text="固定持续时间", variable=self.duration_mode_var, value="fixed", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(duration_mode_frame, text="动态持续时间", variable=self.duration_mode_var, value="dynamic", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(duration_mode_frame, text="自动检测", variable=self.duration_mode_var, value="auto", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=5)
        
        # 固定持续时间设置
        self.fixed_duration_frame = ttk.Frame(options_frame)
        self.fixed_duration_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.fixed_duration_frame, text="最小音调持续时间(秒):").pack(side=tk.LEFT, padx=5)
        self.min_duration_var = tk.DoubleVar(value=0.5)
        ttk.Entry(self.fixed_duration_frame, textvariable=self.min_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 动态持续时间设置
        self.dynamic_duration_frame = ttk.Frame(options_frame)
        
        # 最短持续时间
        min_dur_frame = ttk.Frame(self.dynamic_duration_frame)
        min_dur_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_dur_frame, text="最短持续时间(秒):").pack(side=tk.LEFT, padx=5)
        self.min_dynamic_duration_var = tk.DoubleVar(value=0.1)
        ttk.Entry(min_dur_frame, textvariable=self.min_dynamic_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 频率差异阈值
        freq_diff_frame = ttk.Frame(self.dynamic_duration_frame)
        freq_diff_frame.pack(fill=tk.X, pady=2)
        ttk.Label(freq_diff_frame, text="频率差异阈值(Hz):").pack(side=tk.LEFT, padx=5)
        self.freq_diff_threshold_var = tk.DoubleVar(value=20.0)
        ttk.Entry(freq_diff_frame, textvariable=self.freq_diff_threshold_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(freq_diff_frame, text="(小于此值的相邻音符将被合并)").pack(side=tk.LEFT, padx=5)
        
        # 自动检测设置
        self.auto_detection_frame = ttk.Frame(options_frame)
        
        # 最短持续时间
        auto_min_dur_frame = ttk.Frame(self.auto_detection_frame)
        auto_min_dur_frame.pack(fill=tk.X, pady=2)
        ttk.Label(auto_min_dur_frame, text="最短持续时间(秒):").pack(side=tk.LEFT, padx=5)
        self.auto_min_duration_var = tk.DoubleVar(value=0.1)
        ttk.Entry(auto_min_dur_frame, textvariable=self.auto_min_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 频率差异阈值
        auto_freq_diff_frame = ttk.Frame(self.auto_detection_frame)
        auto_freq_diff_frame.pack(fill=tk.X, pady=2)
        ttk.Label(auto_freq_diff_frame, text="频率差异阈值(Hz):").pack(side=tk.LEFT, padx=5)
        self.auto_freq_diff_var = tk.DoubleVar(value=300.0)
        ttk.Entry(auto_freq_diff_frame, textvariable=self.auto_freq_diff_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 低频阈值
        low_freq_frame = ttk.Frame(self.auto_detection_frame)
        low_freq_frame.pack(fill=tk.X, pady=2)
        ttk.Label(low_freq_frame, text="低频阈值(Hz):").pack(side=tk.LEFT, padx=5)
        self.low_freq_threshold_var = tk.DoubleVar(value=400.0)
        ttk.Entry(low_freq_frame, textvariable=self.low_freq_threshold_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(low_freq_frame, text="(低于此值的频率用sleep代替)").pack(side=tk.LEFT, padx=5)
        
        # 转换按钮
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="开始转换", command=self.start_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="运行生成的代码", command=self.run_generated_code).pack(side=tk.LEFT, padx=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(button_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # 创建选项卡控件
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 日志选项卡
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="转换日志")
        
        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 可视化选项卡
        viz_frame = ttk.Frame(notebook)
        notebook.add(viz_frame, text="音频可视化")
        
        # 创建matplotlib图形
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 代码预览选项卡
        code_frame = ttk.Frame(notebook)
        notebook.add(code_frame, text="生成代码预览")
        
        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD)
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=2)
        
        # 初始化界面状态
        self.on_duration_mode_change()
        
        # 初始日志
        self.log("欢迎使用MP3到Winsound.Beep转换器！")
        self.log("请选择一个MP3文件并设置转换选项。")
    
    def on_duration_mode_change(self):
        """持续时间模式改变时的回调"""
        mode = self.duration_mode_var.get()
        
        # 隐藏所有设置框架
        self.fixed_duration_frame.pack_forget()
        self.dynamic_duration_frame.pack_forget()
        self.auto_detection_frame.pack_forget()
        
        # 根据选择显示对应的设置框架
        if mode == "fixed":
            self.fixed_duration_frame.pack(fill=tk.X, pady=5)
        elif mode == "dynamic":
            self.dynamic_duration_frame.pack(fill=tk.X, pady=5)
        elif mode == "auto":
            self.auto_detection_frame.pack(fill=tk.X, pady=5)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="选择MP3文件",
            filetypes=[("MP3文件", "*.mp3"), ("所有文件", "*.*")]
        )
        if file_path:
            self.mp3_file = file_path
            self.file_path_var.set(file_path)
            self.log(f"已选择文件: {file_path}")
            self.status_var.set(f"已选择: {os.path.basename(file_path)}")
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()
    
    def start_conversion(self):
        if not self.mp3_file:
            messagebox.showerror("错误", "请先选择一个MP3文件！")
            return
        
        if not os.path.exists(self.mp3_file):
            messagebox.showerror("错误", f"文件不存在: {self.mp3_file}")
            return
        
        # 禁用按钮，防止重复点击
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(state="disabled")
        
        # 清空日志和代码预览
        self.log_text.delete(1.0, tk.END)
        self.code_text.delete(1.0, tk.END)
        
        # 重置进度条
        self.progress_var.set(0)
        
        # 在新线程中执行转换，避免UI冻结
        self.conversion_thread = threading.Thread(target=self.convert_mp3)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
    
    def convert_mp3(self):
        try:
            self.status_var.set("正在转换...")
            mode = self.mode_var.get()
            
            if mode == "1":
                self.output_file = self.mp3_to_winsound(self.mp3_file)
            else:
                self.output_file = self.play_mp3_with_threads(self.mp3_file)
            
            self.status_var.set(f"转换完成: {os.path.basename(self.output_file)}")
            
            # 读取生成的代码并显示在代码预览中
            with open(self.output_file, 'r', encoding='utf-8') as f:
                code = f.read()
                self.code_text.insert(tk.END, code)
            
            # 启用按钮
            self.enable_buttons()
            
            messagebox.showinfo("转换完成", f"MP3文件已成功转换为Winsound.beep代码！\n\n输出文件: {self.output_file}")
            
        except Exception as e:
            self.log(f"转换过程中出错: {str(e)}")
            self.status_var.set("转换失败")
            messagebox.showerror("错误", f"转换过程中出错:\n{str(e)}")
            self.enable_buttons()
    
    def enable_buttons(self):
        # 在主线程中启用按钮
        self.after(0, lambda: [widget.configure(state="normal") for widget in self.winfo_children() if isinstance(widget, ttk.Button)])
    
    def run_generated_code(self):
        if not self.output_file or not os.path.exists(self.output_file):
            messagebox.showerror("错误", "请先转换MP3文件！")
            return
        
        try:
            self.log(f"正在运行生成的代码: {self.output_file}")
            self.status_var.set(f"正在播放: {os.path.basename(self.output_file)}")
            
            # 在新线程中运行生成的代码
            threading.Thread(target=self.execute_code, daemon=True).start()
            
        except Exception as e:
            self.log(f"运行代码时出错: {str(e)}")
            messagebox.showerror("错误", f"运行代码时出错:\n{str(e)}")
    
    def execute_code(self):
        try:
            exec(open(self.output_file, encoding='utf-8').read())
            self.after(0, lambda: self.status_var.set("播放完成"))
            self.after(0, lambda: self.log("播放完成"))
        except Exception as e:
            self.after(0, lambda: self.log(f"播放时出错: {str(e)}"))
            self.after(0, lambda: self.status_var.set("播放失败"))
    
    def analyze_frequencies(self, y, sr):
        """分析音频的主要频率"""
        # 使用短时傅里叶变换分析频率
        hop_length = 512
        frame_length = 2048
        
        # 计算频谱
        stft = librosa.stft(y, hop_length=hop_length, n_fft=frame_length)
        magnitude = np.abs(stft)
        
        # 获取频率轴
        freqs = librosa.fft_frequencies(sr=sr, n_fft=frame_length)
        
        frequencies = []
        durations = []
        
        # 分析每个时间帧
        for i in range(magnitude.shape[1]):
            # 找到最强的频率分量
            max_idx = np.argmax(magnitude[:, i])
            dominant_freq = freqs[max_idx]
            
            # 过滤掉太低或太高的频率
            if 80 <= dominant_freq <= 2000:
                frequencies.append(int(dominant_freq))
                durations.append(hop_length / sr)
        
        return frequencies, durations
    
    def process_auto_detection(self, frequencies, durations):
        """自动检测模式：智能处理音频段落"""
        min_duration = self.auto_min_duration_var.get()
        freq_threshold = self.auto_freq_diff_var.get()
        low_freq_threshold = self.low_freq_threshold_var.get()
        
        if not frequencies:
            return [], []
        
        processed_freqs = []
        processed_durations = []
        
        i = 0
        while i < len(frequencies):
            current_freq = frequencies[i]
            current_duration = durations[i]
            
            # 收集相似频率的段落
            freq_group = [current_freq]
            duration_group = [current_duration]
            total_duration = current_duration
            
            j = i + 1
            while j < len(frequencies) and total_duration < min_duration:
                next_freq = frequencies[j]
                next_duration = durations[j]
                
                # 检查频率差异
                if abs(next_freq - current_freq) <= freq_threshold:
                    freq_group.append(next_freq)
                    duration_group.append(next_duration)
                    total_duration += next_duration
                    j += 1
                else:
                    break
            
            # 如果总持续时间超过最短持续时间
            if total_duration >= min_duration:
                # 选择最合适的频率（出现次数最多的）
                freq_counts = {}
                for freq in freq_group:
                    freq_counts[freq] = freq_counts.get(freq, 0) + 1
                
                best_freq = max(freq_counts, key=freq_counts.get)
                
                # 检查是否为低频
                if best_freq < low_freq_threshold:
                    # 使用sleep代替
                    processed_freqs.append(0)  # 0表示sleep
                    processed_durations.append(total_duration)
                else:
                    processed_freqs.append(best_freq)
                    processed_durations.append(total_duration)
            
            i = j if j > i + 1 else i + 1
        
        return processed_freqs, processed_durations
    
    def mp3_to_winsound(self, mp3_file, output_file=None, function_name=None):
        """将MP3文件转换为使用winsound.beep播放的Python代码"""
        # 如果未指定函数名，则使用main或main_xx格式
        if function_name is None:
            if self.function_counter == 0:
                function_name = "main"
            else:
                function_name = f"main_{self.function_counter:02d}"
            self.function_counter += 1
        
        # 如果未指定输出文件，则使用与输入文件相同的名称但扩展名为.py
        if output_file is None:
            output_file = os.path.splitext(mp3_file)[0] + "_winsound.py"
        
        try:
            self.log("开始加载音频文件...")
            self.progress_var.set(10)
            
            # 加载音频文件
            y, sr = librosa.load(mp3_file, sr=None)
            self.log(f"音频加载完成，采样率: {sr} Hz，时长: {len(y)/sr:.2f} 秒")
            
            self.progress_var.set(30)
            self.log("分析音频频率...")
            
            # 分析音频频率
            frequencies, durations = self.analyze_frequencies(y, sr)
            self.log(f"频率分析完成，检测到 {len(frequencies)} 个频率段")
            
            self.progress_var.set(50)
            self.log("处理音频段落...")
            
            # 根据模式处理音频段落
            duration_mode = self.duration_mode_var.get()
            if duration_mode == "fixed":
                processed_freqs, processed_durations = self.merge_short_segments(frequencies, durations)
                self.log(f"固定模式：段落合并完成，最终 {len(processed_freqs)} 个音调段")
            elif duration_mode == "dynamic":
                processed_freqs, processed_durations = self.process_dynamic_segments(frequencies, durations)
                self.log(f"动态模式：段落处理完成，最终 {len(processed_freqs)} 个音调段")
            else:  # auto
                processed_freqs, processed_durations = self.process_auto_detection(frequencies, durations)
                self.log(f"自动检测模式：段落处理完成，最终 {len(processed_freqs)} 个音调段")
            
            self.progress_var.set(70)
            self.log("生成可视化...")
            
            # 显示可视化
            self.visualize_audio(processed_freqs, processed_durations)
            
            self.progress_var.set(90)
            self.log("生成Python代码...")
            
            # 生成代码
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 由MP3文件 '{mp3_file}' 自动生成的winsound.beep播放代码\n")
                f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 音频信息: 采样率 {sr} Hz, 时长 {len(y)/sr:.2f} 秒\n")
                f.write(f"# 音调数量: {len(processed_freqs)}\n\n")
                f.write("import winsound\n")
                f.write("import time\n\n")
                f.write(f"def {function_name}():\n")
                f.write('    """播放转换后的音频"""\n')
                f.write("    print('开始播放音频...')\n")
                
                for i, (freq, duration) in enumerate(zip(processed_freqs, processed_durations)):
                    if freq == 0:  # sleep
                        f.write(f"    time.sleep({duration:.3f})  # 静音段\n")
                    else:
                        f.write(f"    winsound.Beep({freq}, {int(duration * 1000)})\n")
                
                f.write("    print('播放完成！')\n\n")
                f.write(f"if __name__ == '__main__':\n")
                f.write(f"    {function_name}()\n")
            
            self.progress_var.set(100)
            self.log(f"转换完成！生成文件: {output_file}")
            
            return output_file
            
        except Exception as e:
            self.log(f"转换失败: {str(e)}")
            raise e
    
    def merge_short_segments(self, frequencies, durations):
        """固定模式：合并短时间段"""
        min_duration = self.min_duration_var.get()
        merged_freqs = []
        merged_durations = []
        
        if not frequencies:
            return merged_freqs, merged_durations
        
        current_freq = frequencies[0]
        current_duration = durations[0]
        freq_counts = {current_freq: 1}
        
        for i in range(1, len(frequencies)):
            freq = frequencies[i]
            duration = durations[i]
            
            if current_duration < min_duration:
                current_duration += duration
                if freq in freq_counts:
                    freq_counts[freq] += 1
                else:
                    freq_counts[freq] = 1
            else:
                best_freq = max(freq_counts, key=freq_counts.get)
                merged_freqs.append(best_freq)
                merged_durations.append(current_duration)
                
                current_freq = freq
                current_duration = duration
                freq_counts = {freq: 1}
        
        if freq_counts:
            best_freq = max(freq_counts, key=freq_counts.get)
            merged_freqs.append(best_freq)
            merged_durations.append(max(current_duration, min_duration))
        
        return merged_freqs, merged_durations
    
    def process_dynamic_segments(self, frequencies, durations):
        """动态模式：根据频率差异和最短时间处理段落"""
        min_duration = self.min_dynamic_duration_var.get()
        freq_threshold = self.freq_diff_threshold_var.get()
        
        if not frequencies:
            return [], []
        
        processed_freqs = []
        processed_durations = []
        
        current_freq = frequencies[0]
        current_duration = durations[0]
        freq_sum = current_freq * current_duration
        total_duration = current_duration
        
        for i in range(1, len(frequencies)):
            freq = frequencies[i]
            duration = durations[i]
            
            # 检查频率差异和当前持续时间
            freq_diff = abs(freq - current_freq)
            
            if (freq_diff <= freq_threshold and current_duration < min_duration) or current_duration < min_duration:
                # 合并段落
                freq_sum += freq * duration
                total_duration += duration
                current_duration = total_duration
            else:
                # 输出当前段落
                avg_freq = int(freq_sum / total_duration)
                processed_freqs.append(avg_freq)
                processed_durations.append(total_duration)
                
                # 开始新段落
                current_freq = freq
                current_duration = duration
                freq_sum = freq * duration
                total_duration = duration
        
        # 处理最后一个段落
        if total_duration > 0:
            avg_freq = int(freq_sum / total_duration)
            processed_freqs.append(avg_freq)
            processed_durations.append(max(total_duration, min_duration))
        
        return processed_freqs, processed_durations
    
    def visualize_audio(self, frequencies, durations):
        """可视化音频频率和持续时间"""
        self.ax.clear()
        
        if not frequencies:
            self.ax.text(0.5, 0.5, '没有可视化数据', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # 创建时间轴
        time_points = []
        current_time = 0
        for duration in durations:
            time_points.append(current_time)
            current_time += duration
        
        # 绘制频率图
        self.ax.plot(time_points, frequencies, 'b-', linewidth=2, marker='o', markersize=4)
        self.ax.set_xlabel('时间 (秒)')
        self.ax.set_ylabel('频率 (Hz)')
        self.ax.set_title('音频频率分析')
        self.ax.grid(True, alpha=0.3)
        
        # 设置y轴范围
        if frequencies:
            min_freq = min(f for f in frequencies if f > 0)
            max_freq = max(frequencies)
            self.ax.set_ylim(min_freq * 0.9, max_freq * 1.1)
        
        self.canvas.draw()
    
    def play_mp3_with_threads(self, mp3_file):
        """多线程版本的MP3转换"""
        # 这里可以实现多线程版本，暂时使用单线程版本
        return self.mp3_to_winsound(mp3_file)
    
if __name__ == "__main__":
    app = MP3ToWinsoundApp()
    app.mainloop()