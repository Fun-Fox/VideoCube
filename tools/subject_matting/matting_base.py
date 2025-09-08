import torch
import logging
import os
from abc import ABC, abstractmethod
from transformers import AutoModelForImageSegmentation

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SubjectMattingBase(ABC):
    """
    主体抠图工具基类 - 所有主体抠图类的基类
    定义了模型加载等通用功能
    """

    def __init__(self, device: str = None, model_name: str = "ZhengPeng7/BiRefNet"):
        """
        初始化主体抠图基类
        
        Args:
            device: 运行设备 ('cuda' 或 'cpu')
            model_name: 模型名称
        """
        # 自动选择设备
        self.device = device or self._get_device()
        self.model = None
        self.model_name = model_name
        self.logger = logger

    def _get_device(self):
        """
        自动检测可用设备
        """
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        elif torch.xpu.is_available():
            device = "xpu"
        self.logger.info(f"Use Device: {device}")
        return device

    def load_model(self) -> None:
        """
        加载主体抠图模型
        
        Args:
            model_name: 模型名称，如果为None则使用初始化时提供的名称
            local_model_path: 本地模型路径（可选）
        """
        # 修复 'Config' object has no attribute 'is_encoder_decoder' 错误
        # 通过添加额外的配置参数解决兼容性问题
        self.model = AutoModelForImageSegmentation.from_pretrained(
            self.model_name, 
            trust_remote_code=True, 
            force_download=False,
            config=None  # 显式设置 config 为 None，让 transformers 自动处理
        )

        
        self.model.to(self.device)
        self.model.eval()
        self.logger.info("主体抠图模型加载完成")

    @abstractmethod
    def process(self, *args, **kwargs):
        """
        抽象处理方法，由子类实现具体处理逻辑
        """
        pass