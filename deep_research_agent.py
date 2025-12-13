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
        # Do not set os.environ["GOOGLE_API_KEY"] globally to avoid conflicts
        # Initialize client directly with the key
        self.api_key = api_key
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

【你的任务】
请利用Google Deep Research的强大能力，根据用户的具体需求进行深度研究。
如果用户没有提供具体指令，请主动进行全面的全球宏观市场分析，涵盖经济周期、货币政策、地缘政治风险及大类资产配置建议。
请确保你的分析具有前瞻性、数据驱动，并符合顶级投行研报的专业水准。
"""

        elif mode == DeepResearchAgent.MODE_STRATEGY:
            return """
你是一位量化投资策略专家（Quantitative Strategy Director），拥有MIT金融工程博士学位，曾在Two Sigma、DE Shaw担任多因子策略负责人。

【你的专业领域】
1. 多因子选股模型（价值、成长、质量、动量、低波）
2. 资产配置框架（Black-Litterman、风险平价、全天候）
3. 组合优化算法（均值方差、CVaR、Kelly公式）
4. 回测与归因分析（Sharpe、Calmar、信息比率）

【你的任务】
请利用Google Deep Research的强大能力，根据用户的具体需求进行深度量化策略研究。
如果用户没有提供具体指令，请主动分享一个具有实战价值的量化策略思路，包括理论基础、因子构建、风险管理及可能的历史表现分析。
请确保你的分析逻辑严密、学术基础扎实，并尽可能提供可落地的实施细节。
"""

        elif mode == DeepResearchAgent.MODE_STOCK:
            if not symbol:
                raise ValueError("Stock mode requires symbol parameter")

            return f"""
你是一位顶级股票分析师（Senior Equity Analyst），拥有CFA、CPA双证，曾在摩根士丹利担任{symbol}所属行业的首席分析师，连续5年获得《机构投资者》最佳分析师称号。

【你的专业领域】
1. 商业模式深度拆解（Porter五力模型）
2. 财务质量诊断（杜邦分析、现金流质量）
3. 竞争优势评估（护城河宽度、ROIC vs WACC）
4. 估值定价（DCF、相对估值、实物期权）

【你的任务】
请利用Google Deep Research的强大能力，对 {symbol} 进行全方位的深度投资价值分析。
请根据用户的具体关注点进行针对性研究。如果用户没有具体指令，请进行标准的深度个股覆盖，包括但不限于：商业模式、行业竞争格局、财务健康度、增长驱动力、潜在风险及估值分析。
请确保你的观点客观中立，所有论据都有详实的数据或事实支撑。
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

【通用输出要求】
1. 请使用专业的Markdown格式进行排版，确保文档结构清晰、易读。
2. 研究报告应内容详实、数据丰富，充分展现Deep Research的深度搜索与分析能力。
3. 请引用可靠的信息来源，并在报告末尾附上参考文献。

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

                    # --- ENHANCED LOGGING START ---
                    # Inspect internal attributes to see what the agent is doing
                    debug_info = {}
                    try:
                        # Try to extract potential debug fields if they exist in the SDK response
                        # Note: The actual field names depend on the specific API version/model structure
                        # We log everything valid to find the clue.
                        for attr in dir(current_interaction):
                            if not attr.startswith('_') and not callable(getattr(current_interaction, attr)):
                                val = getattr(current_interaction, attr)
                                if val: debug_info[attr] = str(val)[:200] # Truncate long values
                    except:
                        pass
                    
                    logger.info(
                        f"[{attempt}/{self.MAX_RETRIES}] "
                        f"Elapsed: {elapsed_time}s | Status: {status} | Debug: {debug_info}"
                    )
                    # --- ENHANCED LOGGING END ---

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
                        # Try to get more error details
                        full_error_details = str(current_interaction)
                        logger.error(f"Research task failed: {error_msg} | Details: {full_error_details}")
                        return False, "", f"任务失败: {error_msg}"

                    elif status == "cancelled":
                        error_msg = "任务被取消"
                        logger.warning(error_msg)
                        return False, "", error_msg

                    # Wait before next poll
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.SLEEP_INTERVAL)

                except Exception as poll_error:
                    logger.error(f"Polling error at attempt {attempt}: {poll_error}", exc_info=True)
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.SLEEP_INTERVAL)
                    else:
                        return False, "", f"轮询过程中发生错误: {str(poll_error)}"

            # Timeout Handling - Enhanced
            timeout_msg = f"任务超时（{self.MAX_RETRIES * self.SLEEP_INTERVAL // 60}分钟）"
            logger.error(timeout_msg)
            
            # Try to print the final state before giving up
            try:
                final_state = self.client.interactions.get(interaction.id)
                logger.error(f"Final Interaction State on Timeout: {final_state}")
            except:
                logger.error("Could not fetch final state on timeout.")

            return False, "", timeout_msg

        except Exception as e:
            error_msg = f"Deep Research 失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, "", error_msg

    def run_async_task(self, task_id, mode, custom_prompt, symbol, knowledge_service, user_id):
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
                # Fix: If symbol is None (e.g. MACRO/STRATEGY mode), use mode as symbol
                save_symbol = symbol if symbol else mode
                
                save_result = knowledge_service.save_document(
                    save_symbol,
                    pdf_bytes,
                    filename,
                    doc_type='ultra_deep_report',
                    user_id=user_id
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
