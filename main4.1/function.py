import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import os
import soundfile as sf

class MP3ToWinsoundApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MP3到Winsound.Beep转换器(此版本mp3格式文件名必须用英文，不然报错！)")
        self.geometry("800x600")
        self.mp3_file = None
        self.output_file = None
        self.function_counter = 0
        self.setup_ui()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="选择MP3文件", command=self.select_mp3_file).pack(side=tk.LEFT, padx=5, pady=5)
        self.file_label = ttk.Label(file_frame, text="未选择文件")
        self.file_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 转换选项区域
        options_frame = ttk.LabelFrame(main_frame, text="转换选项")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 转换模式选择
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(mode_frame, text="转换模式:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="单线程", variable=self.mode_var, value="single").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="多线程", variable=self.mode_var, value="multi").pack(side=tk.LEFT)
        
        # 持续时间模式选择
        duration_mode_frame = ttk.Frame(options_frame)
        duration_mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(duration_mode_frame, text="持续时间模式:").pack(side=tk.LEFT)
        self.duration_mode_var = tk.StringVar(value="fixed")
        ttk.Radiobutton(duration_mode_frame, text="固定持续时间", variable=self.duration_mode_var, value="fixed", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(duration_mode_frame, text="动态持续时间", variable=self.duration_mode_var, value="dynamic", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(duration_mode_frame, text="自动检测", variable=self.duration_mode_var, value="auto", command=self.on_duration_mode_change).pack(side=tk.LEFT)
        
        # 固定持续时间设置
        self.fixed_duration_frame = ttk.Frame(options_frame)
        self.fixed_duration_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.fixed_duration_frame, text="固定持续时间(秒):").pack(side=tk.LEFT)
        self.fixed_duration_var = tk.DoubleVar(value=0.5)
        ttk.Entry(self.fixed_duration_frame, textvariable=self.fixed_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 动态持续时间设置
        self.dynamic_duration_frame = ttk.Frame(options_frame)
        
        ttk.Label(self.dynamic_duration_frame, text="最短持续时间(秒):").pack(side=tk.LEFT)
        self.min_duration_var = tk.DoubleVar(value=0.1)
        ttk.Entry(self.dynamic_duration_frame, textvariable=self.min_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.dynamic_duration_frame, text="频率差异阈值(Hz):").pack(side=tk.LEFT, padx=(20, 0))
        self.freq_threshold_var = tk.DoubleVar(value=50.0)
        ttk.Entry(self.dynamic_duration_frame, textvariable=self.freq_threshold_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 自动检测设置
        self.auto_detection_frame = ttk.Frame(options_frame)
        
        ttk.Label(self.auto_detection_frame, text="最短持续时间(秒):").pack(side=tk.LEFT)
        self.auto_min_duration_var = tk.DoubleVar(value=0.1)
        ttk.Entry(self.auto_detection_frame, textvariable=self.auto_min_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.auto_detection_frame, text="频率差异阈值(Hz):").pack(side=tk.LEFT, padx=(10, 0))
        self.auto_freq_threshold_var = tk.DoubleVar(value=50.0)
        ttk.Entry(self.auto_detection_frame, textvariable=self.auto_freq_threshold_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.auto_detection_frame, text="低频阈值(Hz):").pack(side=tk.LEFT, padx=(10, 0))
        self.low_freq_threshold_var = tk.DoubleVar(value=100.0)
        ttk.Entry(self.auto_detection_frame, textvariable=self.low_freq_threshold_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 音频可视化选项
        viz_frame = ttk.Frame(options_frame)
        viz_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.show_waveform_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="显示波形图", variable=self.show_waveform_var).pack(side=tk.LEFT)
        
        self.show_spectrogram_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="显示频谱图", variable=self.show_spectrogram_var).pack(side=tk.LEFT, padx=20)
        
        # 按钮区域
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 日志选项卡
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="日志")
        
        self.log_text = tk.Text(log_frame, height=10)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 音频可视化选项卡
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="音频可视化")
        
        # 生成代码预览选项卡
        code_frame = ttk.Frame(self.notebook)
        self.notebook.add(code_frame, text="生成代码预览")
        
        self.code_text = tk.Text(code_frame, height=10)
        code_scrollbar = ttk.Scrollbar(code_frame, orient=tk.VERTICAL, command=self.code_text.yview)
        self.code_text.configure(yscrollcommand=code_scrollbar.set)
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        code_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始化时隐藏动态和自动检测设置
        self.on_duration_mode_change()

    def on_duration_mode_change(self):
        """根据选择的持续时间模式显示相应的设置"""
        mode = self.duration_mode_var.get()
        
        # 隐藏所有设置框架
        self.fixed_duration_frame.pack_forget()
        self.dynamic_duration_frame.pack_forget()
        self.auto_detection_frame.pack_forget()
        
        # 根据模式显示相应的设置
        if mode == "fixed":
            self.fixed_duration_frame.pack(fill=tk.X, padx=5, pady=5)
        elif mode == "dynamic":
            self.dynamic_duration_frame.pack(fill=tk.X, padx=5, pady=5)
        elif mode == "auto":
            self.auto_detection_frame.pack(fill=tk.X, padx=5, pady=5)

    def log(self, message):
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.update_idletasks()

    def select_mp3_file(self):
        """选择MP3文件"""
        file_path = filedialog.askopenfilename(
            title="选择MP3文件",
            filetypes=[("MP3文件", "*.mp3"), ("所有文件", "*.*")]
        )
        if file_path:
            self.mp3_file = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.log(f"已选择文件: {file_path}")

    def enable_buttons(self, enabled=True):
        """启用或禁用按钮"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.convert_button.config(state=state)

    def start_conversion(self):
        """开始转换过程"""
        if not self.mp3_file:
            messagebox.showerror("错误", "请先选择MP3文件")
            return
        
        self.enable_buttons(False)
        self.progress_var.set(0)
        
        # 根据选择的模式进行转换
        if self.mode_var.get() == "single":
            # 单线程转换
            threading.Thread(target=self.convert_mp3, daemon=True).start()
        else:
            # 多线程转换
            threading.Thread(target=self.convert_mp3_multithread, daemon=True).start()

    def convert_mp3(self):
        """转换MP3文件"""
        try:
            self.log("开始转换过程...")
            
            # 获取转换参数
            duration_mode = self.duration_mode_var.get()
            
            if duration_mode == "fixed":
                fixed_duration = self.fixed_duration_var.get()
                result = self.mp3_to_winsound(self.mp3_file, fixed_duration=fixed_duration)
            elif duration_mode == "dynamic":
                min_duration = self.min_duration_var.get()
                freq_threshold = self.freq_threshold_var.get()
                result = self.mp3_to_winsound(self.mp3_file, min_duration=min_duration, freq_threshold=freq_threshold, use_dynamic=True)
            else:  # auto
                min_duration = self.auto_min_duration_var.get()
                freq_threshold = self.auto_freq_threshold_var.get()
                low_freq_threshold = self.low_freq_threshold_var.get()
                result = self.mp3_to_winsound(self.mp3_file, min_duration=min_duration, freq_threshold=freq_threshold, low_freq_threshold=low_freq_threshold, use_auto_detection=True)
            
            if result:
                self.log("转换完成！")
                messagebox.showinfo("成功", "转换完成！")
            else:
                self.log("转换失败")
                messagebox.showerror("错误", "转换失败")
                
        except Exception as e:
            self.log(f"转换过程中出错: {str(e)}")
            messagebox.showerror("错误", f"转换过程中出错: {str(e)}")
        finally:
            self.enable_buttons(True)
            self.progress_var.set(100)

    def convert_mp3_multithread(self):
        """多线程转换MP3文件"""
        # 这里可以实现多线程版本，暂时使用单线程版本
        self.convert_mp3()

    def analyze_frequencies(self, y, sr, hop_length=512):
        """分析音频的主要频率"""
        self.log("正在分析音频频率...")
        
        # 计算短时傅里叶变换
        stft = librosa.stft(y, hop_length=hop_length)
        magnitude = np.abs(stft)
        
        # 获取频率和时间轴
        freqs = librosa.fft_frequencies(sr=sr)
        times = librosa.frames_to_time(np.arange(magnitude.shape[1]), sr=sr, hop_length=hop_length)
        
        # 找到每个时间帧的主要频率
        main_freqs = []
        for i in range(magnitude.shape[1]):
            # 找到幅度最大的频率
            max_freq_idx = np.argmax(magnitude[:, i])
            main_freq = freqs[max_freq_idx]
            
            # 限制频率范围在人耳可听范围内
            if 20 <= main_freq <= 20000:
                main_freqs.append(main_freq)
            else:
                # 如果主频率超出范围，找到范围内幅度最大的频率
                valid_indices = np.where((freqs >= 20) & (freqs <= 20000))[0]
                if len(valid_indices) > 0:
                    valid_magnitudes = magnitude[valid_indices, i]
                    max_valid_idx = valid_indices[np.argmax(valid_magnitudes)]
                    main_freqs.append(freqs[max_valid_idx])
                else:
                    main_freqs.append(440)  # 默认A4音符
        
        self.log(f"分析完成，共{len(main_freqs)}个频率点")
        return main_freqs, times

    def merge_short_segments(self, frequencies, times, min_duration):
        """合并持续时间过短的音频段"""
        self.log(f"正在合并短于{min_duration}秒的音频段...")
        
        if len(frequencies) == 0:
            return [], []
        
        merged_freqs = []
        merged_durations = []
        
        current_freq = frequencies[0]
        current_start_time = times[0] if len(times) > 0 else 0
        
        for i in range(1, len(frequencies)):
            current_time = times[i] if i < len(times) else times[-1] + (times[-1] - times[-2] if len(times) > 1 else 0.1)
            duration = current_time - current_start_time
            
            if duration >= min_duration:
                merged_freqs.append(current_freq)
                merged_durations.append(duration)
                current_freq = frequencies[i]
                current_start_time = current_time
            # 如果持续时间太短，继续累积
        
        # 处理最后一个段
        if len(times) > 0:
            final_duration = times[-1] - current_start_time + (times[-1] - times[-2] if len(times) > 1 else 0.1)
            if final_duration >= min_duration:
                merged_freqs.append(current_freq)
                merged_durations.append(final_duration)
        
        self.log(f"合并完成，从{len(frequencies)}个段合并为{len(merged_freqs)}个段")
        return merged_freqs, merged_durations

    def process_dynamic_segments(self, frequencies, times, min_duration, freq_threshold):
        """处理动态持续时间的音频段"""
        self.log(f"正在处理动态音频段，最短时间{min_duration}秒，频率阈值{freq_threshold}Hz...")
        
        if len(frequencies) == 0:
            return [], []
        
        processed_freqs = []
        processed_durations = []
        
        i = 0
        while i < len(frequencies):
            current_freq = frequencies[i]
            start_time = times[i] if i < len(times) else 0
            
            # 寻找相似频率的连续段
            j = i + 1
            while j < len(frequencies):
                if abs(frequencies[j] - current_freq) <= freq_threshold:
                    j += 1
                else:
                    break
            
            # 计算段的持续时间
            end_time = times[j-1] if j-1 < len(times) else times[-1]
            duration = end_time - start_time
            
            # 如果持续时间足够长，添加到结果中
            if duration >= min_duration:
                # 计算平均频率
                avg_freq = np.mean(frequencies[i:j])
                processed_freqs.append(avg_freq)
                processed_durations.append(duration)
            
            i = j
        
        self.log(f"动态处理完成，生成{len(processed_freqs)}个音频段")
        return processed_freqs, processed_durations

    def process_auto_detection(self, frequencies, times, min_duration, freq_threshold, low_freq_threshold):
        """自动检测模式处理音频段"""
        self.log(f"正在进行自动检测处理，最短时间{min_duration}秒，频率阈值{freq_threshold}Hz，低频阈值{low_freq_threshold}Hz...")
        
        if len(frequencies) == 0:
            return [], [], []
        
        processed_freqs = []
        processed_durations = []
        processed_types = []  # 'beep' 或 'sleep'
        
        i = 0
        while i < len(frequencies):
            current_freq = frequencies[i]
            start_time = times[i] if i < len(times) else 0
            
            # 寻找相似频率的连续段
            j = i + 1
            total_duration = 0
            while j < len(frequencies):
                if abs(frequencies[j] - current_freq) <= freq_threshold:
                    j += 1
                else:
                    break
            
            # 计算段的持续时间
            if j-1 < len(times):
                end_time = times[j-1]
                total_duration = end_time - start_time
            else:
                total_duration = min_duration  # 默认最小持续时间
            
            # 如果持续时间足够长，添加到结果中
            if total_duration >= min_duration:
                # 计算平均频率
                avg_freq = np.mean(frequencies[i:j])
                
                # 根据频率决定使用beep还是sleep
                if avg_freq >= low_freq_threshold:
                    processed_freqs.append(avg_freq)
                    processed_durations.append(total_duration)
                    processed_types.append('beep')
                else:
                    processed_freqs.append(avg_freq)
                    processed_durations.append(total_duration)
                    processed_types.append('sleep')
            
            i = j if j > i + 1 else i + 1
        
        self.log(f"自动检测完成，生成{len(processed_freqs)}个音频段")
        return processed_freqs, processed_durations, processed_types

    def mp3_to_winsound(self, mp3_file, output_file=None, function_name=None, fixed_duration=None, min_duration=0.1, freq_threshold=50.0, low_freq_threshold=100.0, use_dynamic=False, use_auto_detection=False):
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
            y, sr = librosa.load(mp3_file)
            self.log(f"音频加载完成，采样率: {sr} Hz，时长: {len(y)/sr:.2f} 秒")
            
            self.progress_var.set(30)
            
            # 分析频率
            frequencies, times = self.analyze_frequencies(y, sr)
            
            self.progress_var.set(50)
            
            # 根据模式处理音频段
            if use_auto_detection:
                processed_freqs, processed_durations, processed_types = self.process_auto_detection(
                    frequencies, times, min_duration, freq_threshold, low_freq_threshold
                )
            elif use_dynamic:
                processed_freqs, processed_durations = self.process_dynamic_segments(
                    frequencies, times, min_duration, freq_threshold
                )
                processed_types = ['beep'] * len(processed_freqs)  # 动态模式全部使用beep
            else:
                # 固定模式
                if fixed_duration:
                    # 计算需要多少个固定时长的段
                    total_duration = len(y) / sr
                    num_segments = int(total_duration / fixed_duration)
                    
                    processed_freqs = []
                    processed_durations = []
                    
                    for i in range(num_segments):
                        start_idx = int(i * fixed_duration * sr)
                        end_idx = int((i + 1) * fixed_duration * sr)
                        if end_idx > len(y):
                            end_idx = len(y)
                        
                        # 计算该段的主要频率
                        segment = y[start_idx:end_idx]
                        if len(segment) > 0:
                            fft = np.fft.fft(segment)
                            freqs = np.fft.fftfreq(len(segment), 1/sr)
                            magnitude = np.abs(fft)
                            
                            # 只考虑正频率
                            positive_freqs = freqs[:len(freqs)//2]
                            positive_magnitude = magnitude[:len(magnitude)//2]
                            
                            # 找到幅度最大的频率
                            if len(positive_magnitude) > 0:
                                max_freq_idx = np.argmax(positive_magnitude)
                                main_freq = positive_freqs[max_freq_idx]
                                
                                # 限制频率范围
                                if 20 <= main_freq <= 20000:
                                    processed_freqs.append(main_freq)
                                else:
                                    processed_freqs.append(440)  # 默认A4
                            else:
                                processed_freqs.append(440)
                            
                            processed_durations.append(fixed_duration)
                
                processed_types = ['beep'] * len(processed_freqs)  # 固定模式全部使用beep
            
            self.progress_var.set(70)
            
            # 生成可视化
            if self.show_waveform_var.get() or self.show_spectrogram_var.get():
                self.create_visualizations(y, sr, processed_freqs, processed_durations)
            
            self.progress_var.set(80)
            
            # 生成Python代码
            self.log("正在生成Python代码...")
            python_code = self.generate_python_code(processed_freqs, processed_durations, processed_types if use_auto_detection else None, function_name, mp3_file)
            
            # 显示生成的代码
            self.code_text.delete(1.0, tk.END)
            self.code_text.insert(1.0, python_code)
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            self.log(f"Python代码已保存到: {output_file}")
            self.progress_var.set(100)
            
            return True
            
        except Exception as e:
            self.log(f"转换过程中发生错误: {str(e)}")
            return False

    def generate_python_code(self, frequencies, durations, types=None, function_name="main", original_file=""):
        """生成Python播放代码"""
        code_lines = []
        code_lines.append("import winsound")
        code_lines.append("import time")
        code_lines.append("")
        code_lines.append(f"# 从文件生成: {os.path.basename(original_file)}")
        code_lines.append(f"# 音调数量: {len(frequencies)}")
        code_lines.append(f"# 总时长: {sum(durations):.2f} 秒")
        code_lines.append("")
        code_lines.append(f"def {function_name}():")
        code_lines.append("    \"\"\"播放转换后的音频\"\"\"")
        
        for i, (freq, duration) in enumerate(zip(frequencies, durations)):
            # 确保频率在winsound.Beep的有效范围内
            freq = max(37, min(32767, int(freq)))
            duration_ms = max(1, int(duration * 1000))
            
            if types and types[i] == 'sleep':
                code_lines.append(f"    time.sleep({duration:.3f})  # 低频段，使用静音")
            else:
                code_lines.append(f"    winsound.Beep({freq}, {duration_ms})")
        
        code_lines.append("")
        code_lines.append("if __name__ == '__main__':")
        code_lines.append(f"    {function_name}()")
        
        return "\n".join(code_lines)

    def create_visualizations(self, y, sr, frequencies, durations):
        """创建音频可视化"""
        self.log("正在生成可视化图表...")
        
        # 清除之前的图表
        for widget in self.viz_frame.winfo_children():
            widget.destroy()
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        if self.show_waveform_var.get():
            # 波形图
            time_axis = np.linspace(0, len(y) / sr, len(y))
            axes[0].plot(time_axis, y)
            axes[0].set_title('音频波形')
            axes[0].set_xlabel('时间 (秒)')
            axes[0].set_ylabel('幅度')
            axes[0].grid(True)
        
        if self.show_spectrogram_var.get():
            # 频谱图
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            img = librosa.display.specshow(D, y_axis='hz', x_axis='time', sr=sr, ax=axes[1])
            axes[1].set_title('频谱图')
            plt.colorbar(img, ax=axes[1], format='%+2.0f dB')
        
        plt.tight_layout()
        
        # 将图表嵌入到tkinter中
        canvas = FigureCanvasTkAgg(fig, self.viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.log("可视化图表生成完成")

    def play_mp3_with_threads(self, mp3_file):
        """多线程版本的MP3转换"""
        # 这里可以实现多线程版本，暂时使用单线程版本
        return self.mp3_to_winsound(mp3_file)