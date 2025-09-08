import os
import torch
import logging
from abc import ABC, abstractmethod

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MattingBase(ABC):
    """
    抠像工具基类 - 所有抠像类的基类
    定义了模型加载等通用功能
    """

    def __init__(self, device: str = None, model_path: str = None):
        """
        初始化抠像基类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_path: 模型文件路径
        """
        # 自动选择设备，优先使用CUDA（如果可用）
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.model_path = model_path
        self.logger = logger

    def load_model(self, model_path: str = None) -> None:
        """
        加载抠像模型
        
        Args:
            model_path: 模型文件路径，如果为None则使用初始化时提供的路径
            
        Raises:
            FileNotFoundError: 当模型文件不存在时
            RuntimeError: 当模型加载失败时
        """
        model_path = model_path or self.model_path
        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        self.logger.info(f"正在加载模型: {model_path}")
        try:
            # 使用torch.jit.load加载模型，并设置到指定设备
            self.model = torch.jit.load(model_path, map_location=self.device).eval()
            self.logger.info("模型加载完成")
        except Exception as e:
            self.logger.error(f"模型加载失败: {str(e)}")
            raise RuntimeError(f"模型加载失败: {str(e)}")

    @abstractmethod
    def process(self, *args, **kwargs):
        """
        抽象处理方法，由子类实现具体处理逻辑
        """
        pass


