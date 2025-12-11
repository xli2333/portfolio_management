import os
import json
import logging
import base64
import csv  # Standard library import
# import requests # No longer needed
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai # Legacy SDK
from google import genai as client_genai # New SDK
from google.genai import types

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from knowledge_service import KnowledgeService

class PortfolioService:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.local_file = "portfolio.json"
        self.summary_file = "company_summaries.json"
        self.use_supabase = bool(self.supabase_url and self.supabase_key)
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        
        # Configure globally if key exists
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_client = genai.GenerativeModel("gemini-2.5-pro") # Default instance
                self.new_client = client_genai.Client(api_key=self.gemini_key) # New SDK Client
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.gemini_client = None
                self.new_client = None
        else:
            self.gemini_client = None
            self.new_client = None
            
        if self.use_supabase:
            logger.info("Initializing PortfolioService with Supabase")
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.use_supabase = False
        
        if not self.use_supabase:
            logger.info("Initializing PortfolioService with Local File Storage")
            self._init_local_storage()
            self._init_summary_storage()
        
        # Load A Share Name Mapping
        self.a_share_map = {}
        try:
            self._load_a_share_names()
        except Exception as e:
            # CRITICAL: Do not let name loading crash the entire application
            # Log error but continue boot
            print(f"[Critical Warning] Failed to load share names: {e}")
            logger.error(f"Failed to load share names: {e}")

    def _load_a_share_names(self):
        """Load A-share name mapping. Priority: Supabase -> Local CSV."""
        loaded_count = 0
        
        # 1. Priority: Try Supabase
        if self.use_supabase:
            print("[Info] Loading A-Share names from Supabase (Priority)...")
            try:
                loaded_count = self._load_from_supabase_metadata()
                if loaded_count > 0:
                    print(f"[Success] Loaded {loaded_count} names from Supabase. Skipping CSV.")
                    return
            except Exception as e:
                print(f"[Warn] Supabase load failed: {e}")

        # 2. Fallback: Try CSV
        print("[Info] Supabase yielded no names or failed. Trying Local CSV fallback...")
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(base_dir, "A share names.csv")
            
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        if reader.fieldnames:
                            reader.fieldnames = [name.strip() for name in reader.fieldnames]
                            
                        for row in reader:
                            raw_code = row.get('证券代码')
                            name = row.get('证券名称')
                            if raw_code and name:
                                code = raw_code.strip().split('.')[0]
                                self.a_share_map[code] = name.strip()
                                loaded_count += 1
                except Exception as csv_e:
                    print(f"[Warn] CSV load failed: {csv_e}")
                    # Fallback to GBK
                    try:
                        with open(csv_path, mode='r', encoding='gbk') as f:
                            reader = csv.DictReader(f)
                            if reader.fieldnames:
                                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                            for row in reader:
                                raw_code = row.get('证券代码')
                                name = row.get('证券名称')
                                if raw_code and name:
                                    code = raw_code.strip().split('.')[0]
                                    self.a_share_map[code] = name.strip()
                                    loaded_count += 1
                    except Exception as gbk_e:
                        print(f"[Warn] CSV GBK load failed: {gbk_e}")
            else:
                 print(f"[Warn] CSV file not found at: {csv_path}")

        except Exception as e:
            print(f"[Warn] File system error during CSV load: {e}")
            
        print(f"[Info] Final A-Share map size: {len(self.a_share_map)}")

    def _load_from_supabase_metadata(self) -> int:
        """Fetch stock metadata from Supabase table with pagination. Returns count loaded."""
        count = 0
        offset = 0
        batch_size = 1000
        
        print("[Info] Starting Supabase metadata fetch...")
        try:
            while True:
                # Range is inclusive start, inclusive end
                response = self.supabase.table("stock_metadata").select("symbol,name").range(offset, offset + batch_size - 1).execute()
                data = response.data
                
                if not data:
                    break
                
                batch_count = 0
                for row in data:
                    s = row.get('symbol')
                    n = row.get('name')
                    if s and n:
                        self.a_share_map[s] = n
                        batch_count += 1
                
                count += batch_count
                offset += batch_size
                
                # If we got less than batch_size, we are done
                if len(data) < batch_size:
                    break
                    
            print(f"[Success] Fully loaded {count} names from Supabase.")
        except Exception as e:
            print(f"[Error] Failed to load from Supabase: {e}")
            # Do not re-raise, let fallback handle it
            
        return count


    def _init_local_storage(self):
        """Initialize local JSON file if it doesn't exist."""
        if not os.path.exists(self.local_file):
            with open(self.local_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _init_summary_storage(self):
        """Initialize local summary cache."""
        if not os.path.exists(self.summary_file):
            with open(self.summary_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def get_portfolio(self, user_id):
        """Retrieve all holdings for a specific user."""
        if self.use_supabase:
            try:
                response = self.supabase.table("holdings").select("*").eq("user_id", user_id).execute()
                return response.data
            except Exception as e:
                logger.error(f"Supabase read error: {e}")
                return []
        else:
            try:
                with open(self.local_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Local file read error: {e}")
                return []

    def add_stock(self, user_id, symbol, quantity, cost_basis):
        """Add a stock to the portfolio for a specific user."""
        symbol = symbol.upper()
        # Support fractional shares by using float()
        try:
            # Supabase shares column is bigint (int8), so we must send int, not float (e.g. 100.0 fails)
            safe_shares = int(float(quantity))
        except ValueError:
            safe_shares = 0
            
        record = {
            "user_id": user_id,
            "symbol": symbol,
            "shares": safe_shares,
            "cost_basis": float(cost_basis),
            "updated_at": datetime.utcnow().isoformat()
        }

        if self.use_supabase:
            try:
                # Use upsert with on_conflict parameter to update on duplicate (user_id, symbol)
                self.supabase.table("holdings").upsert(
                    record,
                    on_conflict="user_id,symbol"
                ).execute()
                return {"status": "success", "msg": "Added/Updated in Supabase"}
            except Exception as e:
                logger.error(f"Supabase write error: {e}")
                return {"status": "error", "msg": str(e)}
        else:
            try:
                data = self.get_portfolio(user_id) # Local mode ignores user_id effectively
                # Check if symbol exists, if so, maybe update?
                existing = next((item for item in data if item["symbol"] == symbol), None)
                if existing:
                    existing["shares"] = safe_shares
                    existing["cost_basis"] = float(cost_basis)
                    existing["updated_at"] = datetime.utcnow().isoformat()
                else:
                    data.append(record)
                
                with open(self.local_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return {"status": "success", "msg": "Saved locally"}
            except Exception as e:
                logger.error(f"Local file write error: {e}")
                return {"status": "error", "msg": str(e)}

    def update_stock(self, user_id, symbol, quantity, cost_basis):
        """Update an existing stock in the portfolio."""
        return self.add_stock(user_id, symbol, quantity, cost_basis)

    def remove_stock(self, user_id, symbol):
        """Remove a stock from the portfolio."""
        symbol = symbol.upper()
        if self.use_supabase:
            try:
                self.supabase.table("holdings").delete().eq("user_id", user_id).eq("symbol", symbol).execute()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "msg": str(e)}
        else:
            try:
                data = self.get_portfolio(user_id)
                data = [d for d in data if d["symbol"] != symbol]
                with open(self.local_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "msg": str(e)}

    def get_company_summary(self, symbol):
        """Get one-sentence company summary, using cache or Gemini AI."""
        if not symbol: return ""
        
        # 1. Try Cache
        cache = {}
        try:
            if os.path.exists(self.summary_file):
                with open(self.summary_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
        except Exception as e:
            logger.error(f"Summary cache read error: {e}")

        if symbol in cache:
            cached_summary = cache[symbol]
            # [Validation] If we have a mapped name, ensure the summary is high quality
            # If mapped name exists but summary doesn't contain it (likely old/generic summary), force refresh.
            # Also refresh if it looks like an error.
            should_refresh = False
            
            if cached_summary.startswith("AI Generation Error") or cached_summary.startswith("Network Error"):
                should_refresh = True
            elif symbol.isdigit() and symbol in self.a_share_map:
                mapped_name = self.a_share_map[symbol]
                # Simple heuristic: if the Chinese name isn't in the summary, it might be an old summary
                # (unless summary is very short).
                # But to be safe, let's just trust the cache unless it's an error, 
                # OR if the user specifically requests a refresh (not implemented yet).
                # actually, let's just force refresh if it's "API Key Missing" or similar
                if "API Key Missing" in cached_summary:
                    should_refresh = True
            
            if not should_refresh:
                return cached_summary

        # 2. Fetch from Gemini
        summary = self._fetch_gemini_summary(symbol)
        
        # 3. Save to Cache
        if summary and not summary.startswith("API Error") and summary != "Network Error" and summary != "AI Generation Error":
            cache[symbol] = summary
            try:
                with open(self.summary_file, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Summary cache write error: {e}")
        
        return summary

    def _fetch_gemini_summary(self, symbol):
        """Call Gemini API for summary."""
        if not self.gemini_client:
            return "API Key Missing or Client Not Initialized"

        try:
            # For A-Shares, fetch company name for better AI context
            prompt_symbol = symbol
            # [Optimization] Disable name fetching for now to prevent system freeze due to proxy issues
            # if symbol.isdigit():
            #     try:
            #         from data_fetcher import DataFetcher
            #         fetcher = DataFetcher()
            #         info = fetcher.get_stock_info(symbol)
            #         if info and info.get('name') and info['name'] != symbol:
            #             prompt_symbol = f"{symbol} (公司名: {info['name']})"
            #     except Exception as e:
            #         logger.warning(f"Failed to fetch company name for {symbol}: {e}")
            
            # Use specific context for A-Shares
            if symbol.isdigit():
                # Try to get name from CSV map
                company_name = self.a_share_map.get(symbol)
                if company_name:
                    prompt_text = f"请用一句话简明扼要地总结 A股上市公司“{company_name}” ({symbol}) 的主要业务和行业地位（不要废话，直接说重点）。"
                else:
                    prompt_text = f"请用一句话简明扼要地总结 A股代码为 {symbol} 的公司的主要业务和行业地位（不要废话，直接说重点）。"
            else:
                prompt_text = f"请用一句话简明扼要地总结股票代码为 {symbol} 的公司的主要业务和行业地位（不要废话，直接说重点）。"

            # Use the configured Gemini client
            response = self.gemini_client.generate_content(
                prompt_text,
                safety_settings=[
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return "AI Generation Error: No text in response"
                
        except Exception as e:
            logger.error(f"Gemini Fetch Exception: {e}")
            return f"Network Error: {str(e)}"

    def chat_with_gemini(self, symbol, message, history=[], selected_file_ids=[], model_name="gemini-2.5-flash", image_data=None):
        """Interactive chat about a specific stock with knowledge base support."""
        if not self.gemini_key:
            return "API Key Missing or Client Not Initialized"

        try:
            # Context preparation
            stock_context = symbol
            if symbol.isdigit() and symbol in self.a_share_map:
                stock_context = f"{self.a_share_map[symbol]} ({symbol})"

            market_context = "China A-Share" if symbol.isdigit() else "US Stock"

            # Knowledge Base Context
            knowledge_context = ""
            if selected_file_ids:
                try:
                    ks = KnowledgeService()
                    docs_text = ks.get_documents_content(selected_file_ids)
                    if docs_text:
                        knowledge_context = f"\n\n[USER UPLOADED KNOWLEDGE BASE]\n{docs_text}\n[END KNOWLEDGE BASE]\n"
                except Exception as e:
                    logger.error(f"Knowledge injection failed: {e}")

            # System prompt to set behavior
            if symbol == "MACRO":
                system_instruction = (
                    "You are the Chief Macro Economic Advisor (首席宏观经济顾问). "
                    "Your goal is to analyze the Global and Chinese economic environment (Policy, GDP, Interest Rates, Geopolitics). "
                    "Do NOT discuss individual stock technicals unless they reflect a broad trend. "
                    "When giving judgments, TRY to categorize them into: Short-term (1-3mo), Medium-term (3-12mo), and Long-term (1-3yr)."
                )
            elif symbol == "STRATEGY":
                system_instruction = (
                    "You are the Chief Investment Strategist (首席投资策略顾问). "
                    "Your goal is to provide advice on Asset Allocation, Sector Rotation, and Risk Management. "
                    "Focus on *how* to invest (position sizing, timing, hedging) rather than just *what* to buy. "
                    "When giving judgments, TRY to categorize them into: Short-term (1-3mo), Medium-term (3-12mo), and Long-term (1-3yr)."
                )
            else:
                system_instruction = f"You are a financial analysis assistant. You are discussing the {market_context} {stock_context}. Answer questions specifically about this company, its financials, news, or technicals. Keep answers concise and professional."
            
            # --- IMAGE HANDLING (NEW SDK) ---
            if image_data:
                if not self.new_client:
                    return "New Gemini Client initialization failed."
                
                try:
                    # Decode Base64 Image
                    # Remove header if present (e.g. "data:image/png;base64,...")
                    if "," in image_data:
                        image_data = image_data.split(",")[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    
                    # Construct Content with Image
                    # We treat this as a stateless call with history included in contents if possible,
                    # or just a single-turn analysis if history is complex to map.
                    # For simplicity and robustness with images, we'll do a generate_content call
                    # with [System, History..., Current Message + Image]
                    
                    contents = []
                    
                    # Add System Instruction as first content? Or config?
                    # New SDK supports system_instruction in config.
                    
                    # Convert History
                    for msg in history:
                        role = msg.get('role', 'user')
                        text_parts = msg.get('parts', [])
                        if isinstance(text_parts, list):
                            text = " ".join(text_parts)
                        else:
                            text = str(text_parts)
                        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
                    
                    # Add Current Message + Image
                    current_parts = []
                    if knowledge_context:
                        current_parts.append(types.Part.from_text(text=knowledge_context))
                    
                    if message:
                        current_parts.append(types.Part.from_text(text=message))
                    
                    current_parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
                    
                    contents.append(types.Content(role='user', parts=current_parts))
                    
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7
                    )

                    response = self.new_client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config
                    )
                    
                    return response.text if response.text else "AI analyzed the image but returned no text."

                except Exception as img_e:
                    logger.error(f"Image Analysis Failed: {img_e}")
                    return f"Image Analysis Error: {str(img_e)}"

            # --- TEXT ONLY HANDLING (LEGACY SDK) ---
            # Initialize specified model
            client = genai.GenerativeModel(model_name)
            
            # Start chat session
            chat = client.start_chat(history=history)
            
            # Construct full message
            if not history:
                full_message = f"{system_instruction}{knowledge_context}\n\nUser Question: {message}"
            else:
                full_message = f"{knowledge_context}\n{message}" if knowledge_context else message

            response = chat.send_message(
                full_message,
                safety_settings=[
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return "AI No Response"

        except Exception as e:
            logger.error(f"Gemini Chat Exception: {e}")
            return f"Error: {str(e)}"

