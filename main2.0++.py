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
import soundfile as sf  # 添加这一行导入soundfile
matplotlib.use("TkAgg")

class MP3ToWinsoundApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MP3到Winsound.Beep转换器(此版本mp3格式文件名必须用英文，不然报错！)")
        self.geometry("800x600")
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
        
        # 转换模式选择
        self.mode_var = tk.StringVar(value="1")
        ttk.Radiobutton(options_frame, text="单线程转换 (适合简单的单音轨音乐)", variable=self.mode_var, value="1").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(options_frame, text="多线程转换 (适合复杂的多音轨音乐)", variable=self.mode_var, value="2").pack(anchor=tk.W, padx=5, pady=2)
        
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
        
        # 初始日志
        self.log("欢迎使用MP3到Winsound.Beep转换器！")
        self.log("请选择一个MP3文件并设置转换选项。")
    
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
    
    def mp3_to_winsound(self, mp3_file, output_file=None, function_name=None):
        """将MP3文件转换为使用winsound.beep播放的Python代码"""
        # 如果未指定函数名，则从文件名生成
        if function_name is None:
            base_name = os.path.splitext(os.path.basename(mp3_file))[0]
            function_name = self.chinese_to_pinyin(base_name).replace(' ', '_').replace('-', '_')
        
        # 如果未指定输出文件，则使用与输入文件相同的名称但扩展名为.py
        if output_file is None:
            output_file = os.path.splitext(mp3_file)[0] + "_winsound.py"
        
        # 加载音频文件
        self.log(f"正在加载音频文件: {mp3_file}")
        self.progress_var.set(10)
        y, sr = librosa.load(mp3_file, sr=None)
        self.log(f"音频加载完成，采样率: {sr}Hz, 持续时间: {len(y)/sr:.2f}秒")
        
        # 可视化音频波形
        self.visualize_audio(y, sr)
        
        # 提取音高和持续时间
        self.log("正在分析音频频率和音高...")
        self.progress_var.set(20)
        # 使用librosa的音高检测
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        self.log(f"频率分析完成，检测到 {pitches.shape[1]} 个时间帧")
        
        # 定义音符频率映射（C4到B5）
        note_freqs = {
            'C4': 261,  # Do
            'C#4': 277,
            'D4': 293,  # Re
            'D#4': 311,
            'E4': 329,  # Mi
            'F4': 349,  # Fa
            'F#4': 370,
            'G4': 392,  # So
            'G#4': 415,
            'A4': 440,  # La
            'A#4': 466,
            'B4': 493,  # Ti
            'C5': 523,  # Do (高八度)
            'C#5': 554,
            'D5': 587,  # Re (高八度)
            'D#5': 622,
            'E5': 659,  # Mi (高八度)
            'F5': 698,  # Fa (高八度)
            'F#5': 740,
            'G5': 783,  # So (高八度)
            'G#5': 831,
            'A5': 880,  # La (高八度)
            'A#5': 932,
            'B5': 987,  # Ti (高八度)
        }
        
        self.log("音符频率映射表已创建")
        
        # 反向映射，用于查找最接近的音符
        freq_to_note = {freq: note for note, freq in note_freqs.items()}
        
        # 分析每个时间帧的主要频率
        self.log("正在提取主要音符序列...")
        self.progress_var.set(30)
        hop_length = 512
        time_frames = librosa.frames_to_time(range(pitches.shape[1]), sr=sr, hop_length=hop_length)
        
        # 提取主要音符序列
        notes = []
        durations = []
        current_note = None
        start_time = 0
        
        # 设置幅度阈值，忽略低于此值的音符
        magnitude_threshold = np.max(magnitudes) * 0.1
        self.log(f"设置幅度阈值: {magnitude_threshold:.2f}")
        
        total_frames = len(time_frames)
        self.log(f"开始处理 {total_frames} 个时间帧...")
        
        for t, time_frame in enumerate(time_frames):
            # 更新进度条
            if t % 100 == 0:
                progress = 30 + (t / total_frames) * 40
                self.progress_var.set(progress)
                if t % 1000 == 0:
                    self.log(f"已处理 {t}/{total_frames} 帧 ({t/total_frames*100:.1f}%)")
            
            # 获取当前时间帧的最大幅度频率
            max_magnitude_idx = np.argmax(magnitudes[:, t])
            max_magnitude = magnitudes[max_magnitude_idx, t]
            
            # 如果幅度太低，认为是静音
            if max_magnitude < magnitude_threshold:
                if current_note is not None:
                    # 结束当前音符
                    duration = time_frame - start_time
                    if duration > 0.05:  # 忽略太短的音符
                        notes.append(current_note)
                        durations.append(duration)
                    current_note = None
                continue
            
            # 获取频率并找到最接近的音符
            freq = pitches[max_magnitude_idx, t]
            if freq == 0:
                continue
            
            # 找到最接近的标准音符频率
            closest_freq = min(note_freqs.values(), key=lambda x: abs(x - freq))
            note = [n for n, freq_val in note_freqs.items() if freq_val == closest_freq][0]
            
            if current_note != note:
                # 如果有前一个音符，记录它的持续时间
                if current_note is not None:
                    duration = time_frame - start_time
                    if duration > 0.05:  # 忽略太短的音符
                        notes.append(current_note)
                        durations.append(duration)
                
                # 开始新音符
                current_note = note
                start_time = time_frame
        
        # 处理最后一个音符
        if current_note is not None:
            duration = time_frames[-1] - start_time
            if duration > 0.05:
                notes.append(current_note)
                durations.append(duration)
        
        self.log(f"音符提取完成，共提取出 {len(notes)} 个音符")
        
        # 可视化提取的音符
        self.visualize_notes(notes, durations, note_freqs)
        
        # 生成Python代码
        self.log(f"正在生成Python代码到: {output_file}")
        self.progress_var.set(80)
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入导入语句
            f.write("import winsound\n")
            f.write("from time import sleep\n\n")
            # 在mp3_to_winsound方法中，第332-338行已经有正确的逻辑
            # 写入音符频率常量
            f.write("# 音符频率定义\n")
            for i, (note, freq) in enumerate(note_freqs.items()):
                note_name = chr(65 + i % 26)  # A-Z循环
                if i >= 26:
                    note_name += str(i // 26)
                f.write(f"{note_name} = {freq}  # {note}\n")
            f.write("\n")
            
            # 写入函数定义
            f.write(f"def {function_name}():\n")
            
            # 写入音符序列
            for i, (note, duration) in enumerate(zip(notes, durations)):
                # 获取音符对应的频率
                freq = note_freqs[note]
                
                # 找到对应的变量名
                note_var = None  # 初始化变量
                for j, (n, freq_val) in enumerate(note_freqs.items()):
                    if n == note:
                        note_var = chr(65 + j % 26)
                        if j >= 26:
                            note_var += str(j // 26)
                        break
                
                # 调试输出
                print(f"Debug: note={note}, note_var={note_var}, type={type(note_var)}")
                
                # 计算持续时间（毫秒）
                duration_ms = int(duration * 1000)
                
                # 每10个音符添加一个分隔注释
                if i % 10 == 0 and i > 0:
                    f.write(f"    #-------------------------\n")
                
                # 确保note_var是有效的字符串变量名
                if note_var is None or not isinstance(note_var, str):
                    # 使用频率值代替变量名
                    f.write(f"    winsound.Beep({int(freq)},{duration_ms})  # {note}\n")
                else:
                    # 写入winsound.Beep调用，确保note_var是字符串
                    f.write(f"    winsound.Beep({str(note_var)},{duration_ms})  # {note}\n")
                
                # 如果音符之间有间隔，添加sleep
                if i < len(notes) - 1 and duration < 0.2:
                    f.write(f"    sleep({duration:.2f})\n")
            
            # 写入主程序调用
            f.write("\n")
            f.write(f"if __name__ == '__main__':\n")
            f.write(f"    print('正在播放: {os.path.basename(mp3_file)}')\n")
            f.write(f"    {function_name}()\n")
            f.write(f"    print('播放完成')\n")
        
        self.log(f"代码生成完成，共生成 {len(notes)} 个音符的播放代码")
        self.progress_var.set(100)
        return output_file
    
    def play_mp3_with_threads(self, mp3_file, num_threads=2):
        """使用多线程分析MP3文件的不同频率范围并生成多个winsound函数"""
        # 加载音频文件
        self.log(f"正在加载音频文件: {mp3_file}")
        self.progress_var.set(10)
        y, sr = librosa.load(mp3_file, sr=None)
        self.log(f"音频加载完成，采样率: {sr}Hz, 持续时间: {len(y)/sr:.2f}秒")
        
        # 可视化音频波形
        self.visualize_audio(y, sr)
        
        # 将频率范围分成多个部分
        self.log("正在分离和声和打击乐部分...")
        self.progress_var.set(20)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        self.log("音频分离完成")
        
        # 可视化分离后的音频
        self.visualize_separated_audio(y_harmonic, y_percussive, sr)
        
        # 创建输出文件
        base_name = os.path.splitext(os.path.basename(mp3_file))[0]
        output_file = f"{os.path.splitext(mp3_file)[0]}_multi_thread.py"
        
        self.log(f"正在生成多线程Python代码到: {output_file}")
        self.progress_var.set(30)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入导入语句
            f.write("import winsound\n")
            f.write("from time import sleep\n")
            f.write("import threading\n\n")
            
            # 为每个线程生成一个函数
            for i in range(num_threads):
                if i == 0:
                    # 第一个线程处理和声部分
                    audio_part = y_harmonic
                    part_name = "harmonic"
                    self.log("正在处理和声部分...")
                else:
                    # 第二个线程处理打击乐部分
                    audio_part = y_percussive
                    part_name = "percussive"
                    self.log("正在处理打击乐部分...")
                
                # 生成临时文件
                temp_file = f"{os.path.splitext(mp3_file)[0]}_{part_name}_temp.wav"
                self.log(f"正在生成临时文件: {temp_file}")
                sf.write(temp_file, audio_part, sr)
                
                # 更新进度
                progress = 30 + (i / num_threads) * 50
                self.progress_var.set(progress)
                
                # 转换这部分音频并获取生成的代码
                temp_output = f"{os.path.splitext(mp3_file)[0]}_{part_name}_temp.py"
                self.log(f"正在为{part_name}部分生成代码: {temp_output}")
                self.mp3_to_winsound(temp_file, temp_output, f"{base_name}_{part_name}")
                
                # 读取生成的代码并合并
                with open(temp_output, 'r', encoding='utf-8') as temp_f:
                    code = temp_f.read()
                    # 提取函数定义部分
                    function_start = code.find(f"def {base_name}_{part_name}()")
                    function_end = code.find("if __name__ == '__main__':")
                    if function_end == -1:
                        function_end = len(code)
                    function_code = code[function_start:function_end].strip()
                    
                    # 写入函数定义
                    f.write(function_code + "\n\n")
                
                # 删除临时文件
                try:
                    os.remove(temp_file)
                    os.remove(temp_output)
                    self.log(f"临时文件已删除: {temp_file}, {temp_output}")
                except Exception as e:
                    self.log(f"删除临时文件时出错: {str(e)}")
            
            # 写入主函数，使用线程并行播放
            f.write("def play_all():\n")
            f.write("    threads = []\n")
            for i in range(num_threads):
                if i == 0:
                    part_name = "harmonic"
                else:
                    part_name = "percussive"
                f.write(f"    t{i} = threading.Thread(target={base_name}_{part_name})\n")
                f.write(f"    threads.append(t{i})\n")
            
            f.write("\n    # 启动所有线程\n")
            f.write("    for t in threads:\n")
            f.write("        t.start()\n")
            
            f.write("\n    # 等待所有线程完成\n")
            f.write("    for t in threads:\n")
            f.write("        t.join()\n")
            
            # 写入主程序调用
            f.write("\nif __name__ == '__main__':\n")
            f.write(f"    print('正在多线程播放: {os.path.basename(mp3_file)}')\n")
            f.write(f"    play_all()\n")
            f.write(f"    print('播放完成')\n")
        
        self.log(f"多线程代码生成完成: {output_file}")
        self.progress_var.set(100)
        return output_file
    
    def visualize_audio(self, y, sr):
        """可视化音频波形"""
        try:
            self.ax.clear()
            librosa.display.waveshow(y, sr=sr, ax=self.ax)
            self.ax.set_title("音频波形")
            self.ax.set_xlabel("时间 (秒)")
            self.ax.set_ylabel("振幅")
            self.canvas.draw()
        except Exception as e:
            self.log(f"可视化音频波形时出错: {str(e)}")
    
    def visualize_separated_audio(self, y_harmonic, y_percussive, sr):
        """可视化分离后的音频"""
        try:
            self.ax.clear()
            plt.subplot(211)
            librosa.display.waveshow(y_harmonic, sr=sr, alpha=0.5, ax=self.ax)
            self.ax.set_title("和声部分")
            self.ax.set_ylabel("振幅")
            
            plt.subplot(212)
            librosa.display.waveshow(y_percussive, sr=sr, color='r', alpha=0.5)
            plt.title("打击乐部分")
            plt.xlabel("时间 (秒)")
            plt.ylabel("振幅")
            plt.tight_layout()
            
            self.canvas.draw()
        except Exception as e:
            self.log(f"可视化分离音频时出错: {str(e)}")
    
    def visualize_notes(self, notes, durations, note_freqs):
        """可视化提取的音符"""
        try:
            self.ax.clear()
            
            # 将音符转换为频率
            freqs = [note_freqs[note] for note in notes]
            
            # 计算每个音符的开始时间
            start_times = [0]
            for i in range(len(durations)-1):
                start_times.append(start_times[-1] + durations[i])
            
            # 绘制音符
            for i, (freq, duration, start_time) in enumerate(zip(freqs, durations, start_times)):
                self.ax.plot([start_time, start_time + duration], [freq, freq], 'b-', linewidth=2)
            
            self.ax.set_title(f"提取的音符序列 (共{len(notes)}个音符)")
            self.ax.set_xlabel("时间 (秒)")
            self.ax.set_ylabel("频率 (Hz)")
            self.ax.grid(True)
            
            self.canvas.draw()
        except Exception as e:
            self.log(f"可视化音符时出错: {str(e)}")

def main():
    app = MP3ToWinsoundApp()
    app.mainloop()

if __name__ == "__main__":
    main()

    def chinese_to_pinyin(self, text):
        """将中文转换为拼音，非中文字符保持不变"""
        # 简单的中文字符到拼音的映射
        chinese_pinyin_map = {
            '曾': 'zeng', '经': 'jing', '你': 'ni', '说': 'shuo',
            '赵': 'zhao', '乃': 'nai', '吉': 'ji',
            '一': 'yi', '二': 'er', '三': 'san', '四': 'si', '五': 'wu',
            '六': 'liu', '七': 'qi', '八': 'ba', '九': 'jiu', '十': 'shi',
            '爱': 'ai', '情': 'qing', '歌': 'ge', '音': 'yin', '乐': 'le',
            '春': 'chun', '夏': 'xia', '秋': 'qiu', '冬': 'dong',
            '花': 'hua', '鸟': 'niao', '鱼': 'yu', '虫': 'chong',
            '山': 'shan', '水': 'shui', '风': 'feng', '雨': 'yu',
            '天': 'tian', '地': 'di', '人': 'ren', '心': 'xin'
        }
        
        result = []
        for char in text:
            if char in chinese_pinyin_map:
                result.append(chinese_pinyin_map[char])
            elif '\u4e00' <= char <= '\u9fff':  # 其他中文字符
                # 对于映射表中没有的中文字符，使用unicode编码
                result.append(f'char_{ord(char)}')
            else:
                # 非中文字符保持不变
                result.append(char)
        
        return ''.join(result)