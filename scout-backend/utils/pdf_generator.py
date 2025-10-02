"""
Enhanced PDF generator for markdown reports with professional formatting.
"""
import os
import io
import re
from typing import Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, darkblue, darkgreen
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import markdown
from markdown.extensions import codehilite, tables, toc
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class EnhancedPDFGenerator:
    """Professional PDF generator for markdown reports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for professional formatting."""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1a365d'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading 1 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#2d3748'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#e2e8f0'),
            borderPadding=5
        ))
        
        # Heading 2 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=HexColor('#4a5568'),
            fontName='Helvetica-Bold'
        ))
        
        # Heading 3 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=HexColor('#718096'),
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Code style
        self.styles.add(ParagraphStyle(
            name='CustomCode',
            parent=self.styles['Code'],
            fontSize=9,
            fontName='Courier',
            textColor=HexColor('#2d3748'),
            backColor=HexColor('#f7fafc'),
            borderWidth=1,
            borderColor=HexColor('#e2e8f0'),
            borderPadding=8,
            spaceAfter=10
        ))
        
        # Quote style
        self.styles.add(ParagraphStyle(
            name='CustomQuote',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Oblique',
            textColor=HexColor('#4a5568'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10,
            borderWidth=0,
            borderColor=HexColor('#cbd5e0'),
            borderPadding=10,
            backColor=HexColor('#f7fafc')
        ))
    
    def markdown_to_pdf(self, markdown_content: str, output_path: str, title: str = None) -> bytes:
        """Convert markdown content to a professionally formatted PDF."""
        
        # Convert markdown to HTML with extensions
        md = markdown.Markdown(extensions=[
            'tables',
            'codehilite',
            'toc',
            'fenced_code',
            'nl2br'
        ])
        
        html_content = md.convert(markdown_content)
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create PDF document
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build story (content elements)
        story = []
        
        # Add title if provided
        if title:
            story.append(Paragraph(title, self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
        
        # Process HTML elements
        self._process_html_elements(soup, story)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Save to file if output_path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def _process_html_elements(self, soup, story):
        """Process HTML elements and convert to PDF elements."""
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'table', 'blockquote', 'pre', 'code']):
            
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                self._add_heading(element, story)
            
            elif element.name == 'p':
                self._add_paragraph(element, story)
            
            elif element.name in ['ul', 'ol']:
                self._add_list(element, story)
            
            elif element.name == 'table':
                self._add_table(element, story)
            
            elif element.name == 'blockquote':
                self._add_quote(element, story)
            
            elif element.name in ['pre', 'code']:
                self._add_code(element, story)
    
    def _add_heading(self, element, story):
        """Add heading to story."""
        text = element.get_text().strip()
        if not text:
            return
            
        level = int(element.name[1])  # Extract number from h1, h2, etc.
        
        if level == 1:
            style = self.styles['CustomHeading1']
        elif level == 2:
            style = self.styles['CustomHeading2']
        else:
            style = self.styles['CustomHeading3']
        
        story.append(Paragraph(text, style))
    
    def _add_paragraph(self, element, story):
        """Add paragraph to story."""
        text = element.get_text().strip()
        if not text:
            return
        
        # Handle bold and italic formatting
        html_text = str(element)
        html_text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', html_text)
        html_text = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', html_text)
        html_text = re.sub(r'<p[^>]*>', '', html_text)
        html_text = re.sub(r'</p>', '', html_text)
        
        story.append(Paragraph(html_text, self.styles['CustomBody']))
    
    def _add_list(self, element, story):
        """Add list to story."""
        items = element.find_all('li')
        for i, item in enumerate(items):
            text = item.get_text().strip()
            if text:
                if element.name == 'ul':
                    bullet_text = f"• {text}"
                else:
                    bullet_text = f"{i+1}. {text}"
                
                story.append(Paragraph(bullet_text, self.styles['CustomBody']))
        
        story.append(Spacer(1, 10))
    
    def _add_table(self, element, story):
        """Add table to story."""
        rows = []
        
        # Process table rows
        for tr in element.find_all('tr'):
            row = []
            for td in tr.find_all(['td', 'th']):
                cell_text = td.get_text().strip()
                row.append(cell_text)
            if row:
                rows.append(row)
        
        if rows:
            # Create table
            table = Table(rows)
            
            # Style the table
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f7fafc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#2d3748')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ffffff')),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#4a5568')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ])
            
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 15))
    
    def _add_quote(self, element, story):
        """Add blockquote to story."""
        text = element.get_text().strip()
        if text:
            story.append(Paragraph(f'"{text}"', self.styles['CustomQuote']))
    
    def _add_code(self, element, story):
        """Add code block to story."""
        text = element.get_text().strip()
        if text:
            # Handle multi-line code
            lines = text.split('\n')
            for line in lines:
                story.append(Paragraph(line if line.strip() else ' ', self.styles['CustomCode']))
            story.append(Spacer(1, 10))


def generate_enhanced_pdf(markdown_content: str, title: str = None) -> bytes:
    """
    Generate an enhanced PDF from markdown content.
    
    Args:
        markdown_content: The markdown content to convert
        title: Optional title for the document
    
    Returns:
        PDF content as bytes
    """
    generator = EnhancedPDFGenerator()
    return generator.markdown_to_pdf(markdown_content, None, title)


def generate_report_specific_pdf(markdown_content: str, report_type: str) -> bytes:
    """
    Generate PDF with report-type specific styling.
    
    Args:
        markdown_content: The markdown content to convert
        report_type: Type of report (competition, price, synthesis, etc.)
    
    Returns:
        PDF content as bytes
    """
    # Map report types to titles and styling
    report_configs = {
        'competition_report': {
            'title': 'Competitive Analysis Report',
            'color_scheme': '#1a365d'  # Dark blue
        },
        'price_report': {
            'title': 'Pricing Strategy Report', 
            'color_scheme': '#2d5016'  # Dark green
        },
        'final_report': {
            'title': 'Comprehensive Business Analysis',
            'color_scheme': '#742a2a'  # Dark red
        },
        'market_report': {
            'title': 'Market Analysis Report',
            'color_scheme': '#553c9a'  # Purple
        }
    }
    
    # Extract report type from filename
    clean_type = report_type.replace('.md', '').replace('_', ' ')
    config = report_configs.get(report_type.replace('.md', ''), {
        'title': clean_type.title(),
        'color_scheme': '#1a365d'
    })
    
    generator = EnhancedPDFGenerator()
    return generator.markdown_to_pdf(markdown_content, None, config['title'])


def add_report_metadata(content: str, report_type: str) -> str:
    """
    Add metadata footer to reports.
    
    Args:
        content: Original markdown content
        report_type: Type of report
    
    Returns:
        Enhanced markdown content with metadata
    """
    from datetime import datetime
    
    metadata = f"""

---

**Report Information**
- Report Type: {report_type.replace('_', ' ').title()}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- System: Scout Business Intelligence Platform

*This report was automatically generated using AI-powered analysis tools.*
"""
    
    return content + metadata