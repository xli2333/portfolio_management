import os
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AnalystAgent:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found for AnalystAgent")
        else:
            self.client = genai.Client(api_key=self.api_key)

    def _run_research_task(self, symbol: str, role: str, focus_area: str, model_name: str = "gemini-2.5-flash") -> str:
        """
        Executes a specific research sub-task using Google Search.
        Using Flash model for speed and efficiency in information gathering.
        """
        prompt = f"""
You are a professional {role} analyzing {symbol}.
Your goal is to gather FACTUAL information from the internet regarding: {focus_area}.

Please perform a Google Search and summarize your findings in concise bullet points.
Include numbers, dates, and sources where possible. Do not write a full essay, just key facts.
"""
        # Configure Search Tool
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[grounding_tool])

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return response.text if response.text else f"[No data found by {role}]"
        except Exception as e:
            logger.warning(f"{role} failed: {e}")
            return f"[Search Error for {role}: {e}]"

    def generate_deep_research_report(self, symbol: str, context_text: str = "", model_name: str = "gemini-2.5-pro") -> str:
        """
        Multi-Agent Workflow:
        1. 3 Sub-Agents gather info (Data, Industry, Corp).
        2. Main Agent synthesizes everything into a report.
        Returns: final_report_text
        """
        if not self.api_key:
            return "Error: API Key missing."

        logger.info(f"Starting Multi-Agent Research for {symbol}...")

        # --- Phase 1: Distributed Research (Sub-Agents) ---
        # 1. Data Analyst
        data_research = self._run_research_task(
            symbol, 
            "Financial Data Analyst", 
            "Latest financial reports (Revenue, Net Profit, Growth), PE/PB/PS ratios, Market Cap, Stock Price Performance (YTD/1Y), Dividend yield."
        )
        
        # 2. Industry Analyst
        industry_research = self._run_research_task(
            symbol,
            "Industry Researcher",
            "Industry market size & CAGR, Supply chain position (Upstream/Downstream), Major Competitors & Market Share, Recent Industry Trends/Policies."
        )

        # 3. Corporate Analyst
        corp_research = self._run_research_task(
            symbol,
            "Corporate Intelligence Specialist",
            "Recent company news (last 6 months), Product launches, Management changes, Strategic partnerships, Legal disputes or Risks."
        )

        # Combine Raw Search Data
        raw_search_content = f"""
=== RESEARCH AGENT 1: FINANCIAL DATA ===
{data_research}

=== RESEARCH AGENT 2: INDUSTRY ANALYSIS ===
{industry_research}

=== RESEARCH AGENT 3: CORPORATE INTELLIGENCE ===
{corp_research}
"""

        # --- Phase 2: Synthesis (Chief Editor) ---
        market_context = "China A-Share" if symbol.isdigit() else "US Stock"
        
        main_prompt = f"""
You are a Top Wall Street Investment Analyst (Chief Editor).
Your task is to write a comprehensive, professional investment research report for the {market_context} stock: {symbol}.

**IMPORTANT: The entire report content MUST be written in Simplified Chinese (简体中文).**

### Information Sources
I have dispatched 3 field researchers to gather the latest data. You must synthesize their findings along with our internal knowledge base.

#### 1. Fresh Field Research (Latest Internet Data):
{raw_search_content}

#### 2. Internal Knowledge Base (User Uploads):
{context_text[:150000]}

### Task
Write a cohesive, deep-dive report. Do not just copy-paste the research; analyze it. Connect the dots between financial data, industry trends, and internal docs.

### Report Structure (Markdown)
Please structure the report exactly as follows (Titles in Chinese):

# {symbol} 深度投资价值分析报告
**日期:** {os.environ.get('CURRENT_DATE', 'Today')}
**分析师:** AI Advisor ({model_name})

## 1. 核心观点 (Executive Summary)
- 评级：(买入/持有/卖出)
- 核心投资逻辑 (3-5点，使用列表)

## 2. 财务与估值分析 (Financial & Valuation Analysis)
- 综合数据分析师的发现
- 与历史表现或同业对比

## 3. 行业与竞争格局 (Industry & Competitive Landscape)
- 行业分析师的洞察
- {symbol} 的市场地位

## 4. 经营动态与风险 (Operational Updates & Risks)
- 公司新闻与内部资料结合
- 新产品、管理层变动及主要风险

## 5. 结论 (Conclusion)
- 最终结论与展望
"""

        # Main Agent Config (No search tool needed here, as we provided the search results in context)
        # Using Pro model for reasoning
        try:
            logger.info(f"Chief Editor generating final report using {model_name}...")
            response = self.client.models.generate_content(
                model=model_name,
                contents=main_prompt
            )
            final_report = response.text if response.text else "Error: Chief Editor produced no text."
            
            return final_report

        except Exception as e:
            logger.error(f"Chief Editor Failed: {e}")
            return f"Agent Error: {str(e)}"

    def generate_macro_strategy_report(self, category: str, context_text: str = "", model_name: str = "gemini-2.5-pro") -> str:
        """
        Generates a specialized report for Macro or Strategy analysis.
        Focuses on Short/Medium/Long term outlooks.
        category: 'MACRO' or 'STRATEGY'
        """
        if not self.api_key:
            return "Error: API Key missing."

        current_date = os.environ.get('CURRENT_DATE', 'Today')
        
        if category == "MACRO":
            role_title = "首席宏观经济顾问 (Chief Macro Economist)"
            report_title = "全球与中国宏观经济深度展望报告"
            core_task = "Analyze the current global and Chinese macroeconomic environment, focusing on policy, interest rates, GDP, and geopolitical risks."
        else: # STRATEGY
            role_title = "首席投资策略顾问 (Chief Investment Strategist)"
            report_title = "各大类资产配置与投资策略报告"
            core_task = "Formulate investment strategies, asset allocation advice, and risk management rules based on the current market environment."

        prompt = f"""
You are the {role_title}. 
Your task is to write a high-level, forward-looking strategic report: "{report_title}".

**Constraint:** The report MUST be written in **Simplified Chinese (简体中文)**.

### Input Data
1. **Internal Knowledge Base (Key Source):**
{context_text[:150000]}

2. **Your General Knowledge:**
Use your internal knowledge about current economic theories and historical market patterns.

### {core_task}

### Required Structure (Strictly Follow This)

# {report_title}
**日期:** {current_date}
**顾问:** AI Advisor ({model_name})

## 1. 核心观点 (Executive Summary)
- 当前市场定义的关键特征（牛/熊/震荡）。
- 最核心的3个结论。

## 2. 深度分析 (Deep Dive)
- (If Macro) Analyze: Growth (GDP), Inflation (CPI/PPI), Liquidity (Rates/Central Bank), and Policy.
- (If Strategy) Analyze: Valuations, Sentiment, Capital Flows, and Sector Rotation.

## 3. 趋势研判 (Time-Horizon Analysis) - **MOST IMPORTANT**
For this section, you MUST provide distinct judgments for three time horizons:

### 3.1 短期判断 (Short-term: 1-3 Months)
- Focus: Market sentiment, technical levels, immediate policy catalysts, liquidity shocks.
- Actionable advice: What to watch *now*.

### 3.2 中期判断 (Medium-term: 3-12 Months)
- Focus: Earnings cycles, economic recovery confirmation, fiscal policy impact.
- Actionable advice: Sector positioning (Overweight/Underweight).

### 3.3 长期判断 (Long-term: 1-3 Years)
- Focus: Structural changes (e.g., AI revolution, Demographics, Geopolitics), Debt cycles.
- Actionable advice: Strategic asset allocation (Strategic Beta).

## 4. 风险提示 (Key Risks)
- List the top 3 "Black Swan" or "Gray Rhino" risks.

---
**Instruction:** Be professional, objective, and decisive. Use the provided Knowledge Base as the primary source of truth if available.
"""

        try:
            logger.info(f"Generating {category} report using {model_name}...")
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text if response.text else f"Error: {role_title} produced no text."

        except Exception as e:
            logger.error(f"{category} Report Failed: {e}")
            return f"Agent Error: {str(e)}"
