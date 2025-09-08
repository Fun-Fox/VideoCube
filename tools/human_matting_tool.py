import os
import logging
import torch
from tools.human_matting import ImageMatting, VideoMatting

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HumanMattingTool:
    """
    抠像工具主类 - 提供统一的接口来处理图片和视频抠像
    
    该类封装了图片和视频抠像功能，提供简单易用的接口。
    """

    def __init__(self,
                 model_path: str = None,
                 device: str = None,
                 batch_size: int = 4,
                 fp16: bool = False):
        """
        初始化抠像工具
        
        Args:
            model_path: 模型文件路径
            device: 运行设备 ('cuda' 或 'cpu')
            batch_size: 视频处理批大小
            fp16: 是否使用半精度浮点数运算
        """
        # 自动选择设备
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path or self._get_default_model_path()
        self.batch_size = batch_size
        self.fp16 = fp16
        self.logger = logger

    def _get_default_model_path(self) -> str:
        """
        获取默认模型路径
        
        Returns:
            默认模型文件路径
        """
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(root_dir, 'models', 'mobilenetv3', 'rvm_resnet50_fp32.torchscript')
        return model_path

    def matting_image(self,
                      input_path: str,
                      output_path: str,
                      bg_color: str = 'white',
                      transparent: bool = False) -> None:
        """
        图片抠像接口
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            bg_color: 背景颜色
            transparent: 是否输出透明背景
        """
        self.logger.info(f"开始处理图片: {input_path}")
        image_matting = ImageMatting(self.device, self.model_path, self.fp16)
        image_matting.load_model()
        image_matting.process(input_path, output_path, bg_color, transparent)
        self.logger.info(f"图片处理完成: {output_path}")

    def matting_video(self,
                      video_path: str,
                      output_folder: str,
                      bg_color: str = 'white',
                      transparent: bool = False) -> str:
        """
        视频抠像接口
        
        Args:
            video_path: 输入视频路径
            output_folder: 输出文件夹路径
            bg_color: 背景颜色
            transparent: 是否输出透明背景
            
        Returns:
            输出视频路径
        """
        self.logger.info(f"开始处理视频: {video_path}")
        video_matting = VideoMatting(self.device, self.model_path, self.batch_size, self.fp16)
        video_matting.load_model()
        output_path = video_matting.process(video_path, output_folder, bg_color, transparent)
        self.logger.info(f"视频处理完成: {output_path}")
        return output_path

    def batch_process_videos(self,
                             input_folder: str,
                             output_folder: str,
                             bg_color: str = 'white',
                             transparent: bool = False) -> None:
        """
        批量处理视频
        
        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            bg_color: 背景颜色
            transparent: 是否输出透明背景
        """
        self.logger.info(f"开始批量处理视频: {input_folder}")
        supported_exts = ['.mp4', '.avi', '.mov', '.mkv']

        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)

        for filename in os.listdir(input_folder):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in supported_exts:
                video_path = os.path.join(input_folder, filename)
                file_name = os.path.splitext(filename)[0]
                out_dir = os.path.join(output_folder, file_name)

                self.logger.info(f"开始处理视频: {filename}")
                try:
                    self.matting_video(video_path, out_dir, bg_color, transparent)
                    self.logger.info(f"视频处理完成: {filename}")
                except Exception as e:
                    self.logger.error(f"视频处理失败 {filename}: {str(e)}")