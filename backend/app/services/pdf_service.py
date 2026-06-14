import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.order import Order
from app.models.company import CompanyProfile

class PDFInvoiceService:
    @staticmethod
    def generate_invoice(order: Order, company: CompanyProfile) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor('#4F46E5'))
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
        normal_style = styles['Normal']
        
        # Header
        elements.append(Paragraph("TAX INVOICE", title_style))
        
        # Company Info
        company_name = company.company_name if company and company.company_name else "Your Company Name"
        gstin = company.gstin if company and company.gstin else "N/A"
        phone = company.phone if company and company.phone else "N/A"
        email = company.email if company and company.email else "N/A"
        address = company.address if company and company.address else "N/A"
        
        elements.append(Paragraph(f"<b>{company_name}</b>", heading_style))
        elements.append(Paragraph(f"GSTIN: {gstin}<br/>Phone: {phone}<br/>Email: {email}<br/>Address: {address}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Invoice Details & Customer Info
        data = [
            ["Invoice No:", f"INV-{order.id:04d}", "Billed To:"],
            ["Date:", datetime.utcnow().strftime("%Y-%m-%d"), order.customer],
            ["Due Date:", getattr(order, "delivery_date", "N/A"), ""]
        ]
        
        t1 = Table(data, colWidths=[80, 150, 200])
        t1.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,0), (2,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 30))
        
        # Line Items
        item_data = [["Description", "Quantity", "Unit Price", "Total"]]
        subtotal = 0.0
        
        for item in order.items:
            qty = float(item.quantity or 1)
            price = float(item.price or 0.0)
            total = qty * price
            subtotal += total
            item_data.append([
                item.name,
                f"{qty} {item.unit if item.unit else ''}",
                f"Rs. {price:.2f}",
                f"Rs. {total:.2f}"
            ])
            
        # Tax Calculation (assuming 18% standard IGST or CGST/SGST split)
        tax = subtotal * 0.18
        grand_total = subtotal + tax
        
        item_data.append(["", "", "Subtotal:", f"Rs. {subtotal:.2f}"])
        item_data.append(["", "", "GST (18%):", f"Rs. {tax:.2f}"])
        item_data.append(["", "", "Grand Total:", f"Rs. {grand_total:.2f}"])
        
        t2 = Table(item_data, colWidths=[240, 80, 100, 100])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -4), 1, colors.HexColor('#E5E7EB')),
            ('LINEBELOW', (0, -4), (-1, -4), 1, colors.black),
            ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 40))
        
        # Footer
        elements.append(Paragraph("Thank you for your business!", styles['Italic']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
