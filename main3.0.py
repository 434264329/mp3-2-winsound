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

class ImprovedMP3ToWinsoundApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("改进版MP3到Winsound.Beep转换器")
        self.geometry("900x700")
        self.mp3_file = None
        self.output_file = None
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
        
        # 持续时间模式选择
        duration_mode_frame = ttk.Frame(options_frame)
        duration_mode_frame.pack(fill=tk.X, pady=5)
        
        self.duration_mode_var = tk.StringVar(value="fixed")
        ttk.Radiobutton(duration_mode_frame, text="固定持续时间", variable=self.duration_mode_var, value="fixed", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(duration_mode_frame, text="动态持续时间", variable=self.duration_mode_var, value="dynamic", command=self.on_duration_mode_change).pack(side=tk.LEFT, padx=5)
        
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
        
        # 音频可视化选项
        viz_frame = ttk.Frame(options_frame)
        viz_frame.pack(fill=tk.X, pady=5)
        self.show_visualization_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="显示音频可视化", variable=self.show_visualization_var).pack(side=tk.LEFT, padx=5)
        
        # 转换按钮
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="开始转换", command=self.start_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="运行生成的代码", command=self.run_generated_code).pack(side=tk.LEFT, padx=5)
        
        # 带动效的进度条
        progress_frame = ttk.LabelFrame(main_frame, text="转换进度")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="等待开始...")
        self.progress_label.pack(pady=2)
        
        # 可视化区域
        self.viz_frame = ttk.LabelFrame(main_frame, text="音频可视化")
        self.viz_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="转换日志")
        log_frame.pack(fill=tk.X, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 初始化界面状态
        self.on_duration_mode_change()
    
    def on_duration_mode_change(self):
        """持续时间模式改变时的回调"""
        if self.duration_mode_var.get() == "fixed":
            self.fixed_duration_frame.pack(fill=tk.X, pady=5)
            self.dynamic_duration_frame.pack_forget()
        else:
            self.fixed_duration_frame.pack_forget()
            self.dynamic_duration_frame.pack(fill=tk.X, pady=5)
    
    def animate_progress(self, target_value, step=1):
        """为进度条添加动画效果"""
        current = self.progress_var.get()
        if current < target_value:
            new_value = min(current + step, target_value)
            self.progress_var.set(new_value)
            self.after(50, lambda: self.animate_progress(target_value, step))
    
    def log(self, message):
        """添加日志信息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()
    
    def browse_file(self):
        """浏览并选择MP3文件"""
        file_path = filedialog.askopenfilename(
            title="选择MP3文件",
            filetypes=[("MP3文件", "*.mp3"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.mp3_file = file_path
    
    def start_conversion(self):
        """开始转换过程"""
        if not self.mp3_file:
            messagebox.showerror("错误", "请先选择MP3文件")
            return
        
        # 重置进度条
        self.progress_var.set(0)
        self.progress_label.config(text="开始转换...")
        
        # 在新线程中执行转换
        threading.Thread(target=self.convert_mp3, daemon=True).start()
    
    def convert_mp3(self):
        """改进的MP3转换方法"""
        try:
            self.log("开始加载音频文件...")
            self.animate_progress(10)
            
            # 加载音频文件
            y, sr = librosa.load(self.mp3_file, sr=None)
            self.log(f"音频加载完成，采样率: {sr} Hz，时长: {len(y)/sr:.2f} 秒")
            
            self.animate_progress(20)
            self.progress_label.config(text="分析音频频率...")
            
            # 分析音频频率
            frequencies, durations = self.analyze_frequencies(y, sr)
            self.log(f"频率分析完成，检测到 {len(frequencies)} 个频率段")
            
            self.animate_progress(40)
            self.progress_label.config(text="处理音频段落...")
            
            # 根据模式处理音频段落
            if self.duration_mode_var.get() == "fixed":
                processed_freqs, processed_durations = self.merge_short_segments(frequencies, durations)
                self.log(f"固定模式：段落合并完成，最终 {len(processed_freqs)} 个音调段")
            else:
                processed_freqs, processed_durations = self.process_dynamic_segments(frequencies, durations)
                self.log(f"动态模式：段落处理完成，最终 {len(processed_freqs)} 个音调段")
            
            self.animate_progress(60)
            
            # 显示可视化
            if self.show_visualization_var.get():
                self.progress_label.config(text="生成可视化...")
                self.visualize_audio(processed_freqs, processed_durations)
                self.animate_progress(80)
            
            self.progress_label.config(text="生成Python代码...")
            
            # 生成代码
            output_file = self.generate_improved_code(processed_freqs, processed_durations)
            
            self.animate_progress(100)
            self.progress_label.config(text="转换完成！")
            self.log(f"转换完成！生成文件: {output_file}")
            
        except Exception as e:
            self.log(f"转换失败: {str(e)}")
            messagebox.showerror("转换失败", str(e))
    
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
                current_duration += duration
                # 使用加权平均计算新频率
                current_freq = int(freq_sum / total_duration)
            else:
                # 保存当前段落
                processed_freqs.append(current_freq)
                processed_durations.append(max(current_duration, min_duration))
                
                # 开始新段落
                current_freq = freq
                current_duration = duration
                freq_sum = freq * duration
                total_duration = duration
        
        # 处理最后一个段落
        if total_duration > 0:
            processed_freqs.append(current_freq)
            processed_durations.append(max(current_duration, min_duration))
        
        return processed_freqs, processed_durations
    
    def visualize_audio(self, frequencies, durations):
        """显示音频可视化"""
        # 清除之前的可视化
        for widget in self.viz_frame.winfo_children():
            widget.destroy()
        
        # 创建matplotlib图形
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        
        # 频率图
        time_points = np.cumsum([0] + durations[:-1])
        ax1.plot(time_points, frequencies, 'b-o', markersize=3)
        ax1.set_xlabel('时间 (秒)')
        ax1.set_ylabel('频率 (Hz)')
        ax1.set_title('音频频率变化')
        ax1.grid(True, alpha=0.3)
        
        # 持续时间图
        ax2.bar(range(len(durations)), durations, alpha=0.7, color='green')
        ax2.set_xlabel('音符序号')
        ax2.set_ylabel('持续时间 (秒)')
        ax2.set_title('音符持续时间分布')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 将图形嵌入到tkinter中
        canvas = FigureCanvasTkAgg(fig, self.viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def generate_improved_code(self, frequencies, durations):
        """生成改进的Python代码"""
        base_name = os.path.splitext(os.path.basename(self.mp3_file))[0]
        output_file = f"main.py"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("import winsound\n")
            f.write("from time import sleep\n\n")
            
            f.write("def main():\n")
            f.write(f"    print('正在播放: {base_name}')\n")
            
            for i, (freq, duration) in enumerate(zip(frequencies, durations)):
                duration_ms = int(duration * 1000)
                f.write(f"    winsound.Beep({freq}, {duration_ms})  # 频率: {freq}Hz, 时长: {duration:.2f}s\n")
                
                if (i + 1) % 10 == 0:
                    f.write("    # " + "-" * 50 + "\n")
            
            f.write("    print('播放完成')\n\n")
            
            if len(frequencies) > 50:
                chunk_size = 50
                for chunk_idx in range(0, len(frequencies), chunk_size):
                    func_name = f"main_{chunk_idx // chunk_size + 1}" if chunk_idx > 0 else "main_part1"
                    f.write(f"def {func_name}():\n")
                    
                    chunk_freqs = frequencies[chunk_idx:chunk_idx + chunk_size]
                    chunk_durations = durations[chunk_idx:chunk_idx + chunk_size]
                    
                    for freq, duration in zip(chunk_freqs, chunk_durations):
                        duration_ms = int(duration * 1000)
                        f.write(f"    winsound.Beep({freq}, {duration_ms})\n")
                    
                    f.write("\n")
            
            f.write("if __name__ == '__main__':\n")
            f.write("    main()\n")
        
        self.output_file = output_file
        return output_file
    
    def run_generated_code(self):
        """运行生成的代码"""
        if not self.output_file or not os.path.exists(self.output_file):
            messagebox.showerror("错误", "请先转换MP3文件")
            return
        
        try:
            import subprocess
            subprocess.Popen(["python", self.output_file], shell=True)
            self.log("开始运行生成的代码...")
        except Exception as e:
            messagebox.showerror("运行失败", f"无法运行生成的代码: {str(e)}")

def main():
    app = ImprovedMP3ToWinsoundApp()
    app.mainloop()

if __name__ == "__main__":
    main()