"""动画脚本解析Pipeline入口文件.

该文件用于运行动画脚本解析Pipeline。
"""

import asyncio
import re
from loguru import logger
from datetime import datetime
import pandas as pd

from agent import AnimationScriptPipeline


async def main():
    """主函数"""
    # 创建Pipeline实例
    pipeline = AnimationScriptPipeline()
    
    # 示例剧本片段
    sample_script = """
        孤岛生存为背景的短视频
    故事的最后一幕，故事反转，且引人深思
    """
    
    try:
        logger.info("原始故事:")
        logger.info(sample_script)
        
        # 完整处理流程
        logger.info("开始完整处理流程...")
        final_result, script_text = await pipeline.process_animation_story(sample_script)
        
        # 保存结果到Excel文件
        save_to_excel(final_result, script_text)
        
        logger.info("动画脚本解析完成，结果已保存到Excel文件")
        return final_result
        
    except Exception as e:
        logger.error(f"解析过程中出现错误: {e}")
        raise


def extract_character_design(script_text):
    """
    从剧本设计中提取角色设计信息
    
    Args:
        script_text (str): 剧本设计文本
        
    Returns:
        list: 包含角色设计信息的字典列表
    """
    character_data = []
    
    # 使用正则表达式提取角色信息
    # 这里假设角色信息在"角色介绍"部分
    character_section = re.search(r"[角色介绍|人物设定].*?(?=\n\n|\n[^-]|\Z)", script_text, re.DOTALL)
    
    if character_section:
        character_text = character_section.group()
        # 提取每个角色的信息
        characters = re.findall(r"-.*?(?=\n-|\Z)", character_text, re.DOTALL)
        
        for character in characters:
            # 提取角色名称
            name_match = re.search(r"[:：]\s*([^,\n]+)", character)
            name = name_match.group(1).strip() if name_match else "未知角色"
            
            # 提取角色类型、性格特点和形象设计
            type_match = re.search(r"[类型|种类][:：]\s*([^,\n]+)", character)
            character_type = type_match.group(1).strip() if type_match else "未知类型"
            
            personality_match = re.search(r"[性格|特点][:：]\s*([^,\n]+)", character)
            personality = personality_match.group(1).strip() if personality_match else "未知性格"
            
            design_match = re.search(r"[形象|外观|设计][:：]\s*(.*?)(?=\n|$)", character, re.DOTALL)
            design = design_match.group(1).strip() if design_match else "无详细描述"
            
            character_data.append({
                "角色名称": name,
                "角色类型": character_type,
                "性格特点": personality,
                "形象设计": design
            })
    
    return character_data


def save_to_excel(animation_output, script_text):
    """
    将动画脚本输出保存到Excel文件
    
    Args:
        animation_output: AnimationScriptOutput对象
        script_text: 剧本设计文本
    """
    # 生成文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"animation_script_{timestamp}.xlsx"
    
    # 将StoryboardInfo列表转换为字典列表
    storyboard_data = []
    for storyboard in animation_output.storyboards:
        storyboard_data.append({
            "镜号": storyboard.shot_id,
            "情节标题": storyboard.plot_title,
            "画面构图描述": storyboard.scene_elements,
            "画面中相关动作": storyboard.actions,
            "运镜": storyboard.shot_movement,
            "BGM描述": storyboard.bgm_description,
            "特效音描述": storyboard.sound_effect,
            "建议时长": storyboard.duration
        })
    
    # 创建DataFrame
    storyboard_df = pd.DataFrame(storyboard_data)
    
    # 提取角色设计信息
    character_data = extract_character_design(script_text)
    character_df = pd.DataFrame(character_data) if character_data else pd.DataFrame(columns=["角色名称", "角色类型", "性格特点", "形象设计"])
    
    # 保存到Excel文件
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        storyboard_df.to_excel(writer, sheet_name='分镜脚本', index=False)
        logger.info(f"分镜脚本已保存到 {filename} 的'分镜脚本'工作表中")
        
        if not character_df.empty:
            character_df.to_excel(writer, sheet_name='角色设计', index=False)
            logger.info(f"角色设计已保存到 {filename} 的'角色设计'工作表中")
        else:
            # 创建一个空的工作表
            pd.DataFrame([["未检测到角色设计信息"]], columns=["提示"]).to_excel(writer, sheet_name='角色设计', index=False)
            logger.info("未检测到角色设计信息")


if __name__ == "__main__":
    asyncio.run(main())