import os
import json
import logging
import uuid
import shutil
from datetime import datetime
from pypdf import PdfReader
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.use_supabase = bool(self.supabase_url and self.supabase_key)
        
        self.base_path = "knowledge_base"
        self.local_meta_file = os.path.join(self.base_path, "documents.json")
        self.table_name = "knowledge_documents"  # Correct table name
        
        # Ensure directories
        os.makedirs(self.base_path, exist_ok=True)
        if not self.use_supabase:
            self._init_local_storage()

        if self.use_supabase:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("KnowledgeService: Connected to Supabase")
            except Exception as e:
                logger.error(f"KnowledgeService: Supabase init failed: {e}")
                self.use_supabase = False
                self._init_local_storage()

    def _init_local_storage(self):
        """Initialize local metadata JSON."""
        if not os.path.exists(self.local_meta_file):
            with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return ""

    def save_document(self, symbol: str, file_obj, filename: str, doc_type: str = "user_upload", user_id: str = None) -> dict:
        """
        Save uploaded file or generated report.
        1. Save file to disk (local cache).
        2. Save metadata to DB (Supabase) or local JSON.
        """
        symbol = symbol.upper()
        doc_id = str(uuid.uuid4())
        
        # Create symbol directory
        symbol_dir = os.path.join(self.base_path, symbol)
        os.makedirs(symbol_dir, exist_ok=True)
        
        # Determine paths
        # Use safe filename
        safe_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).strip()
        file_path = os.path.join(symbol_dir, f"{doc_id}_{safe_filename}")
        
        # Save file content locally (Supabase storage not configured in this version)
        try:
            file_obj.save(file_path)
        except AttributeError:
            # If file_obj is bytes or string (e.g. from report generator)
            with open(file_path, 'wb') as f:
                f.write(file_obj if isinstance(file_obj, bytes) else file_obj.encode('utf-8'))

        # Get file size
        file_size = os.path.getsize(file_path)

        # Base record (Internal/Local representation)
        record = {
            "id": doc_id,
            "user_id": user_id,
            "symbol": symbol,
            "filename": safe_filename,
            "file_path": file_path, # Local path, not in DB
            "type": doc_type,       # Mapped to file_type in DB
            "file_size": file_size,
            "created_at": datetime.utcnow().isoformat()
        }

        # Save Metadata
        if self.use_supabase:
            try:
                # Prepare record for Supabase (match schema)
                # Schema: id, user_id, symbol, filename, file_size, created_at, file_type
                db_record = {
                    "id": doc_id,
                    "user_id": user_id, # Required by RLS/Schema
                    "symbol": symbol,
                    "filename": safe_filename,
                    "file_size": file_size,
                    "created_at": record["created_at"],
                    "file_type": doc_type 
                }
                
                if not user_id or user_id == 'anonymous':
                     # If anonymous, this insert might fail depending on RLS, but we try anyway
                     # Or generate a dummy UUID if strict UUID check?
                     # For now pass it as is.
                     pass

                self.supabase.table(self.table_name).insert(db_record).execute()
            except Exception as e:
                logger.error(f"Supabase document insert failed: {e}")
                return {"error": str(e)}
        else:
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                docs.append(record)
                with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, indent=2)
            except Exception as e:
                logger.error(f"Local document save failed: {e}")
                return {"error": str(e)}

        return record

    def list_documents(self, symbol: str) -> list:
        """List documents for a specific symbol."""
        symbol = symbol.upper()
        if self.use_supabase:
            try:
                res = self.supabase.table(self.table_name).select("*").eq("symbol", symbol).order("created_at", desc=True).execute()
                return res.data
            except Exception as e:
                logger.error(f"Supabase list failed: {e}")
                return []
        else:
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                return [d for d in docs if d["symbol"] == symbol]
            except Exception as e:
                return []

    def get_document_metadata(self, doc_id: str) -> dict:
        """Retrieve document metadata by ID."""
        doc = None
        if self.use_supabase:
            try:
                res = self.supabase.table(self.table_name).select("*").eq("id", doc_id).single().execute()
                doc = res.data
            except Exception:
                return None
        else:
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                doc = next((d for d in docs if d["id"] == doc_id), None)
            except Exception:
                return None
        
        if doc:
             # Reconstruct file_path if missing (DB doesn't store it)
             if "file_path" not in doc:
                 symbol_dir = os.path.join(self.base_path, doc["symbol"])
                 # Note: In save_document we used f"{doc_id}_{safe_filename}"
                 # DB stores safe_filename in "filename" column
                 doc["file_path"] = os.path.join(symbol_dir, f"{doc['id']}_{doc['filename']}")
        
        return doc

    def get_document_content(self, doc_id: str) -> str:
        """Retrieve full text content of a document by ID."""
        doc = self.get_document_metadata(doc_id)
        
        if not doc:
            return ""

        file_path = doc.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return ""

        # Check extension
        if file_path.lower().endswith(".pdf"):
            return self.extract_text_from_pdf(file_path)
        else:
            # Text/Markdown files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return ""

    def delete_document(self, doc_id: str) -> bool:
        """Delete document metadata and file."""
        doc = self.get_document_metadata(doc_id)
        if not doc: return False

        # 2. Delete file
        if "file_path" in doc and os.path.exists(doc["file_path"]):
            try:
                os.remove(doc["file_path"])
            except Exception as e:
                logger.error(f"Failed to delete file: {e}")

        # 3. Delete Metadata
        if self.use_supabase:
            self.supabase.table(self.table_name).delete().eq("id", doc_id).execute()
        else:
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                docs = [d for d in docs if d["id"] != doc_id]
                with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, indent=2)
            except Exception:
                pass
        
        return True

    def get_documents_content(self, file_ids: list) -> str:
        """Combine content of multiple documents."""
        if not file_ids:
            return ""
            
        combined_text = ""
        for doc_id in file_ids:
            doc = self.get_document_metadata(doc_id)
            if not doc: continue
            
            filename = doc.get('filename', 'Unknown File')
            content = self.get_document_content(doc_id)
            
            if content:
                combined_text += f"\n\n--- Document: {filename} ---\n{content}\n"
        
        return combined_text