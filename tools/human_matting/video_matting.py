import torch
import numpy as np
import cv2
import os
from einops import rearrange, repeat
from PIL import ImageColor
from tqdm import tqdm
from .video_base import VideoMattingBase


class VideoMatting(VideoMattingBase):
    """
    视频抠像类 - 用于处理视频背景移除
    支持透明背景输出和自定义背景颜色
    """

    def process(self,
                video_path: str,
                output_folder: str,
                bg_color: str = 'white',
                transparent: bool = False) -> str:
        """
        对视频进行抠像处理
        
        关于图像大小调整的说明：
        在当前实现中，视频帧被调整为1080x1920尺寸是为了优化处理速度和内存使用。
        这种固定尺寸的方法可以确保在不同视频上的一致性能，但会改变原始视频的宽高比。
        如果需要保持原始视频比例，可以修改帧处理逻辑以适应原始尺寸。

        Args:
            video_path: 输入视频路径
            output_folder: 输出文件夹路径
            bg_color: 背景颜色 (默认: 'white')
            transparent: 是否输出透明背景 (默认: False)

        Returns:
            输出视频路径
        """
        if not self.model:
            raise RuntimeError("请先加载模型")

        # 获取视频信息
        video_info = self._extract_video_info(video_path)
        self.logger.info(f"视频信息: {video_info}")

        # 创建输出目录
        os.makedirs(output_folder, exist_ok=True)

        # 处理视频帧
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
            
        total_frames = video_info['total_frames']
        fps = video_info['fps']
        height, width = video_info['height'], video_info['width']

        # 初始化进度条和递归状态
        pbar = tqdm(total=total_frames, desc=f"处理 {os.path.basename(video_path)}")
        rec = [None] * 4  # RVM模型的递归状态
        frame_idx = 0

        # 逐批处理视频帧
        while True:
            frames = []
            # 按批次读取帧以提高处理效率
            for _ in range(self.batch_size):
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 调整帧大小以适应模型输入要求
                # 注意：这里会改变视频帧的宽高比，如果需要保持比例，可以使用cv2.resize的其他参数
                frame = cv2.resize(frame, (1080, 1920))
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)

            if not frames:
                break

            # 转换为tensor并调整维度顺序 (N, H, W, C) -> (N, C, H, W)
            video_frames = torch.from_numpy(np.stack(frames)).float()
            video_frames = rearrange(video_frames, "n h w c -> n c h w").to(self.device)
            
            # 根据设置决定是否使用半精度
            if self.fp16:
                video_frames = video_frames.half()
                # 确保模型也转换为半精度
                self.model = self.model.half()

            # 执行抠像处理
            with torch.no_grad():
                try:
                    # 计算下采样比率以优化处理速度
                    downsample_ratio = min(512 / max(height, width), 1)
                    
                    # 使用RVM模型处理帧批次
                    fgrs, phas, *rec = self.model(video_frames, *rec, downsample_ratio)
                    masks = phas.gt(0).float()  # 创建前景掩码

                    if transparent:
                        # 透明背景处理 - 前景与透明背景合成
                        fgrs = fgrs * masks + (1.0 - masks) * 1.0
                    else:
                        # 固定颜色背景处理 - 前景与指定颜色背景合成
                        bg = torch.Tensor(ImageColor.getrgb(bg_color)[:3]).float() / 255.
                        bg = repeat(bg, "c -> n c h w", n=fgrs.shape[0], h=1, w=1).to(self.device)
                        if self.fp16:
                            bg = bg.half()
                        fgrs = fgrs * masks + bg * (1.0 - masks)

                    # 保存结果
                    # 转换回图片格式 (N, C, H, W) -> (N, H, W, C)
                    fgrs = rearrange(fgrs.float().cpu(), "n c h w -> n h w c").numpy()

                    for i, fgr in enumerate(fgrs):
                        fgr = (fgr * 255).astype(np.uint8)
                        if transparent:
                            # 处理透明通道并保存为RGBA格式
                            mask = (masks[i].cpu().numpy() * 255).astype(np.uint8)
                            if mask.ndim == 3:
                                mask = mask.squeeze(0)[..., None]
                            elif mask.ndim == 4:
                                mask = mask.squeeze(0)[..., 0, None]
                            rgba = np.concatenate([fgr, mask], axis=-1)
                            cv2.imwrite(
                                os.path.join(output_folder, f"frame_{frame_idx:05d}_rgba.png"),
                                cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
                            )
                        else:
                            # 保存为RGB格式
                            cv2.imwrite(
                                os.path.join(output_folder, f"frame_{frame_idx:05d}_fgr.png"),
                                cv2.cvtColor(fgr, cv2.COLOR_RGB2BGR)
                            )
                        frame_idx += 1
                        pbar.update(1)

                except Exception as e:
                    self.logger.error(f"处理帧时出错: {str(e)}")
                    continue

        cap.release()
        pbar.close()

        # 合成视频
        file_name = os.path.splitext(os.path.basename(video_path))[0]
        if transparent:
            image_pattern = os.path.join(output_folder, "frame_%05d_rgba.png")
            temp_video_path = os.path.join(os.path.dirname(output_folder), f"{file_name}_rgba.mov")
        else:
            image_pattern = os.path.join(output_folder, "frame_%05d_fgr.png")
            temp_video_path = os.path.join(os.path.dirname(output_folder), f"{file_name}_fgr.mp4")

        # 图片转视频
        self._images_to_video(image_pattern, temp_video_path, fps, transparent)

        # 提取并合并音频
        audio_path = os.path.join(output_folder, "extracted_audio.aac")
        if self._extract_audio(video_path, audio_path):
            if transparent:
                final_video_path = temp_video_path.replace(".mov", "_with_audio.mov")
            else:
                final_video_path = temp_video_path.replace(".mp4", "_with_audio.mp4")
            self._merge_audio_video(temp_video_path, audio_path, final_video_path)
            # 清理临时文件
            os.remove(temp_video_path)
            os.remove(audio_path)
            return final_video_path
        else:
            # 清理音频文件（如果存在）
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return temp_video_path