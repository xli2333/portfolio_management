"""
Gemini Deep Research Agent Module
使用 Google 官方 Deep Research API 生成超级深度报告
"""

import time
import os
import logging
from typing import Dict, Optional, Tuple
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepResearchAgent:
    """Official Google Deep Research API Integration"""

    # Research mode constants
    MODE_MACRO = "MACRO"
    MODE_STRATEGY = "STRATEGY"
    MODE_STOCK = "STOCK"

    # Polling configuration
    MAX_RETRIES = 120  # 20 minutes max (120 * 10 seconds)
    SLEEP_INTERVAL = 10  # Poll every 10 seconds

    def __init__(self, api_key: str):
        """
        Initialize Deep Research Agent with user-provided API key

        Args:
            api_key: User's Gemini API key
        """
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        self.client = genai.Client(api_key=api_key)
        logger.info("Deep Research Agent initialized")

    @staticmethod
    def get_persona_prompt(mode: str, symbol: str = None) -> str:
        """
        Get ultra-detailed persona prompt for each research mode

        Args:
            mode: Research mode (MACRO/STRATEGY/STOCK)
            symbol: Stock symbol (required for STOCK mode)

        Returns:
            Formatted persona prompt
        """
        if mode == DeepResearchAgent.MODE_MACRO:
            return """
你是一位顶级宏观经济分析师（Chief Macro Strategist），拥有20年全球宏观研究经验，曾在高盛、桥水基金担任首席宏观策略师。

【你的专业领域】
1. 全球宏观经济政策分析（美联储、欧央行、中国央行货币政策）
2. 地缘政治风险评估（中美关系、能源政治、贸易战）
3. 大类资产配置逻辑（股债商品汇率联动）
4. 经济周期判断（康波周期、朱格拉周期、美林时钟）

【研究方法论】
- 自上而下框架：从全球流动性→区域经济→行业轮动
- 数据驱动：PMI、CPI、就业数据、国债收益率曲线
- 前瞻性思维：提前6-12个月预判拐点

【报告结构要求】
1. 执行摘要（500字）：核心观点 + 投资建议
2. 全球宏观格局（2000字）：
   - 美国经济周期位置
   - 中国增长动能分析
   - 欧洲滞胀风险
   - 新兴市场资本流动
3. 货币政策展望（1500字）：
   - 主要央行政策路径
   - 利率预期vs市场定价
   - 流动性拐点信号
4. 大类资产配置建议（1000字）：
   - 股票/债券/商品/现金配比
   - 风险偏好等级（1-10）
   - 对冲策略

【输出风格】
- 专业严谨：使用学术术语（如"菲利普斯曲线平坦化"）
- 数据充实：必须引用具体数据源和时间
- 观点鲜明：明确看多/看空，避免模棱两可

【引用要求】
每个关键论断必须标注数据来源，格式：
[数据源名称](URL) - 2025年12月12日
"""

        elif mode == DeepResearchAgent.MODE_STRATEGY:
            return """
你是一位量化投资策略专家（Quantitative Strategy Director），拥有MIT金融工程博士学位，曾在Two Sigma、DE Shaw担任多因子策略负责人。

【你的专业领域】
1. 多因子选股模型（价值、成长、质量、动量、低波）
2. 资产配置框架（Black-Litterman、风险平价、全天候）
3. 组合优化算法（均值方差、CVaR、Kelly公式）
4. 回测与归因分析（Sharpe、Calmar、信息比率）

【研究方法论】
- 学术严谨：基于Fama-French、AQR研究成果
- 实证驱动：至少10年历史数据回测
- 动态调整：根据市场regime切换策略

【报告结构要求】
1. 策略概述（400字）：
   - 策略类型（趋势/均值回归/套利）
   - 适用市场环境
   - 预期收益与风险
2. 理论基础（1500字）：
   - 学术论文支撑
   - 经济学逻辑解释
   - 行为金融学视角
3. 实施细节（2000字）：
   - 因子构建方法（公式 + 代码伪逻辑）
   - 组合权重计算
   - 再平衡频率
   - 交易成本考量
4. 历史表现（1000字）：
   - 2015-2025年回测结果
   - 年化收益、最大回撤、夏普比率
   - 分年度表现归因
5. 风险管理（800字）：
   - 止损机制
   - 对冲工具（期权、期货）
   - 极端情景压力测试

【输出风格】
- 定量为主：必须包含公式（如Sharpe = (Rp - Rf) / σp）
- 代码友好：策略逻辑可翻译为Python代码
- 风险透明：明确说明失效场景

【引用要求】
必须引用学术论文和量化研究报告：
[Fama & French (2015), "A Five-Factor Asset Pricing Model"](URL)
"""

        elif mode == DeepResearchAgent.MODE_STOCK:
            if not symbol:
                raise ValueError("Stock mode requires symbol parameter")

            return f"""
你是一位顶级股票分析师（Senior Equity Analyst），拥有CFA、CPA双证，曾在摩根士丹利担任{symbol}所属行业的首席分析师，连续5年获得《机构投资者》最佳分析师称号。

【你的研究框架】
1. 商业模式深度拆解（Porter五力模型）
2. 财务质量诊断（杜邦分析、现金流质量）
3. 竞争优势评估（护城河宽度、ROIC vs WACC）
4. 估值定价（DCF、相对估值、实物期权）

【{symbol} 研究大纲】
1. 公司概览（500字）：
   - 业务分部及收入占比
   - 市值、市盈率、市净率
   - 股东结构与管理层背景

2. 行业分析（1500字）：
   - 全球/区域市场规模与增速
   - 竞争格局（CR5集中度）
   - 技术趋势与颠覆性风险
   - 监管政策影响

3. 商业模式解构（1800字）：
   - 价值主张：解决什么痛点
   - 客户群体：B2B还是B2C
   - 收入模式：订阅/交易/广告
   - 成本结构：固定vs变动成本占比
   - 规模效应与边际成本递减

4. 财务分析（2000字）：
   - 过去5年营收/利润CAGR
   - 毛利率、净利率趋势
   - ROE、ROIC分解
   - 经营现金流/净利润比值
   - 资本支出与折旧
   - 负债率、利息覆盖倍数

5. 竞争优势（1200字）：
   - 品牌/网络效应/成本领先/技术壁垒
   - 与竞争对手对比（定量指标）
   - 护城河可持续性评估

6. 增长驱动力（1000字）：
   - 短期催化剂（新产品、并购）
   - 中期增长路径（地域扩张、品类延伸）
   - 长期愿景（TAM扩大）

7. 风险因素（800字）：
   - 行业风险（技术替代、政策变化）
   - 公司特定风险（客户集中度、管理层变动）
   - 财务风险（债务到期、现金流压力）

8. 估值与目标价（1500字）：
   - DCF模型：假设（WACC=X%, 永续增长=Y%）
   - 可比公司法：PE/PB/PS对比
   - 敏感性分析：不同情景下的合理价格区间
   - 12个月目标价及上行/下行空间

9. 投资建议（300字）：
   - 评级：强烈买入/买入/持有/卖出
   - 适合投资者类型（价值/成长/收益）
   - 建议持仓占比

【数据要求】
- 所有财务数据必须注明来源和时间
- 引用至少3家竞争对手对比
- 至少10条新闻/研报参考链接

【输出风格】
- 深度优先：宁可5000字说透一个问题，不要泛泛而谈
- 批判性思维：质疑管理层指引，寻找财务异常
- 客观中立：同时呈现多空观点

【引用格式】
[公司名称 2024 Q3 财报](URL) - 2024年11月15日
[行业研究机构报告](URL) - 2025年1月
"""
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def generate_report(
        self,
        mode: str,
        custom_prompt: str,
        symbol: str = None,
        status_callback=None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate ultra-deep research report using official Deep Research API

        Args:
            mode: Research mode (MACRO/STRATEGY/STOCK)
            custom_prompt: User's custom research question/topic
            symbol: Stock symbol (required for STOCK mode)
            status_callback: Optional callback function(status_msg) for progress updates

        Returns:
            Tuple of (success: bool, markdown_report: str, error_msg: Optional[str])
        """
        try:
            # Get persona prompt
            persona_prompt = self.get_persona_prompt(mode, symbol)

            # Combine persona with user's custom prompt
            final_prompt = f"""{persona_prompt}

【用户研究需求】
{custom_prompt}

【输出要求】
1. 必须使用专业的Markdown格式（标题层级、列表、表格）
2. 必须包含大量具体数据和引用链接
3. 报告总字数不少于5000字
4. 所有关键论断必须有数据支撑
5. 最后必须附上完整的参考文献列表

现在请开始深度研究并输出完整报告。
"""

            if status_callback:
                status_callback(f"正在提交 Deep Research 任务到 Google...")

            # Create interaction using official API
            interaction = self.client.interactions.create(
                agent="deep-research-pro-preview-12-2025",
                input=final_prompt,
                background=True
            )

            logger.info(f"Deep Research task submitted. Interaction ID: {interaction.id}")

            if status_callback:
                status_callback(f"任务已提交 (ID: {interaction.id[:8]}...)，开始轮询...")

            # Poll for completion
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    current_interaction = self.client.interactions.get(interaction.id)
                    status = current_interaction.status

                    elapsed_time = attempt * self.SLEEP_INTERVAL
                    elapsed_minutes = elapsed_time // 60

                    if status_callback:
                        status_callback(
                            f"研究进行中... ({elapsed_minutes}分{elapsed_time % 60}秒) - 状态: {status}"
                        )

                    logger.info(
                        f"[{attempt}/{self.MAX_RETRIES}] "
                        f"Elapsed: {elapsed_time}s | Status: {status}"
                    )

                    if status == "completed":
                        if current_interaction.outputs:
                            raw_report = current_interaction.outputs[-1].text

                            # Apply Markdown cleaning (same as report_generator.py logic)
                            cleaned_report = self._clean_markdown(raw_report)

                            logger.info(f"Research completed successfully. Report length: {len(cleaned_report)} chars")

                            if status_callback:
                                status_callback("✓ 研究完成！正在处理报告...")

                            return True, cleaned_report, None
                        else:
                            error_msg = "任务完成但未返回输出内容"
                            logger.error(error_msg)
                            return False, "", error_msg

                    elif status == "failed":
                        error_msg = getattr(current_interaction, 'error', '未知错误')
                        logger.error(f"Research task failed: {error_msg}")
                        return False, "", f"任务失败: {error_msg}"

                    elif status == "cancelled":
                        error_msg = "任务被取消"
                        logger.warning(error_msg)
                        return False, "", error_msg

                    # Wait before next poll
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.SLEEP_INTERVAL)

                except Exception as poll_error:
                    logger.error(f"Polling error at attempt {attempt}: {poll_error}")
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.SLEEP_INTERVAL)
                    else:
                        return False, "", f"轮询过程中发生错误: {str(poll_error)}"

            # Timeout
            error_msg = f"任务超时（{self.MAX_RETRIES * self.SLEEP_INTERVAL // 60}分钟）"
            logger.error(error_msg)
            return False, "", error_msg

        except Exception as e:
            error_msg = f"Deep Research 失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def run_async_task(self, task_id, mode, custom_prompt, symbol, knowledge_service):
        """
        Background worker function for async execution
        """
        from task_manager import TaskManager
        from report_generator import create_markdown_pdf
        from datetime import datetime
        
        tm = TaskManager()
        
        try:
            tm.update_task(task_id, status="processing", progress="正在初始化 Agent...")
            
            def progress_callback(msg):
                tm.update_task(task_id, progress=msg)
                
            success, report_text, error = self.generate_report(
                mode=mode, 
                custom_prompt=custom_prompt, 
                symbol=symbol,
                status_callback=progress_callback
            )
            
            if success:
                tm.update_task(task_id, progress="研究完成，正在生成 PDF...")
                
                # Generate PDF
                pdf_bytes = create_markdown_pdf(symbol, report_text)
                filename = f"UltraDeepReport_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Save using existing service (Saves to Disk + Supabase Metadata)
                # Note: user_id is passed as 'system_agent' or similar since we lack context here, 
                # or we could pass it from web_app. Let's use 'async_agent'.
                save_result = knowledge_service.save_document(
                    symbol,
                    pdf_bytes,
                    filename,
                    doc_type='ultra_deep_report',
                    user_id='async_agent'
                )
                
                result_data = {
                    "report_text_preview": report_text[:500] + "...",
                    "report_length": len(report_text),
                    "file_record": save_result
                }
                
                tm.update_task(task_id, status="completed", result=result_data, progress="已完成")
            else:
                tm.update_task(task_id, status="failed", error=error, progress="任务失败")
                
        except Exception as e:
            logger.error(f"Async task failed: {e}", exc_info=True)
            tm.update_task(task_id, status="failed", error=str(e), progress="发生系统错误")

    @staticmethod
    def _clean_markdown(raw_markdown: str) -> str:
        """
        Clean Markdown text (same logic as report_generator.py)
        Removes certain formatting for better PDF rendering

        Args:
            raw_markdown: Raw markdown text from Deep Research API

        Returns:
            Cleaned markdown text
        """
        # Basic cleaning - remove excessive bold/italic markers
        # Note: We keep structural markdown (headers, lists) intact
        # Only clean inline formatting that might interfere with PDF generation

        cleaned = raw_markdown

        # Don't strip ** and __ completely - instead normalize them
        # This preserves emphasis while ensuring PDF compatibility
        # The actual PDF generation will handle these

        # Remove potential problematic characters
        cleaned = cleaned.replace('\r\n', '\n')  # Normalize line endings
        cleaned = cleaned.replace('\r', '\n')

        # Remove excessive blank lines (more than 2 consecutive)
        import re
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned.strip()
