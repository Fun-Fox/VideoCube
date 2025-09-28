"""动画脚本解析Pipeline入口文件.

该文件用于运行动画脚本解析Pipeline。
"""

import asyncio
import re
from agent.log_config import logger
from datetime import datetime
import pandas as pd

from agent import AnimationScriptPipeline
from agent.models import ScriptDesignOutput


async def main():
    """主函数"""
    # 创建Pipeline实例
    pipeline = AnimationScriptPipeline()
    
    # 示例剧本片段
    sample_script = """
       始祖鸟在极高海拔地区赞助该活动的原因，在烟花秀中始祖鸟的角色，是否在事前进行了生态学评估，是否科学论证过在高海拔、低温环境下烟花材料的降解性不会对生态造成破坏等。
    """
    
    # 获取可用模板
    story_templates = pipeline.template_manager.list_story_templates()
    storyboard_templates = pipeline.template_manager.list_storyboard_templates()
    
    logger.info(f"可用故事模板: {story_templates}")
    logger.info(f"可用分镜模板: {storyboard_templates}")
    
    # 选择使用的模板（这里可以设置为具体的模板文件名，或者None表示不使用模板）
    story_template = None  # 示例: "example_story_template.md"
    storyboard_template = None  # 示例: "example_storyboard_template.md"
    
    try:
        logger.info("原始故事:")
        logger.info(sample_script)
        
        # 完整处理流程
        logger.info("开始完整处理流程...")
        final_result, script_design = await pipeline.process_animation_story(
            sample_script, 
            story_template=story_template,
            storyboard_template=storyboard_template
        )
        
        # 保存结果到Excel文件
        save_to_excel(final_result, script_design)
        
        logger.info("动画脚本解析完成，结果已保存到Excel文件")
        return final_result
        
    except Exception as e:
        logger.error(f"解析过程中出现错误: {e}")
        raise


def extract_character_design(script_design: ScriptDesignOutput):
    """
    从剧本设计中提取角色设计信息
    
    Args:
        script_design (ScriptDesignOutput): 剧本设计结构化数据
        
    Returns:
        list: 包含角色设计信息的字典列表
    """
    character_data = []
    
    # 直接从ScriptDesignOutput模型中提取角色信息
    for character in script_design.characters:
        character_data.append({
            "角色名称": character.name,
            "性格特点": character.characteristics,
            "形象设计": character.appearance
        })
    
    return character_data


def save_to_excel(animation_output, script_design):
    """
    将动画脚本输出保存到Excel文件
    
    Args:
        animation_output: AnimationScriptOutput对象
        script_design: ScriptDesignOutput对象
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
            "画面描述": storyboard.scene_elements,
            "动作设计": storyboard.actions,
            "旁白": storyboard.narrator,
            "BGM描述": storyboard.bgm_description,
            "特效音描述": storyboard.sound_effect,
            "建议时长": storyboard.duration
        })
    
    # 创建DataFrame
    storyboard_df = pd.DataFrame(storyboard_data)
    
    # 提取角色设计信息
    character_data = extract_character_design(script_design)
    character_df = pd.DataFrame(character_data) if character_data else pd.DataFrame(columns=["角色名称",  "性格特点", "形象设计"])
    
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