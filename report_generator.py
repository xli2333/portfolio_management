import os
import io
import logging
import markdown
from xhtml2pdf import pisa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Fonts directory
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

# CSS Stylesheet for "Top-Tier Research Report" look
# This mimics a professional financial report layout
REPORT_CSS = """
<style>
    @font-face {
        font-family: 'RegularFont';
        src: url('%(serif_font_path)s');
    }
    @font-face {
        font-family: 'BoldFont';
        src: url('%(sans_font_path)s');
    }
    
    @page {
        size: A4;
        margin: 2.5cm 2cm 2.5cm 2cm;
        @frame footer_frame {
            -pdf-frame-content: footerContent;
            bottom: 1cm;
            margin-left: 2cm;
            margin-right: 2cm;
            height: 1cm;
        }
    }

    body {
        font-family: 'RegularFont', sans-serif;
        font-size: 10.5pt;
        line-height: 1.6;
        color: #333333;
        word-break: break-all;
    }

    /* Headings - Serif (Unified Style) */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'RegularFont', sans-serif;
        color: #1a202c; /* Dark Slate */
        font-weight: bold;
        line-height: 1.3;
    }

    h1 {
        font-size: 24pt;
        border-bottom: 2px solid #2563eb; /* Blue underline */
        padding-bottom: 10px;
        margin-bottom: 20px;
        margin-top: 0;
    }

    h2 {
        font-size: 16pt;
        margin-top: 20px;
        margin-bottom: 10px;
        border-left: 5px solid #2563eb;
        padding-left: 10px;
        background-color: #f8fafc;
    }

    h3 {
        font-size: 13pt;
        margin-top: 15px;
        color: #475569;
    }

    /* Text Elements */
    p {
        margin-bottom: 10px;
        text-align: left;
    }

    strong {
        font-family: 'BoldFont', sans-serif;
        color: #000000;
    }

    /* Tables - Professional Data Grid */
    table {
        width: 100%%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 9pt;
    }
    
    th {
        background-color: #f1f5f9;
        color: #1e293b;
        font-family: 'BoldFont', sans-serif;
        font-weight: bold;
        border-bottom: 2px solid #cbd5e1;
        padding: 8px;
        text-align: left;
    }
    
    td {
        border-bottom: 1px solid #e2e8f0;
        padding: 8px;
        color: #334155;
    }
    
    /* Lists */
    ul, ol {
        margin-top: 5px;
        margin-bottom: 10px;
        padding-left: 20px;
    }
    li {
        margin-bottom: 5px;
    }

    /* Code Blocks / Quotes */
    pre, code {
        font-family: 'Courier New', monospace;
        background-color: #f3f4f6;
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 9pt;
    }
    
    blockquote {
        border-left: 4px solid #94a3b8;
        padding-left: 15px;
        margin-left: 0;
        color: #64748b;
        font-style: italic;
        background-color: #f8fafc;
        padding: 10px;
    }
    
    /* Footer */
    #footerContent {
        text-align: center;
        color: #94a3b8;
        font-size: 8pt;
    }
</style>
"""

def _get_font_paths():
    """
    Resolve font paths. 
    1. Regular/Serif: Look for 'serif.ttf', fallback to 'yahei.ttf'.
    2. Bold/Sans: Look for 'yahei_bold.ttf', fallback to 'yahei.ttf'.
    """
    yahei = os.path.join(FONTS_DIR, 'yahei.ttf')
    yahei_bold = os.path.join(FONTS_DIR, 'yahei_bold.ttf')
    serif = os.path.join(FONTS_DIR, 'serif.ttf')
    
    # Determine Regular Font (Body)
    if os.path.exists(serif):
        regular_font = serif
    elif os.path.exists(yahei):
        regular_font = yahei
    else:
        # Fallback to a system font name if file not found (may fail on Linux if not installed)
        regular_font = 'Helvetica'
        
    # Determine Bold Font (Headings)
    if os.path.exists(yahei_bold):
        bold_font = yahei_bold
    elif os.path.exists(yahei):
        bold_font = yahei
    else:
        bold_font = 'Helvetica-Bold'
        
    return regular_font, bold_font

