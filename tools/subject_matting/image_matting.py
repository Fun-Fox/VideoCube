import torch
import os
from PIL import Image
from .matting_base import SubjectMattingBase
from .image_utils import ImageProcessor, tensor2pil


# 支持的颜色列表
colors = ["transparency", "green", "white", "red", "yellow", "blue", "black", "pink", "purple", "brown", "violet",
          "wheat", "whitesmoke", "yellowgreen", "turquoise", "tomato", "thistle", "teal", "tan", "steelblue",
          "springgreen", "snow", "slategrey", "slateblue", "skyblue", "orange"]


class SubjectImageMatting(SubjectMattingBase):
    """
    主体图像抠图类 - 用于处理单张图片的背景移除
    """

    def __init__(self, device: str = None, model_name: str = "ZhengPeng7/BiRefNet"):
        """
        初始化主体图像抠图类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_name: 模型名称
        """
        super().__init__(device, model_name)

    def process(self,
                image_path: str,
                output_path: str,
                background_color_name: str = "transparency") -> tuple:
        """
        对单张图片进行主体抠图处理
        
        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径
            background_color_name: 背景颜色名称
            
        Returns:
            tuple: (处理后的图像路径, 掩码路径)
            
        Raises:
            RuntimeError: 当模型未加载时
            ValueError: 当无法读取输入图片时
        """
        if not self.model:
            raise RuntimeError("请先加载模型")

        # 读取图片
        self.logger.info(f"正在读取图片: {image_path}")
        if not os.path.exists(image_path):
            raise ValueError(f"图片文件不存在: {image_path}")

        orig_image = Image.open(image_path)
        if orig_image is None:
            raise ValueError(f"无法读取图片: {image_path}")

        self.logger.info(f"原始图片尺寸: {orig_image.size}")

        # 处理图像
        try:
            self.logger.info("开始执行主体抠图处理")
            # 创建一个假的tensor用于处理（模拟ComfyUI的输入）
            dummy_tensor = torch.randn(1, 3, orig_image.height, orig_image.width)
            processed_image_tensor, mask_tensor = ImageProcessor.process_single_image(
                self.model, self.device, dummy_tensor, orig_image, background_color_name
            )
            
            # 保存处理后的图像
            processed_image = tensor2pil(processed_image_tensor.squeeze())
            mask_image = tensor2pil(mask_tensor.squeeze())
            
            processed_image.save(output_path)
            
            # 保存掩码
            mask_path = output_path.replace(".", "_mask.")
            mask_image.save(mask_path)
            
            self.logger.info(f"主体抠图完成: {output_path}")
            self.logger.info(f"遮罩保存至: {mask_path}")
            
            return output_path, mask_path

        except Exception as e:
            self.logger.error(f"主体抠图失败: {str(e)}")
            raise


class BatchImageMatting(SubjectMattingBase):
    """
    批量图像抠图类 - 用于批量处理图片的背景移除
    """

    def __init__(self, device: str = None, model_name: str = "ZhengPeng7/BiRefNet"):
        """
        初始化批量图像抠图类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_name: 模型名称
        """
        super().__init__(device, model_name)

    def process(self,
                input_dir: str,
                output_dir: str,
                background_color_name: str = "transparency") -> dict:
        """
        批量处理图片目录中的所有图片
        
        Args:
            input_dir: 输入图片目录
            output_dir: 输出图片目录
            background_color_name: 背景颜色名称
            
        Returns:
            dict: 处理结果统计信息
            
        Raises:
            RuntimeError: 当模型未加载时
            ValueError: 当输入目录不存在时
        """
        if not self.model:
            raise RuntimeError("请先加载模型")

        if not os.path.exists(input_dir):
            raise ValueError(f"输入目录不存在: {input_dir}")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 支持的图像格式
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')
        
        # 统计信息
        processed_count = 0
        failed_files = []
        
        # 遍历输入目录中的所有图像文件
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(image_extensions):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, f"matting_{filename}")
                
                try:
                    self.logger.info(f"正在处理: {filename}")
                    orig_image = Image.open(input_path)
                    # 创建一个假的tensor用于处理（模拟ComfyUI的输入）
                    dummy_tensor = torch.randn(1, 3, orig_image.height, orig_image.width)
                    processed_image_tensor, mask_tensor = ImageProcessor.process_single_image(
                        self.model, self.device, dummy_tensor, orig_image, background_color_name
                    )
                    
                    # 保存处理后的图像
                    processed_image = tensor2pil(processed_image_tensor.squeeze())
                    mask_image = tensor2pil(mask_tensor.squeeze())
                    
                    processed_image.save(output_path)
                    
                    # 保存掩码
                    mask_path = output_path.replace(".", "_mask.")
                    mask_image.save(mask_path)
                    
                    processed_count += 1
                    self.logger.info(f"处理完成: {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"处理失败 {filename}: {str(e)}")
                    failed_files.append(filename)
                    continue

        result = {
            "processed_count": processed_count,
            "failed_count": len(failed_files),
            "failed_files": failed_files,
            "output_dir": output_dir
        }
        
        self.logger.info(f"批量处理完成: 共处理 {processed_count} 张图片, 失败 {len(failed_files)} 张")
        return result

