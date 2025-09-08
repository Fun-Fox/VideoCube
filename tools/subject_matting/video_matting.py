import torch
import os
import cv2
from tqdm import tqdm
from PIL import Image
from .matting_base import SubjectMattingBase
from .image_utils import ImageProcessor, tensor2pil
from .video_utils import VideoProcessor


class SubjectVideoMatting(SubjectMattingBase):
    """
    主体视频抠图类 - 用于处理视频的背景移除
    """

    def __init__(self, device: str = None, model_name: str = "ZhengPeng7/BiRefNet", batch_size: int = 1):
        """
        初始化主体视频抠图类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_name: 模型名称
            batch_size: 批处理大小
        """
        super().__init__(device, model_name)
        self.batch_size = batch_size

    def process(self,
                video_path: str,
                output_folder: str,
                background_color_name: str = "transparency") -> str:
        """
        对视频进行主体抠图处理
        
        Args:
            video_path: 输入视频路径
            output_folder: 输出文件夹路径
            background_color_name: 背景颜色名称
            
        Returns:
            输出视频路径
            
        Raises:
            RuntimeError: 当模型未加载时
            ValueError: 当无法读取输入视频时
        """
        if not self.model:
            raise RuntimeError("请先加载模型")

        if not os.path.exists(video_path):
            raise ValueError(f"视频文件不存在: {video_path}")

        # 获取视频信息
        video_info = VideoProcessor.extract_video_info(video_path)
        self.logger.info(f"视频信息: {video_info}")

        # 创建输出目录
        os.makedirs(output_folder, exist_ok=True)

        # 处理视频帧
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
            
        total_frames = video_info['total_frames']
        fps = video_info['fps']

        # 初始化进度条
        pbar = tqdm(total=total_frames, desc=f"处理 {os.path.basename(video_path)}")
        frame_idx = 0

        # 逐帧处理视频
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            try:
                # 将OpenCV图像(BGR)转换为PIL图像(RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                orig_image = Image.fromarray(frame_rgb)
                
                # 创建一个假的tensor用于处理（模拟ComfyUI的输入）
                dummy_tensor = torch.randn(1, 3, orig_image.height, orig_image.width)
                processed_image_tensor, mask_tensor = ImageProcessor.process_single_image(
                    self.model, self.device, dummy_tensor, orig_image, background_color_name
                )
                
                # 保存处理后的图像
                processed_image = tensor2pil(processed_image_tensor.squeeze())
                mask_image = tensor2pil(mask_tensor.squeeze())
                
                processed_image.save(
                    os.path.join(output_folder, f"frame_{frame_idx:05d}.png")
                )
                mask_image.save(
                    os.path.join(output_folder, f"mask_{frame_idx:05d}.png")
                )
                
                frame_idx += 1
                pbar.update(1)

            except Exception as e:
                self.logger.error(f"处理帧 {frame_idx} 时出错: {str(e)}")
                frame_idx += 1
                pbar.update(1)
                continue

        cap.release()
        pbar.close()

        # 合成视频
        file_name = os.path.splitext(os.path.basename(video_path))[0]
        image_pattern = os.path.join(output_folder, "frame_%05d.png")
        temp_video_path = os.path.join(os.path.dirname(output_folder), f"{file_name}_matting.mp4")

        # 图片转视频
        VideoProcessor.images_to_video(image_pattern, temp_video_path, fps, background_color_name == "transparency")

        # 提取并合并音频
        audio_path = os.path.join(output_folder, "extracted_audio.aac")
        if VideoProcessor.extract_audio(video_path, audio_path):
            final_video_path = temp_video_path.replace(".mp4", "_with_audio.mp4")
            VideoProcessor.merge_audio_video(temp_video_path, audio_path, final_video_path)
            # 清理临时文件
            os.remove(temp_video_path)
            os.remove(audio_path)
            return final_video_path
        else:
            # 清理音频文件（如果存在）
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return temp_video_path