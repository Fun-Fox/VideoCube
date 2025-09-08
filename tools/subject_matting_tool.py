import os
import logging
import torch
from tools.subject_matting import SubjectImageMatting, BatchImageMatting, SubjectVideoMatting

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SubjectMattingTool:
    """
    主体抠图工具主类 - 提供统一的接口来处理图片和视频主体抠图
    
    该类封装了图片和视频主体抠图功能，提供简单易用的接口。
    """

    def __init__(self,
                 model_name: str = None,
                 device: str = None,
                 batch_size: int = 1):
        """
        初始化主体抠图工具
        
        Args:
            model_name: 模型名称
            device: 运行设备 ('cuda' 或 'cpu')
            batch_size: 视频处理批大小
        """
        # 自动选择设备
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = model_name
        self.batch_size = batch_size
        self.logger = logger


    def matting_image(self,
                      input_path: str,
                      output_path: str,
                      background_color: str = 'transparency') -> tuple:
        """
        图片主体抠图接口
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            background_color: 背景颜色
            
        Returns:
            tuple: (输出图片路径, 掩码路径)
        """
        self.logger.info(f"开始处理图片: {input_path}")
        image_matting = SubjectImageMatting(self.device, self.model_name)
        image_matting.load_model()
        result = image_matting.process(input_path, output_path, background_color)
        self.logger.info(f"图片处理完成: {output_path}")
        return result

    def batch_matting_images(self,
                             input_folder: str,
                             output_folder: str,
                             background_color: str = 'transparency') -> dict:
        """
        批量处理图片
        
        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            background_color: 背景颜色
            
        Returns:
            dict: 处理结果统计信息
        """
        self.logger.info(f"开始批量处理图片: {input_folder}")
        batch_matting = BatchImageMatting(self.device, self.model_name)
        batch_matting.load_model()
        result = batch_matting.process(input_folder, output_folder, background_color)
        self.logger.info(f"批量图片处理完成: {output_folder}")
        return result

    def matting_video(self,
                      video_path: str,
                      output_folder: str,
                      background_color: str = 'transparency') -> str:
        """
        视频主体抠图接口
        
        Args:
            video_path: 输入视频路径
            output_folder: 输出文件夹路径
            background_color: 背景颜色
            
        Returns:
            输出视频路径
        """
        self.logger.info(f"开始处理视频: {video_path}")
        video_matting = SubjectVideoMatting(self.device, self.model_name, self.batch_size)
        video_matting.load_model()
        output_path = video_matting.process(video_path, output_folder, background_color)
        self.logger.info(f"视频处理完成: {output_path}")
        return output_path

    def batch_process_videos(self,
                             input_folder: str,
                             output_folder: str,
                             background_color: str = 'transparency') -> None:
        """
        批量处理视频
        
        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
            background_color: 背景颜色
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
                    self.matting_video(video_path, out_dir, background_color)
                    self.logger.info(f"视频处理完成: {filename}")
                except Exception as e:
                    self.logger.error(f"视频处理失败 {filename}: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 创建主体抠图工具实例
    image_matting = SubjectImageMatting("cuda" if torch.cuda.is_available() else "cpu")
    image_matting.load_model()

    # 示例：处理单张图片
    # tool.matting_image("input.jpg", "output.png", "transparency")

    # 示例：批量处理图片
    # tool.batch_matting_images("input_images/", "output_images/", "white")

    # 示例：处理视频
    # tool.matting_video("input.mp4", "output_frames/", "transparency")

    # 示例：批量处理视频
    # tool.batch_process_videos("input_videos/", "output_videos/", "white")

    print("Subject Matting Tool 已准备就绪")
