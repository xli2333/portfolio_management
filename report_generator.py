from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
import os
import io
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Font Configuration ---
CHINESE_FONT_NAME = 'ChineseFont'
DEFAULT_FONT = 'Helvetica'
FONT_LOADED = False

def ensure_chinese_font():
    """
    Attempt to load a Chinese font. 
    1. Check local 'fonts/' directory.
    2. Check system paths (Windows/Linux).
    3. (Optional) Download if missing - skipped for safety/speed in this env.
    """
    global FONT_LOADED, CHINESE_FONT_NAME
    
    if FONT_LOADED:
        return

    # List of potential font paths
    font_candidates = [
        'fonts/yahei.ttf',
        'fonts/yahei_bold.ttf',
        'fonts/SimHei.ttf',
        'fonts/msyh.ttf',
        'fonts/NotoSansSC-Regular.ttf',
        'fonts/wqy-microhei.ttc',
        # Windows
        r'C:\Windows\Fonts\simhei.ttf',
        r'C:\Windows\Fonts\msyh.ttf',
        # Linux / Docker (Standard locations)
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
    ]

    font_path = None
    for path in font_candidates:
        if os.path.exists(path):
            font_path = path
            break
            
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(CHINESE_FONT_NAME, font_path))
            FONT_LOADED = True
            logger.info(f"Loaded Chinese font from: {font_path}")
        except Exception as e:
            logger.error(f"Failed to load font {font_path}: {e}")
    else:
        logger.warning("No Chinese font found. PDF Chinese characters may not render.")

# Initialize font on load
ensure_chinese_font()

def get_font_name():
    return CHINESE_FONT_NAME if FONT_LOADED else DEFAULT_FONT

# --- PDF Generation Functions ---

def create_chat_pdf(symbol, messages) -> bytes:
    """
    Generate a formatted PDF from chat messages using Platypus for robust wrapping.
    messages: list of strings (formatted as "[ROLE]: Text")
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, 
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    font_name = get_font_name()
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle(
        name='ChatTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        spaceAfter=20,
        alignment=1 # Center
    )
    
    style_user = ParagraphStyle(
        name='UserMessage',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=HexColor('#FFFFFF'),
        backColor=HexColor('#000000'),
        borderPadding=10,
        spaceBefore=10,
        spaceAfter=10,
        borderRadius=5
    )
    
    style_model = ParagraphStyle(
        name='ModelMessage',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=16,
        textColor=HexColor('#1f2937'),
        backColor=HexColor('#f3f4f6'),
        borderPadding=10,
        spaceBefore=10,
        spaceAfter=10,
        borderRadius=5
    )
    
    story = []
    
    # Header
    story.append(Paragraph(f"{symbol} - AI 对话记录", style_title))
    story.append(Spacer(1, 0.5*cm))
    
    # Messages
    for msg in messages:
        # msg format expectation: "[ROLE]: Text"
        # We need to parse it slightly to separate role and text for styling
        if ']: ' in msg:
            role_part, content = msg.split(']: ', 1)
            role = role_part.replace('[', '').strip().upper()
        else:
            role = 'UNKNOWN'
            content = msg

        # Escape HTML chars for ReportLab (it supports basic tags like <b>, <br>)
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        content = content.replace('\n', '<br/>')
        
        if role == 'USER':
            p = Paragraph(f"<b>USER:</b><br/>{content}", style_user)
        else:
            # Model
            p = Paragraph(f"<b>AI ANALYST:</b><br/>{content}", style_model)
            
        story.append(p)

    try:
        doc.build(story)
    except Exception as e:
        logger.error(f"PDF Build Failed: {e}")
        # Fallback to simple canvas if Platypus fails completely
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100, 700, f"Error generating PDF: {str(e)}")
        c.save()
        
    buffer.seek(0)
    return buffer.read()


def create_markdown_pdf(symbol, markdown_text) -> bytes:
    """
    Generate a formatted PDF from Markdown text.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=2*cm, leftMargin=2*cm, 
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    font_name = get_font_name()
    styles = getSampleStyleSheet()
    
    # Create Custom Styles with Chinese Font
    styles.add(ParagraphStyle(name='ChineseNormal', parent=styles['Normal'], fontName=font_name, fontSize=10, leading=16, spaceAfter=6))
    styles.add(ParagraphStyle(name='ChineseHeading1', parent=styles['Heading1'], fontName=font_name, fontSize=18, leading=22, spaceAfter=12, textColor=HexColor('#0f172a')))
    styles.add(ParagraphStyle(name='ChineseHeading2', parent=styles['Heading2'], fontName=font_name, fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, textColor=HexColor('#334155')))
    
    story = []
    
    # Title
    story.append(Paragraph(f"{symbol} - 深度研究报告", styles['ChineseHeading1']))
    story.append(Spacer(1, 0.5*cm))
    
    # Simple Markdown Parser
    lines = markdown_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue
            
        try:
            # Clean Markdown formatting for cleaner PDF text
            clean_line = line.replace('**', '') # Remove bold markers for simplicity
            clean_line = clean_line.replace('__', '')
            clean_line = clean_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if line.startswith('# '):
                story.append(Paragraph(clean_line[2:], styles['ChineseHeading1']))
            elif line.startswith('## '):
                story.append(Paragraph(clean_line[3:], styles['ChineseHeading2']))
            elif line.startswith('### '):
                story.append(Paragraph(f"<b>{clean_line[4:]}</b>", styles['ChineseNormal']))
            elif line.startswith('- ') or line.startswith('* '):
                story.append(Paragraph(f"• {clean_line[2:]}", styles['ChineseNormal']))
            else:
                story.append(Paragraph(clean_line, styles['ChineseNormal']))
        except Exception as e:
            logger.error(f"PDF Gen Error on line: {line} -> {e}")
            
    try:
        doc.build(story)
    except Exception as e:
        logger.error(f"PDF Build Failed: {e}")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100, 700, "PDF Generation Failed. Please check logs.")
        c.save()

    buffer.seek(0)
    return buffer.read()

def _generate_chart_png(analyzer, png_path: str):
    """
    Internal helper to generate chart PNG (imported only when needed to avoid heavy deps)
    """
    try:
        import mplfinance as mpf
        import pandas as pd
        
        # ... logic ...
        # (This function was in web_app.py in the previous context, 
        # but report_generator.py usually focuses on PDF. 
        # If web_app.py calls this, it's fine. 
        # Keeping this file focused on PDF generation logic.)
        pass 
    except ImportError:
        pass