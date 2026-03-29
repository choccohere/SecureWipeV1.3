import os
import time

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def export_certificate_pdf(details, file_name=None):
    if not REPORTLAB_AVAILABLE:
        return False, "ReportLab not installed."

    if file_name is None:
        file_name = f"Erasure_Cert_{int(time.time())}.pdf"

    try:
        c = canvas.Canvas(file_name, pagesize=(8.5 * inch, 11 * inch))
        c.setTitle(f"Erasure Certificate")
        c.setFont("Courier", 10)
        
        text_object = c.beginText(1 * inch, 10 * inch)
        text_object.setLeading(14)
        
        text_object.textLine("--- SECURE WIPE ERASURE CERTIFICATE ---")
        text_object.textLine(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        text_object.textLine("")
        
        for key, value in details.items():
            text_object.textLine(f"{key.replace('_', ' ').title()}: {value}")
        
        text_object.textLine("")
        text_object.textLine("--- END OF REPORT ---")
        
        c.drawText(text_object)
        c.save()
        return True, os.path.abspath(file_name)
    except Exception as e:
        return False, str(e)
