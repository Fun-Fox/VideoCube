# 视频创作魔方

收集日常批量视频创作过程中使用的一些工具集

# 剧本编辑器

其中有不同角色

使用(pydantic-ai)[https://github.com/pydantic/pydantic-ai] 
实现剧本编辑Agent

![](doc/1.png)


# 工具箱

## 抠像工具箱

```commandline
# nvcc -V
# pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128 -i https://pypi.tuna.tsinghua.edu.cn/simple/
# conda install -c conda-forge ffmpeg
```

### 人像抠像

### 主体抠像

经过测试

主体抠像的精度方面 大于 人像抠像

生成速度方面 人像抠像 大于 主体抠像

## 视频处理

### CodeCut

使用代码进行视频剪辑工具
