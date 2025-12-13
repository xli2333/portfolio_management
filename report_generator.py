import os
import io
import logging
import time
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

# Standard CSS for WeasyPrint
# Note: WeasyPrint handles @page and standard CSS3 remarkably well.
REPORT_CSS = """
@font-face {
    font-family: 'SerifFont';
    src: url('file://%(serif_font_path)s');
}

@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;
    @bottom-center {
        content: "Page " counter(page);
        font-family: 'SerifFont', serif;
        font-size: 9pt;
        color: #64748b;
    }
}

body {
    font-family: 'SerifFont', serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #333333;
    /* Crucial for text wrapping */
    word-wrap: break-word; 
    overflow-wrap: break-word;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: 'SerifFont', serif;
    color: #1a202c;
    font-weight: bold;
    line-height: 1.3;
}

h1 {
    font-size: 24pt;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

h2 {
    font-size: 16pt;
    margin-top: 20px;
    border-left: 5px solid #2563eb;
    padding-left: 10px;
    background-color: #f8fafc;
}

/* Links & Images - Prevent overflow */
a {
    color: #2563eb;
    word-break: break-all;
}

img {
    max-width: 100%;
    height: auto;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 9pt;
    /* WeasyPrint handles table layout much better than xhtml2pdf */
    table-layout: fixed; 
}

th, td {
    border: 1px solid #e2e8f0;
    padding: 8px;
    vertical-align: top;
    word-wrap: break-word; /* Ensure cell content wraps */
    overflow-wrap: break-word;
}

th {
    background-color: #f1f5f9;
    font-weight: bold;
    text-align: left;
}

pre, code {
    font-family: 'Courier New', monospace;
    background-color: #f3f4f6;
    padding: 2px 4px;
    border-radius: 4px;
    font-size: 9pt;
    white-space: pre-wrap; /* Wrap long code lines */
    word-break: break-all;
}

blockquote {
    border-left: 4px solid #94a3b8;
    padding-left: 15px;
    color: #64748b;
    font-style: italic;
    background-color: #f8fafc;
    padding: 10px;
}
"""

def _get_font_path():
    """
    Resolve the absolute path to the Serif font.
    Prioritizes 'serif.ttf', falls back to 'yahei.ttf', then system fallback.
    """
    serif = os.path.join(FONTS_DIR, 'serif.ttf')
    yahei = os.path.join(FONTS_DIR, 'yahei.ttf')
    
    selected_font = None
    
    if os.path.exists(serif):
        selected_font = serif
        logger.info(f"[Font] Found serif.ttf at: {serif}")
    elif os.path.exists(yahei):
        selected_font = yahei
        logger.info(f"[Font] serif.ttf not found. Fallback to yahei.ttf at: {yahei}")
    else:
        logger.warning("[Font] No local fonts found in fonts/ directory.")
        return None

    # WeasyPrint expects forward slashes even on Windows for file:// URLs
    return selected_font.replace('\\', '/')

def create_markdown_pdf(symbol, markdown_text) -> bytes:
    """
    Generate PDF using WeasyPrint (The Gold Standard for Python HTML->PDF).
    """
    t_start = time.time()
    try:
        # 1. Font Configuration
        font_path = _get_font_path()
        css_str = ""
        
        if font_path:
            # Inject font path into CSS
            css_str = REPORT_CSS % {'serif_font_path': font_path}
        else:
            # Fallback CSS without custom font face
            logger.warning("[PDF] Generating without custom font.")
            css_str = REPORT_CSS.replace("src: url('file://%(serif_font_path)s');", "")

        # 2. Convert Markdown to HTML
        html_body = markdown.markdown(
            markdown_text, 
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # 3. Build Complete HTML
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{symbol} Report</title>
        </head>
        <body>
            <div style="text-align: center; margin-bottom: 40px;">
                <h1>{symbol} 深度投资价值分析报告</h1>
                <p style="color: #64748b; font-size: 12pt;">AI Deep Research Agent</p>
            </div>
            {html_body}
        </body>
        </html>
        """
        
        logger.info(f"[PDF] HTML generated ({len(full_html)} chars). Starting WeasyPrint rendering...")

        # 4. Render PDF
        font_config = FontConfiguration()
        pdf_bytes = HTML(string=full_html, base_url=os.path.dirname(__file__)).write_pdf(
            stylesheets=[CSS(string=css_str, font_config=font_config)],
            font_config=font_config
        )
        
        t_end = time.time()
        logger.info(f"[PDF] Success! Generated {len(pdf_bytes)} bytes in {t_end - t_start:.2f}s")
        return pdf_bytes

    except Exception as e:
        logger.error(f"[PDF] CRITICAL ERROR: {str(e)}", exc_info=True)
        # Return empty bytes to signal failure (handled by web_app.py)
        return b""

def create_chat_pdf(symbol, messages) -> bytes:
    """
    Generate Chat PDF using WeasyPrint.
    """
    try:
        # Re-use font logic
        font_path = _get_font_path()
        css_str = ""
        if font_path:
            css_str = REPORT_CSS % {'serif_font_path': font_path}
        else:
            css_str = REPORT_CSS.replace("src: url('file://%(serif_font_path)s');", "")

        chat_html_body = ""
        for msg in messages:
            if ']: ' in msg:
                role_part, content = msg.split(']: ', 1)
                role = role_part.replace('[', '').strip().upper()
            else:
                role = 'UNKNOWN'
                content = msg
            
            content_html = markdown.markdown(content, extensions=['tables', 'nl2br'])
            
            if role == 'USER':
                wrapper_style = "text-align: right; margin-bottom: 15px;"
                bubble_style = "display: inline-block; text-align: left; background-color: #1e293b; color: #ffffff; padding: 10px 15px; border-radius: 8px; max-width: 80%;"
            else:
                wrapper_style = "text-align: left; margin-bottom: 15px;"
                bubble_style = "display: inline-block; text-align: left; background-color: #f1f5f9; color: #1e293b; padding: 10px 15px; border-radius: 8px; max-width: 80%; border: 1px solid #e2e8f0;"

            chat_html_body += f"""
            <div style="{wrapper_style}">
                <div style="{bubble_style}">
                    <div style="font-size: 8pt; font-weight: bold; opacity: 0.8; margin-bottom: 4px;">{role}</div>
                    <div style="font-size: 10pt;">{content_html}</div>
                </div>
            </div>
            """

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
            <div style="text-align: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px;">
                <h1>{symbol} - AI 对话记录</h1>
            </div>
            {chat_html_body}
        </body>
        </html>
        """

        font_config = FontConfiguration()
        return HTML(string=full_html).write_pdf(
            stylesheets=[CSS(string=css_str, font_config=font_config)],
            font_config=font_config
        )

    except Exception as e:
        logger.error(f"[Chat PDF] Error: {e}", exc_info=True)
        return b""