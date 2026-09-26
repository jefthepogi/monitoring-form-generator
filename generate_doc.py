from pathlib import Path
from docxtpl import DocxTemplate
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from models import MonitoringFormDocumentData

def shade_cell(cell, fill_hex: str):
    """Adds a background color to a table cell natively."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill_hex)
    cell._tc.get_or_add_tcPr().append(shading)

def safe_get_sig(cert_idx: int, sig_idx: int, data: MonitoringFormDocumentData):
    """Safely fetch a signature, returning empty strings if it doesn't exist."""
    try:
        return data.signatures.certifications[cert_idx].signatories[sig_idx]
    except IndexError:
        return {"name": "", "title": ""}

def generate_templated_docx(
    json_path: str = "input_data.json", 
    template_path: str = "template.docx", 
    output_name: str = "SPMP_Monitoring_Final"
):
    raw_json = Path(json_path).read_text(encoding="utf-8")
    data = MonitoringFormDocumentData.model_validate_json(raw_json)

    # 1. Load the template (inherits perfect fonts, margins, and column widths)
    doc = DocxTemplate(template_path)

    # 2. Render all non-table Jinja tags (Title, Candidates, Signatures)
    context = {
        "hdr": data.header_info,
        "proj": data.project_info,
        "cert1": {
            "sig1": safe_get_sig(0, 0, data),
            "sig2": safe_get_sig(0, 1, data),
        },
        "cert2": {
            "sig1": safe_get_sig(1, 0, data),
            "sig2": safe_get_sig(1, 1, data),
        }
    }
    doc.render(context)

    # 3. Hybrid Native Table Generation
    # doc.tables[0] is the Document Header table. 
    # doc.tables[1] is the main Monitoring Matrix table.
    monitoring_table = doc.tables[1] 

    for item in data.monitoring_items:
        row_cells = monitoring_table.add_row().cells

        if item.is_header:
            # Format Gray Section Header Row (e.g. "1. OVERVIEW")
            cell = row_cells[0]
            for i in range(1, 7):
                cell.merge(row_cells[i])
            
            p = cell.paragraphs[0]
            run = p.add_run(f"{item.section_id} {item.title}".strip())
            run.bold = True
            run.font.size = Pt(9)
            shade_cell(cell, "E0E0E0")
            
        else:
            # Format Standard Data Row
            row_cells[0].text = f"{item.section_id} {item.title}".strip()
            row_cells[1].text = item.corrections or ""
            row_cells[2].text = item.page_no or ""
            row_cells[3].text = item.client_name or ""
            
            if item.complied:
                row_cells[4].text = "✓"
            else:
                row_cells[5].text = "✓"
                
            row_cells[6].text = item.remarks or ""

            # Standardize font sizes and alignments for the appended cells
            for col_idx, cell in enumerate(row_cells):
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(11)
                    
                    # Center align the Page No (2), Yes (4), and No (5) columns
                    if col_idx in [2, 4, 5]:
                        p.alignment = 1  # 1 = WD_ALIGN_PARAGRAPH.CENTER

    # 4. Save the final file
    output_path = Path(f"outputs/{output_name}.docx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        doc.save(output_path)
        print(f"\nSUCCESS! Pixel-perfect document generated: {output_path}")
    except PermissionError:
        print(f"\nERROR: Could not save '{output_path}'. Please close the file in Word.")

if __name__ == "__main__":
    generate_templated_docx()