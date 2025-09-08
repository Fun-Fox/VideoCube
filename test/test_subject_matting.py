"""
抠像工具测试文件
"""

import logging
import os

from tools import SubjectMattingTool

# 设置日志级别
logging.basicConfig(level=logging.INFO)
root_dir = os.path.dirname(os.path.abspath(__file__))


def test_image_matting():
    """测试图片抠像"""
    print("=== 测试图片抠像 ===")
    try:
        tool = SubjectMattingTool(model_name="ZhengPeng7/BiRefNet")
        # 示例用法（需要实际的测试图片）:
        tool.matting_image(os.path.join(root_dir, "assets", "test_input.png"),  os.path.join(root_dir, "subject_output_frames","test_output.png"),)
        print("图片抠像测试完成")
    except Exception as e:
        print(f"图片抠像测试失败: {e}")


def test_video_matting():
    """测试视频抠像"""
    print("=== 测试视频抠像 ===")
    try:
        tool = SubjectMattingTool(model_name="ZhengPeng7/BiRefNet",batch_size=2)
        # 示例用法（需要实际的测试视频）:

        result_path = tool.matting_video(os.path.join(root_dir, "assets", "test_input.mp4"),
                                         os.path.join(root_dir, "subject_output_frames"))
        print("视频抠像测试完成")
    except Exception as e:
        print(f"视频抠像测试失败: {e}")


def test_batch_processing():
    """测试批量处理"""
    print("=== 测试批量处理 ===")
    try:
        tool = SubjectMattingTool(batch_size=2)
        # 示例用法（需要实际的测试文件夹）:
        tool.batch_process_videos("input_videos", "subject_output_videos")
        print("批量处理测试完成")
    except Exception as e:
        print(f"批量处理测试失败: {e}")


if __name__ == "__main__":
    # 运行测试
    # test_image_matting()
    test_video_matting()
    # test_batch_processing()
