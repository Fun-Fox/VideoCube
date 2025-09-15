# 视频创作魔方

收集日常批量视频创作过程中使用的一些工具集

# 剧本编辑器
其中有不同角色

使用[PocketFlow]{https://github.com/The-Pocket/PocketFlow} 构建AI Agent 框架
实现三个角色：

绘画风格：提示词
角色、场景描述
# 分镜生图
分镜图片（这个图片需要几张图、图与图之间首尾帧切换）

# 图生视频
视频运镜、角色动作

# 工具箱

## 抠像工具箱

```commandline
# nvcc -V
# pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128 -i https://pypi.tuna.tsinghua.edu.cn/simple/
# conda install -c conda-forge ffmpeg
```

### 人像抠像

### 主体抠像

经过测试主体精度> 人像

速度方面 人像> 主体

## 视频处理

### CodeCut

使用代码进行视频剪辑工具
