"""
Gemini Deep Research API 测试脚本
基于 Google Interactions API 文档实现
"""

import time
import os
from google import genai
from google.genai import types

# 设置 API Key
API_KEY = "AIzaSyCwuOLuKsOjAI08XldWMhMcvQgpII9nhdI"
os.environ["GOOGLE_API_KEY"] = API_KEY

# 1. 初始化客户端
print("=== 初始化 Gemini Deep Research 客户端 ===")
client = genai.Client(api_key=API_KEY)

# 2. 定义研究目标
# 根据文档，明确的结构化问题能显著提升报告质量
research_prompt = """
请对 2025 年全球人工智能芯片市场进行深入研究。

重点关注以下方面：
1. NVIDIA、AMD、Google TPU 等主要参与者的技术路线对比
2. AI 芯片在训练和推理场景中的性能差异
3. 2025 年市场规模预测和增长趋势

请以专业技术报告的形式输出，包含执行摘要、详细分析和数据对比。
"""

print("=== 研究主题 ===")
print(research_prompt)
print("\n" + "="*60 + "\n")

# 3. 创建交互 (Interaction)
# 关键点：
# - agent 必须为 "deep-research-pro-preview-12-2025"
# - background 必须为 True
# - agent_config 中的 thinking_summaries: "auto" 可获取思维过程
print("=== 正在提交 Deep Research 任务 ===")

try:
    # 使用最简配置（只包含必需参数）
    interaction = client.interactions.create(
        agent="deep-research-pro-preview-12-2025",  # 必须使用这个代理名称
        input=research_prompt,
        background=True  # 必须开启后台模式
    )

    print(f"✓ 任务已提交成功")
    print(f"✓ 交互 ID (Interaction ID): {interaction.id}")
    print(f"✓ 初始状态: {interaction.status}")
    print("\n" + "="*60 + "\n")

except Exception as e:
    print(f"✗ 提交任务失败: {e}")
    exit(1)

# 4. 轮询获取结果
# 根据文档，Deep Research 任务可能需要数分钟
# 建议设置合理的轮询间隔和最大重试次数
MAX_RETRIES = 60  # 最大尝试次数（约 10 分钟）
SLEEP_INTERVAL = 10  # 每次等待 10 秒

print("=== 开始轮询任务状态 ===")
print(f"最大等待时间: {MAX_RETRIES * SLEEP_INTERVAL // 60} 分钟")
print(f"轮询间隔: {SLEEP_INTERVAL} 秒\n")

for attempt in range(1, MAX_RETRIES + 1):
    try:
        # 获取交互的最新状态
        # 注意：直接传递 ID，不使用关键字参数
        current_interaction = client.interactions.get(interaction.id)
        status = current_interaction.status

        # 显示进度
        elapsed_time = attempt * SLEEP_INTERVAL
        print(f"[{attempt}/{MAX_RETRIES}] 已等待 {elapsed_time}秒 | 当前状态: {status}")

        # 检查状态
        if status == "completed":
            print("\n" + "="*60)
            print("=== ✓ 研究任务完成 ===")
            print("="*60 + "\n")

            # 最终报告通常位于 outputs 列表的最后一个元素
            if current_interaction.outputs:
                final_report = current_interaction.outputs[-1].text

                # 保存报告到文件
                output_file = "deep_research_report.md"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(final_report)

                print("=== 研究报告 ===\n")
                print(final_report)
                print(f"\n\n报告已保存至: {output_file}")
            else:
                print("⚠ 警告：任务完成但未发现输出内容。")

            break

        elif status == "failed":
            print("\n" + "="*60)
            print("=== ✗ 任务失败 ===")
            print("="*60)
            print(f"错误信息: {current_interaction.error if hasattr(current_interaction, 'error') else '未知错误'}")
            break

        elif status == "cancelled":
            print("\n" + "="*60)
            print("=== 任务被取消 ===")
            print("="*60)
            break

        # 等待后再次轮询
        if attempt < MAX_RETRIES:
            time.sleep(SLEEP_INTERVAL)

    except Exception as e:
        print(f"⚠ 轮询过程中发生错误: {e}")
        # 在网络波动时，可以选择重试而不是直接退出
        if attempt < MAX_RETRIES:
            time.sleep(SLEEP_INTERVAL)
else:
    print("\n" + "="*60)
    print("=== ⏱ 任务超时 ===")
    print("="*60)
    print(f"任务未能在规定时间内完成（{MAX_RETRIES * SLEEP_INTERVAL // 60} 分钟）")
    print(f"交互 ID: {interaction.id}")
    print("您可以稍后使用此 ID 继续查询任务状态")

print("\n=== 脚本执行完毕 ===")
