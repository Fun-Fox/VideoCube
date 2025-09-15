import os
import warnings
import tempfile
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCAL_MODEL_PATH = os.path.join(root_dir, 'models', "faster-whisper-large-v3")

class WhisperModelSingleton:
    _instance = None
    _model = None

    def __new__(cls, model_size="large-v3", device="cuda"):
        if cls._instance is None:
            cls._instance = super(WhisperModelSingleton, cls).__new__(cls)

            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            # 如果本地存在模型，则从本地加载
            if os.path.exists(LOCAL_MODEL_PATH):
                print(f"📦 正在从本地加载模型: {LOCAL_MODEL_PATH}")
                cls._model = WhisperModel(
                    model_size_or_path=LOCAL_MODEL_PATH,
                    device=device,
                )
            else:
                print(f"🌐 未找到本地模型，正在从远程下载: {model_size}")
                cls._model = WhisperModel(
                    model_size_or_path=model_size,
                    device=device,
                )
        return cls._instance

    def transcribe(self, audio_path, **kwargs):
        """
        调用 whisper 模型进行语音识别
        :param audio_path: 音频文件路径
        :param kwargs: 其他 transcribe 参数
        :return: segments, info
        """
        segments, info = self._model.transcribe(audio_path, **kwargs)
        segments = list(segments)
        return segments, info

    def transcribe_video(self, video_path, **kwargs):
        """
        从视频文件中提取音频并进行转录
        :param video_path: 视频文件路径
        :param kwargs: 其他 transcribe 参数
        :return: segments, info
        """
        # 创建临时文件用于存储提取的音频
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
            tmp_audio_path = tmp_audio.name

        try:
            # 从视频中提取音频
            self._extract_audio_from_video(video_path, tmp_audio_path)
            
            # 转录音频
            segments, info = self.transcribe(tmp_audio_path, **kwargs)
            
            return segments, info
        finally:
            # 清理临时文件
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)

    def _extract_audio_from_video(self, video_path, output_path):
        """
        从视频文件中提取音频
        :param video_path: 视频文件路径
        :param output_path: 输出音频文件路径
        """
        print(f"正在从视频提取音频: {video_path}")
        
        # 使用ffmpeg提取音频
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 禁用视频
            '-ac', '1',  # 单声道
            '-ar', '16000',  # 采样率
            '-acodec', 'pcm_s16le',  # 音频编解码器
            '-f', 'wav',  # 输出格式
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"音频提取完成: {output_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频提取失败: {e.stderr.decode()}")

    def generate_srt(self, segments, output_path):
        """
        将转录结果生成SRT字幕文件
        :param segments: 转录的片段列表
        :param output_path: SRT文件输出路径
        """
        with open(output_path, 'w', encoding='utf-8') as srt_file:
            for i, segment in enumerate(segments, 1):
                # 格式化开始时间
                start_time = self._format_time(segment.start)
                # 格式化结束时间
                end_time = self._format_time(segment.end)
                
                # 写入SRT格式内容
                srt_file.write(f"{i}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{segment.text.strip()}\n\n")
                
        print(f"SRT字幕文件已生成: {output_path}")

    def _format_time(self, seconds):
        """
        将秒数转换为SRT时间格式 (HH:MM:SS,mmm)
        :param seconds: 秒数
        :return: 格式化的时间字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def transcribe_to_srt(self, file_path, output_path, file_type='auto', **kwargs):
        """
        转录音频/视频文件并生成SRT字幕文件
        :param file_path: 音频/视频文件路径
        :param output_path: SRT文件输出路径
        :param file_type: 文件类型 ('audio', 'video' 或 'auto')
        :param kwargs: 其他 transcribe 参数
        """
        # 支持的音频格式
        audio_extensions = ['.wav', '.mp3', '.flac', '.aac', '.m4a']
        # 支持的视频格式
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        
        if file_type == 'auto':
            file_ext = Path(file_path).suffix.lower()
            if file_ext in audio_extensions:
                file_type = 'audio'
            elif file_ext in video_extensions:
                file_type = 'video'
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 转录文件
        if file_type == 'audio':
            segments, info = self.transcribe(file_path, **kwargs)
        elif file_type == 'video':
            segments, info = self.transcribe_video(file_path, **kwargs)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        # 生成SRT文件
        self.generate_srt(segments, output_path)
        return segments, info


if __name__ == "__main__":
    model = WhisperModelSingleton()
    # segments, info = model.transcribe_video("test.mp4")
    # print(segments)
    # print(info)
    
    # 示例：转录视频并生成SRT字幕文件
    file_path= r"D:\PycharmProjects\VideoCube\test\assets\xhs_live.mp4"
    segments, info = model.transcribe_to_srt(file_path, "output.srt")
    print(f"转录完成，生成SRT文件: output.srt")
    print(f"检测到语言: {info.language}")
    print(f"语言概率: {info.language_probability}")