def create_markdown_pdf(symbol, markdown_text) -> bytes:
    """
    Convert Markdown text to a professional PDF report using HTML+CSS.
    """
    # 1. Convert Markdown to HTML
    # 'tables': for table support
    # 'fenced_code': for ``` code blocks
    html_content = markdown.markdown(
        markdown_text, 
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    # 2. Prepare CSS with correct font paths
    reg_font_path, bold_font_path = _get_font_paths()
    
    # Escape paths for Windows CSS url() usage if necessary, though xhtml2pdf handles standard paths well.
    # On Windows, paths might need to be forward slashes for CSS url()
    reg_font_path = reg_font_path.replace('\\', '/')
    bold_font_path = bold_font_path.replace('\\', '/')
    
    css = REPORT_CSS % {
        'serif_font_path': reg_font_path, 
        'sans_font_path': bold_font_path
    }
    
    # 3. Build Full HTML Document
    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        {css}
    </head>
    <body>
        <div id="footerContent">
            AI Investment Research - Generated by DeepResearchAgent - {symbol}
            <pdf:pagenumber/>
        </div>
        
        <!-- Report Title Section -->
        <div style="text-align: center; margin-bottom: 40px;">
            <h1 style="border: none; font-size: 28pt; color: #1e3a8a;">{symbol} 深度投资价值分析报告</h1>
            <p style="color: #64748b; font-size: 12pt;">AI Deep Research Agent</p>
        </div>

        <!-- Main Content -->
        {html_content}
    </body>
    </html>
    """
    
    # 4. Convert HTML to PDF using xhtml2pdf
    buffer = io.BytesIO()
    
    # link_callback to allow loading local resources (fonts)
    # This is critical for Docker environments where pisa might not resolve relative paths or needs explicit permission
    def link_callback(uri, rel):
        # Allow loading from fonts directory. 
        # uri might be a file path or url, we just want to map it to our known fonts dir
        if 'fonts' in uri or uri.endswith('.ttf'):
             return os.path.join(FONTS_DIR, os.path.basename(uri))
        return uri

    pisa_status = pisa.CreatePDF(
        src=full_html,
        dest=buffer,
        encoding='utf-8',
        link_callback=link_callback
    )
    
    if pisa_status.err:
        logger.error(f"PDF Generation Error: {pisa_status.err}")
        return b""
        
    buffer.seek(0)
    return buffer.read()

def create_chat_pdf(symbol, messages) -> bytes:
    """
    Generate a formatted PDF from chat messages using the same HTML->PDF engine.
    """
    # 1. Convert Chat Messages to a clean HTML structure
    chat_html_body = ""
    
    for msg in messages:
        if ']: ' in msg:
            role_part, content = msg.split(']: ', 1)
            role = role_part.replace('[', '').strip().upper()
        else:
            role = 'UNKNOWN'
            content = msg
            
        # Convert Markdown in content (e.g. bolding in chat)
        content_html = markdown.markdown(content, extensions=['tables', 'nl2br'])
        
        if role == 'USER':
            bg_color = "#1e293b" # Dark blue/black
            text_color = "#ffffff"
            align = "right"
            role_display = "USER"
        else:
            bg_color = "#f1f5f9" # Light gray
            text_color = "#1e293b"
            align = "left"
            role_display = "AI ADVISOR"
            
        chat_html_body += f"""
        <div style="margin-bottom: 15px; text-align: {align};">
            <div style="display: inline-block; text-align: left; background-color: {bg_color}; color: {text_color}; padding: 10px 15px; border-radius: 8px; max-width: 80%;">
                <div style="font-size: 8pt; margin-bottom: 4px; font-weight: bold; opacity: 0.8;">{role_display}</div>
                <div style="font-size: 10pt;">{content_html}</div>
            </div>
        </div>
        """

    # 2. Prepare CSS (Reusing font logic)
    reg_font_path, bold_font_path = _get_font_paths()
    reg_font_path = reg_font_path.replace('\\', '/')
    bold_font_path = bold_font_path.replace('\\', '/')
    
    css = REPORT_CSS % {
        'serif_font_path': reg_font_path, 
        'sans_font_path': bold_font_path
    }
    
    # 3. Build Document
    full_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        {css}
    </head>
    <body>
        <div style="text-align: center; margin-bottom: 30px; border-bottom: 1px solid #e2e8f0; padding-bottom: 20px;">
            <h1 style="border: none; margin:0;">{symbol} - AI 对话记录</h1>
        </div>
        
        {chat_html_body}
    </body>
    </html>
    """
    
    # link_callback for fonts
    def link_callback(uri, rel):
        if 'fonts' in uri or uri.endswith('.ttf'):
             return os.path.join(FONTS_DIR, os.path.basename(uri))
        return uri
        
    pisa_status = pisa.CreatePDF(
        src=full_html, 
        dest=buffer, 
        encoding='utf-8',
        link_callback=link_callback
    )
    
    if pisa_status.err:
        logger.error(f"Chat PDF Error: {pisa_status.err}")
        return b""
        
    buffer.seek(0)
    return buffer.read()
