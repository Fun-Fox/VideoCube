import torch
import numpy as np
import cv2
from einops import rearrange, repeat
from PIL import ImageColor
from .matting_base import MattingBase


class ImageMatting(MattingBase):
    """
    图片抠像类 - 用于处理单张图片的背景移除
    支持透明背景输出和自定义背景颜色
    """

    def __init__(self, device: str = None, model_path: str = None, fp16: bool = False):
        """
        初始化图片抠像类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_path: 模型文件路径
            fp16: 是否使用半精度浮点数 (float16) 运算
        """
        super().__init__(device, model_path)
        self.fp16 = fp16

    def process(self,
                input_path: str,
                output_path: str,
                bg_color: str = 'white',
                transparent: bool = False) -> None:
        """
        对单张图片进行抠像处理
        
        关于图像大小调整的说明：
        当前实现中，图像被调整为1080x1920尺寸是为了优化处理速度和内存使用。
        这个固定的尺寸适用于大多数情况，但可能会导致图像比例变化。
        如果需要保持原始图像比例，可以修改resize逻辑以适应原始尺寸。

        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            bg_color: 背景颜色 (默认: 'white')
            transparent: 是否输出透明背景 (默认: False)
            
        Raises:
            RuntimeError: 当模型未加载时
            ValueError: 当无法读取输入图片时
        """
        if not self.model:
            raise RuntimeError("请先加载模型")

        # 读取图片
        self.logger.info(f"正在读取图片: {input_path}")
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"无法读取图片: {input_path}")

        original_h, original_w = image.shape[:2]
        self.logger.info(f"原始图片尺寸: {original_w}x{original_h}")

        # 调整图片大小以适应模型输入要求
        # 注意：这里会改变图像的宽高比，如果需要保持比例，可以使用cv2.resize的其他参数
        resized_image = cv2.resize(image, (1080, 1920))
        rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        # 转换为tensor并调整维度顺序 (H, W, C) -> (1, C, H, W)
        tensor_image = torch.from_numpy(rgb_image).float()
        tensor_image = rearrange(tensor_image, "h w c -> 1 c h w").to(self.device)

        # 根据设置决定是否使用半精度
        if self.fp16:
            tensor_image = tensor_image.half()
            self.model.half()

        # 执行抠像处理
        with torch.no_grad():
            try:
                # 计算下采样比率以优化处理速度
                downsample_ratio = min(512 / max(original_h, original_w), 1)
                rec = [None] * 4  # 递归状态初始化
                
                self.logger.info("开始执行抠像处理")
                fgr, pha, *rec = self.model(tensor_image, *rec, downsample_ratio)
                mask = pha.gt(0).float()  # 创建前景掩码

                if transparent:
                    # 透明背景处理 - 前景与透明背景合成
                    result = fgr * mask + (1.0 - mask) * 1.0
                else:
                    # 固定颜色背景处理 - 前景与指定颜色背景合成
                    bg = torch.Tensor(ImageColor.getrgb(bg_color)[:3]).float() / 255.
                    bg = repeat(bg, "c -> 1 c h w", h=1, w=1).to(self.device)
                    if self.fp16:
                        bg = bg.half()
                    result = fgr * mask + bg * (1.0 - mask)

                # 转换回图片格式 (1, C, H, W) -> (H, W, C)
                result_image = rearrange(result.float().cpu(), "1 c h w -> h w c").numpy()
                result_image = (result_image * 255).astype(np.uint8)

                if transparent:
                    # 处理透明通道并保存为RGBA格式
                    mask_array = (pha[0].cpu().numpy() * 255).astype(np.uint8)
                    if mask_array.ndim == 3:
                        mask_array = mask_array.squeeze(0)[..., None]
                    elif mask_array.ndim == 4:
                        mask_array = mask_array.squeeze(0)[..., 0, None]
                    rgba = np.concatenate([result_image, mask_array], axis=-1)
                    cv2.imwrite(output_path, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
                else:
                    # 保存为RGB格式
                    cv2.imwrite(output_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))

                self.logger.info(f"图片抠像完成: {output_path}")

            except Exception as e:
                self.logger.error(f"图片抠像失败: {str(e)}")
                raise


