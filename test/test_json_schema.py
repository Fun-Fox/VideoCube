import json
from typing import Dict, Any


def resolve_refs(schema: Dict[Any, Any], defs: Dict[str, Any] = None) -> Dict[Any, Any]:
    """
    递归解析并展开JSON Schema中的$ref引用
    """
    if defs is None:
        # 提取根级别的$defs
        defs = schema.get('$defs', {})

        # 同时检查parameters中的$defs（针对tools结构）
        if 'tools' in schema:
            for tool in schema['tools']:
                if 'function' in tool and 'parameters' in tool['function']:
                    tool_defs = tool['function']['parameters'].get('$defs', {})
                    defs.update(tool_defs)

    def resolve_value(value):
        if isinstance(value, dict):
            # 如果遇到$ref，替换为实际定义
            if '$ref' in value:
                ref_path = value['$ref']
                if ref_path.startswith('#/$defs/'):
                    def_name = ref_path.split('/')[-1]
                    if def_name in defs:
                        # 递归解析引用的定义
                        resolved = resolve_refs(defs[def_name], defs)
                        # 合并引用定义中的其他属性
                        result = resolved.copy()
                        for key, val in value.items():
                            if key != '$ref':
                                result[key] = val
                        return result
                elif ref_path.startswith('#/properties/'):
                    # 处理其他类型的引用
                    logger.warning(f"Unsupported reference format: {ref_path}")
            # 递归处理嵌套字典
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            # 递归处理列表
            return [resolve_value(item) for item in value]
        else:
            return value

    # 处理整个schema
    resolved_schema = resolve_value(schema)

    # 移除所有层级的$defs
    def remove_defs(obj):
        if isinstance(obj, dict):
            if '$defs' in obj:
                del obj['$defs']
            for key, value in obj.items():
                remove_defs(value)
        elif isinstance(obj, list):
            for item in obj:
                remove_defs(item)

    remove_defs(resolved_schema)

    return resolved_schema


