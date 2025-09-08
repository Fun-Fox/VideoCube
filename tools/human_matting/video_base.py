import os
import torch
import numpy as np
import cv2
import logging
from einops import rearrange, repeat
from PIL import ImageColor
from tqdm import tqdm
import subprocess
from typing import Dict
from .matting_base import MattingBase


class VideoMattingBase(MattingBase):
    """
    视频抠像基类 - 提供视频处理的通用功能
    包括视频信息提取、音视频处理等基础功能
    """

    def __init__(self, device: str = None, model_path: str = None, batch_size: int = 4, fp16: bool = False):
        """
        初始化视频抠像基类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_path: 模型文件路径
            batch_size: 批处理大小，影响内存使用和处理速度
            fp16: 是否使用半精度浮点数 (float16) 运算
        """
        super().__init__(device, model_path)
        self.batch_size = batch_size
        self.fp16 = fp16
        self.logger = logging.getLogger(__name__)

    def _extract_video_info(self, video_path: str) -> Dict:
        """
        提取视频基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            包含视频信息的字典，包括总帧数、帧率、宽度和高度
        """
        self.logger.info(f"正在提取视频信息: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': int(cap.get(cv2.CAP_PROP_FPS)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
        cap.release()
        
        self.logger.info(f"视频信息提取完成: {info}")
        return info

    def _extract_audio(self, video_path: str, audio_path: str) -> bool:
        """
        提取视频音频轨道
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频输出路径
            
        Returns:
            是否成功提取音频
        """
        self.logger.info("正在提取音频轨道")
        try:
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn", "-acodec", "aac",
                "-y", audio_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            success = os.path.exists(audio_path)
            if success:
                self.logger.info(f"音频提取完成: {audio_path}")
            else:
                self.logger.warning("音频提取失败: 输出文件不存在")
            return success
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"音频提取失败: ffmpeg执行错误: {str(e)}")
            return False
        except Exception as e:
            self.logger.warning(f"音频提取失败: {str(e)}")
            return False

    def _images_to_video(self,
                         image_pattern: str,
                         output_path: str,
                         fps: int,
                         transparent: bool = False) -> None:
        """
        将图片序列转换为视频
        
        Args:
            image_pattern: 图片序列路径模式
            output_path: 输出视频路径
            fps: 视频帧率
            transparent: 是否支持透明通道
        """
        self.logger.info(f"正在合成视频: {output_path}")
        
        # 根据是否需要透明通道选择编解码器和像素格式
        codec = "qtrle" if transparent else "libx264"
        pix_fmt = "yuva420p" if transparent else "yuv420p"

        cmd = [
            "ffmpeg",
            "-framerate", str(fps),
            "-i", image_pattern,
            "-vcodec", codec,
            "-pix_fmt", pix_fmt,
            "-y", output_path
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            self.logger.info(f"视频合成完成: {output_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"视频合成失败: ffmpeg执行错误: {str(e)}")
            raise RuntimeError(f"视频合成失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"视频合成失败: {str(e)}")
            raise

    def _merge_audio_video(self, video_path: str, audio_path: str, output_path: str) -> None:
        """
        合并音频和视频
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 最终输出路径
        """
        self.logger.info(f"正在合并音视频: {output_path}")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            "-shortest",
            "-y", output_path
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            self.logger.info(f"音视频合并完成: {output_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"音视频合并失败: ffmpeg执行错误: {str(e)}")
            raise RuntimeError(f"音视频合并失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"音视频合并失败: {str(e)}")
            raise