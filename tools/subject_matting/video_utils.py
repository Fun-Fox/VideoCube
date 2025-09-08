import os
import cv2
import logging
import subprocess
from typing import Dict

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    视频处理工具类 - 提供视频处理的通用功能
    """

    @staticmethod
    def extract_video_info(video_path: str) -> Dict:
        """
        提取视频基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            包含视频信息的字典，包括总帧数、帧率、宽度和高度
        """
        logger.info(f"正在提取视频信息: {video_path}")
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
        
        logger.info(f"视频信息提取完成: {info}")
        return info

    @staticmethod
    def extract_audio(video_path: str, audio_path: str) -> bool:
        """
        提取视频音频轨道
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频输出路径
            
        Returns:
            是否成功提取音频
        """
        logger.info("正在提取音频轨道")
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
                logger.info(f"音频提取完成: {audio_path}")
            else:
                logger.warning("音频提取失败: 输出文件不存在")
            return success
        except subprocess.CalledProcessError as e:
            logger.warning(f"音频提取失败: ffmpeg执行错误: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"音频提取失败: {str(e)}")
            return False

    @staticmethod
    def images_to_video(image_pattern: str,
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
        logger.info(f"正在合成视频: {output_path}")
        
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
            logger.info(f"视频合成完成: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"视频合成失败: ffmpeg执行错误: {str(e)}")
            raise RuntimeError(f"视频合成失败: {str(e)}")
        except Exception as e:
            logger.error(f"视频合成失败: {str(e)}")
            raise

    @staticmethod
    def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
        """
        合并音频和视频
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 最终输出路径
        """
        logger.info(f"正在合并音视频: {output_path}")
        
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
            logger.info(f"音视频合并完成: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"音视频合并失败: ffmpeg执行错误: {str(e)}")
            raise RuntimeError(f"音视频合并失败: {str(e)}")
        except Exception as e:
            logger.error(f"音视频合并失败: {str(e)}")
            raise