# 使用示例
original_schema = {
  "messages": [
    {
      "role": "system",
      "content": "# 剧本设计Agent提示词\n\n你是一个专业的动画剧本设计师，负责将动画故事转化为详细剧本设计。\n\n## 核心要求\n\n### 角色设定\n- 每个角色需有明确性格特征和行为逻辑\n- 角色数量控制在1-3个\n- 角色类型不限（人类、动物、植物、物品等）\n- 提供详细形象设计（外观、服装、特征等）\n\n### 场景安排\n- 每个场景需有明确描述\n- 场景转换要自然流畅\n- 场景设计要考虑动画制作的可行性\n\n### 情节发展\n- 具备起承转合结构\n- 设置多个情节点保持观众兴趣\n- 符合短视频节奏\n- 情节发展要逻辑清晰，有因果关系\n\n## 输出格式\n- 角色介绍（含性格特点和形象设计）\n- 情节发展（详细描述起承转合和关键情节点）\n\n## 设计原则\n- 严格遵循故事内容\n- 角色设定要服务于故事表达\n- 场景安排要考虑视觉表现力\n- 情节发展要有节奏感和戏剧冲突"
    },
    {
      "role": "user",
      "content": "好的，收到您的需求。这不是一个传统的故事梗概，而是一个基于真实事件疑虑的创作需求。我将扮演故事优化师，将这些尖锐的质询点，转化为一个充满戏剧张力、解答疑惑并传递品牌价值的60秒动画短故事。\n\n---\n\n### **故事优化方案**\n\n**核心思路：** 将公众的“质疑”拟人化，通过一位品牌内部的“守护者”角色，展现品牌在面对挑战时的思考、挣扎与最终选择，从而正面回应所有疑虑，完成一次漂亮的情感和价值沟通。\n\n**故事名称：** 《雪山上的第53次实验》\n\n**核心价值：** 真正的向上，是带着敬畏。\n\n---\n\n### **60秒动画故事脚本**\n\n**(0-3秒) 故事钩子 (悬念引导型 + 冲突前置)**\n\n*   **画面：** 极简风格动画。一座雄伟、静谧的雪山之巅，纯白圣洁。突然，一朵绚烂的虚拟“烟花”在屏幕中央炸开，但随之出现的不是喝彩，而是红色加粗的弹幕式提问，覆盖在烟花上：\n    *   **“高海拔放烟花？”**\n    *   **“作秀还是破坏？”**\n    *   **“考虑过生态吗？”**\n*   **音效：** 雄浑安静的环境风声，被一声刺耳的“滋啦”（类似错误提示音）打断，配合弹幕出现。\n*   **潜台词：** 我们知道你们在担心什么，现在就来回答。\n\n**(4-15秒) 情节展开 & 第一次反转 (引入核心冲突)**\n\n*   **画面：** 场景切换到一间明亮的会议室。项目经理（形象略显急切）指着雪山活动方案PPT，兴奋地说：“我们要在这里，举办一场前所未有的烟花大秀！”\n*   **画面：** 镜头给到角落里的一位年轻女工程师，**小林**（戴着黑框眼镜，眼神坚毅，胸前有始祖鸟logo工牌）。她猛地站起来，打断了会议。\n*   **小林（台词，坚定）：** “不行。常规烟花中的重金属和塑料微粒，在高寒环境下数百年都无法降解。这对山脉是不可逆的伤害。”\n*   **音效：** 会议室瞬间安静，只有小林坚定的声音。\n*   **第一次反转：** 品牌的赞助计划，首先被自己内部的“环保红线”叫停了。\n\n**(16-40秒) 核心解密 & 第二次反转 (展现行动与论证)**\n\n*   **画面：** 快速蒙太奇，展现小林和她的团队如何解决问题。\n    *   **(16-25秒) 生态评估：** 小林和同事穿着始祖鸟冲锋衣，在雪山上采集土壤和冰芯样本，在显微镜下进行分析。（回应“是否进行生态学评估”）\n    *   **(26-35秒) 科学论证：** 场景切换到实验室。白板上写满了化学分子式。小林团队将不同材料放入-30℃的低温模拟环境中进行测试。一块普通烟花材料毫无变化，而另一块新型材料（旁边标注：植物淀粉基粘合剂、无毒矿物色素）在微生物作用下，开始缓慢分解。（回应“是否科学论证降解性”）\n    *   **(36-40秒) 角色特写：** 经历了52次失败后，第53次实验的样本在模拟环境中完美降解。小林和团队成员疲惫但欣慰地笑了。\n*   **音效：** 紧张而富有节奏感的背景音乐，配合实验仪器声、笔在白板上划过的声音，最后在成功一刻归于平静和舒缓。\n*   **第二次反转：** 品牌的角色不是烟花的“燃放者”，而是“重塑者”。他们投入巨大成本，不是为了办一场秀，而是为了攻克一个环保难题。\n\n**(41-55秒) 高潮 & 最终结局 (情感闭环)**\n\n*   **画面：** 回到雪山之巅的夜晚。烟花升空，但绽放的效果更柔和、空灵。没有浓烟，没有刺鼻气味。\n*   **关键特写：** 一片雪花般的“烟花尘埃”缓缓飘落，落在小林戴着手套的手心。它不是灼热的灰烬，而是一触即化的、冰晶般的白色粉末。\n*   **旁白 (温暖、诚恳的男声):** “始祖鸟赞助的，不是一场烟花秀。而是一次承诺的兑现：用52次失败和无数次科学论证，换来一场‘会消失’的烟花。它唯一的痕迹，是回归自然的敬畏之心。”\n*   **画面：** 烟花下，人们仰望星空，表情宁静而感动。没有狂热的喧嚣。\n*   **音效：** 烟花声效减弱，更像风铃和冰晶碰撞的声音。背景是悠远、空灵的音乐。\n\n**(56-60秒) 价值升华 & 品牌落点**\n\n*   **画面：** 第二天清晨，日出金光洒满雪山，一切洁白如初，仿佛什么都未发生。小林站在山巅，深深吸了一口清冽的空气，露出释然的微笑。\n*   **画面：** 屏幕中央缓缓浮现文字：\n    *   **“对自然的敬畏，是攀登的唯一方向。”**\n*   **结尾画面：** 始祖鸟Logo出现，简洁有力。\n*   **音效：** 清晨的鸟鸣和风声，音乐收尾。\n\n---\n### **优化小结**\n\n1.  **角色塑造：** 创造了“小林”这一核心角色，她既是品牌专业精神的化身，也是环保理念的守护者，让冰冷的科学论证过程变得有血有肉。\n2.  **结构反转：** 通过“内部叫停 -> 攻克难题 -> 完美呈现”的三次反转，将一个可能引起负面舆情的事件，转变为展现品牌责任感和科技实力的正面故事。\n3.  **解答疑虑：** 将用户关心的“生态评估”、“科学论证”、“材料降解”等核心问题，巧妙地融入到故事蒙太奇中，用视觉化的方式给出答案，比单纯的文字解释更有说服力。\n4.  **情感共鸣：** 故事的落点不是炫耀烟花多美，而是强调“敬畏之心”和“守护”的品牌价值观，与目标用户（户外爱好者、环保关注者）建立深层情感链接。\n5.  **短视频适配：** 严格遵循60秒节奏，开篇即冲突，中间快节奏展现，结尾慢下来升华情感，完全符合短视频的观看习惯。"
    }
  ],
  "model": "gemini-2.5-pro",
  "stream": False,
  "tool_choice": "required",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "final_result",
        "description": "剧本设计输出",
        "parameters": {
          "properties": {
            "characters": {
              "description": "角色设计列表",
              "items": {
                "$ref": "#/$defs/CharacterDesign"
              },
              "type": "array"
            },
            "plot_points": {
              "description": "情节点列表",
              "items": {
                "$ref": "#/$defs/PlotPoint"
              },
              "type": "array"
            }
          },
          "required": [
            "characters",
            "plot_points"
          ],
          "type": "object",
          "additionalProperties": False,
          "$defs": {
            "CharacterDesign": {
              "description": "角色设计信息",
              "properties": {
                "name": {
                  "description": "角色名称",
                  "type": "string"
                },
                "characteristics": {
                  "description": "角色性格特点",
                  "type": "string"
                },
                "appearance": {
                  "description": "角色外貌描述",
                  "type": "string"
                }
              },
              "required": [
                "name",
                "characteristics",
                "appearance"
              ],
              "type": "object",
              "additionalProperties": False
            },
            "PlotPoint": {
              "description": "情节点信息",
              "properties": {
                "title": {
                  "description": "情节点标题",
                  "type": "string"
                },
                "description": {
                  "description": "情节点详细描述",
                  "type": "string"
                }
              },
              "required": [
                "title",
                "description"
              ],
              "type": "object",
              "additionalProperties": False
            }
          }
        },
        "strict": True
      }
    }
  ]
}

# 解析引用
flattened_schema = resolve_refs(original_schema)
print(json.dumps(flattened_schema, indent=2))
