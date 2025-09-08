import torch
from torchvision import transforms
import numpy as np
from PIL import Image
import torch.nn.functional as F

# 图像预处理变换
transform_image = transforms.Compose(
    [
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)


def tensor2pil(image):
    """
    将tensor转换为PIL图像
    
    Args:
        image: 输入tensor
        
    Returns:
        PIL图像
    """
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


def pil2tensor(image):
    """
    将PIL图像转换为tensor
    
    Args:
        image: 输入PIL图像
        
    Returns:
        tensor
    """
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def resize_image(image):
    """
    调整图像大小以适应模型输入
    
    Args:
        image: 输入PIL图像
        
    Returns:
        调整大小后的图像
    """
    image = image.convert('RGB')
    model_input_size = (1024, 1024)
    image = image.resize(model_input_size, Image.BILINEAR)
    return image


class ImageProcessor:
    """
    图像处理工具类 - 提供图像处理的通用功能
    """

    @staticmethod
    def process_single_image(model, device, image_tensor, orig_image, background_color_name="transparency"):
        """
        处理单张图像
        
        Args:
            model: 加载的模型
            device: 运行设备
            image_tensor: 输入图像tensor
            orig_image: 原始PIL图像
            background_color_name: 背景颜色名称
            
        Returns:
            processed_image_tensor: 处理后的图像tensor
            mask_tensor: 掩码tensor
        """
        w, h = orig_image.size
        image = resize_image(orig_image)
        im_tensor = transform_image(image).unsqueeze(0)
        im_tensor = im_tensor.to(device)
        
        with torch.no_grad():
            result = model(im_tensor)[-1].sigmoid().cpu()
        
        result = torch.squeeze(F.interpolate(result, size=(h, w)))
        ma = torch.max(result)
        mi = torch.min(result)
        result = (result - mi) / (ma - mi)
        im_array = (result * 255).cpu().data.numpy().astype(np.uint8)
        pil_im = Image.fromarray(np.squeeze(im_array))
        
        if background_color_name == 'transparency':
            color = (0, 0, 0, 0)
            mode = "RGBA"
        else:
            color = background_color_name
            mode = "RGB"
        
        new_im = Image.new(mode, pil_im.size, color)
        new_im.paste(orig_image, mask=pil_im)
        new_im_tensor = pil2tensor(new_im)
        pil_im_tensor = pil2tensor(pil_im)
        
        return new_im_tensor, pil_im_tensor