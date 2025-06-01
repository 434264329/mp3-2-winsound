import librosa
import numpy as np
import os
import threading
import time

def mp3_to_winsound(mp3_file, output_file=None, function_name=None):
    """
    将MP3文件转换为使用winsound.beep播放的Python代码
    
    参数:
        mp3_file (str): MP3文件路径
        output_file (str, optional): 输出Python文件路径
        function_name (str, optional): 生成的函数名称
    """
    # 如果未指定函数名，则从文件名生成
    if function_name is None:
        function_name = os.path.splitext(os.path.basename(mp3_file))[0].replace(' ', '_')
    
    # 如果未指定输出文件，则使用与输入文件相同的名称但扩展名为.py
    if output_file is None:
        output_file = os.path.splitext(mp3_file)[0] + "_winsound.py"
    
    # 加载音频文件
    print(f"正在加载音频文件: {mp3_file}")
    y, sr = librosa.load(mp3_file, sr=None)
    
    # 提取音高和持续时间
    print("正在分析音频...")
    # 使用librosa的音高检测
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    
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
    
    # 反向映射，用于查找最接近的音符
    freq_to_note = {freq: note for note, freq in note_freqs.items()}
    
    # 分析每个时间帧的主要频率
    hop_length = 512
    time_frames = librosa.frames_to_time(range(pitches.shape[1]), sr=sr, hop_length=hop_length)
    
    # 提取主要音符序列
    notes = []
    durations = []
    current_note = None
    start_time = 0
    
    # 设置幅度阈值，忽略低于此值的音符
    magnitude_threshold = np.max(magnitudes) * 0.1
    
    for t, time_frame in enumerate(time_frames):
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
        note = [n for n, f in note_freqs.items() if f == closest_freq][0]
        
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
    
    # 生成Python代码
    print(f"正在生成Python代码到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入导入语句
        f.write("import winsound\n")
        f.write("from time import sleep\n\n")
        
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
            for j, (n, f) in enumerate(note_freqs.items()):
                if n == note:
                    note_var = chr(65 + j % 26)
                    if j >= 26:
                        note_var += str(j // 26)
                    break
            
            # 计算持续时间（毫秒）
            duration_ms = int(duration * 1000)
            
            # 每10个音符添加一个分隔注释
            if i % 10 == 0 and i > 0:
                f.write(f"    #-------------------------\n")
            
            # 写入winsound.Beep调用
            f.write(f"    winsound.Beep({note_var},{duration_ms})  # {note}\n")
            
            # 如果音符之间有间隔，添加sleep
            if i < len(notes) - 1 and duration < 0.2:
                f.write(f"    sleep({duration:.2f})\n")
        
        # 写入主程序调用
        f.write("\n")
        f.write(f"if __name__ == '__main__':\n")
        f.write(f"    print('正在播放: {os.path.basename(mp3_file)}')\n")
        f.write(f"    {function_name}()\n")
        f.write(f"    print('播放完成')\n")
    
    print(f"转换完成! 生成的Python文件: {output_file}")
    return output_file

def play_mp3_with_threads(mp3_file, num_threads=2):
    """
    使用多线程分析MP3文件的不同频率范围并生成多个winsound函数
    
    参数:
        mp3_file (str): MP3文件路径
        num_threads (int): 线程数量，对应于要分析的频率范围数量
    """
    # 加载音频文件
    y, sr = librosa.load(mp3_file, sr=None)
    
    # 将频率范围分成多个部分
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    # 创建输出文件
    base_name = os.path.splitext(os.path.basename(mp3_file))[0]
    output_file = f"{base_name}_multi_thread.py"
    
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
            else:
                # 第二个线程处理打击乐部分
                audio_part = y_percussive
                part_name = "percussive"
            
            # 为这部分音频生成临时文件
            temp_file = f"{base_name}_{part_name}_temp.wav"
            librosa.output.write_wav(temp_file, audio_part, sr)
            
            # 转换这部分音频并获取生成的代码
            temp_output = f"{base_name}_{part_name}_temp.py"
            mp3_to_winsound(temp_file, temp_output, f"{base_name}_{part_name}")
            
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
            except:
                pass
        
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
    
    print(f"多线程转换完成! 生成的Python文件: {output_file}")
    return output_file

def main():
    print("MP3到Winsound.Beep转换器")
    print("-" * 40)
    
    # 获取MP3文件路径
    mp3_file = input("请输入MP3文件路径: ")
    
    if not os.path.exists(mp3_file):
        print(f"错误: 文件 '{mp3_file}' 不存在!")
        return
    
    # 选择转换模式
    print("\n请选择转换模式:")
    print("1. 单线程转换 (适合简单的单音轨音乐)")
    print("2. 多线程转换 (适合复杂的多音轨音乐)")
    mode = input("请选择 (1/2): ")
    
    try:
        if mode == "1":
            output_file = mp3_to_winsound(mp3_file)
        else:
            output_file = play_mp3_with_threads(mp3_file)
        
        # 询问是否立即运行生成的代码
        run_code = input(f"\n是否立即运行生成的代码? (y/n): ")
        if run_code.lower() == 'y':
            print(f"\n正在运行: {output_file}")
            exec(open(output_file, encoding='utf-8').read())
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")

if __name__ == "__main__":
    main()
