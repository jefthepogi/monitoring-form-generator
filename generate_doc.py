import os
import re
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docxtpl import DocxTemplate
from models import MonitoringFormDocumentData

# Declare optional values
MONITORING_HEADER_FONT_SIZE = 12
MONITORING_ITEM_FONT_SIZE = 11
MONITORING_FORM_TYPE = "SPMP_Monitoring"

def shade_cell(cell, fill_hex: str):
    """Adds a background color to a table cell safely without corrupting XML."""
    tcPr = cell._tc.get_or_add_tcPr()
    
    # Remove existing shading tags to prevent duplicate XML tag crashes
    existing_shd = tcPr.xpath('w:shd')
    for shd in existing_shd:
        tcPr.remove(shd)
        
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill_hex)
    tcPr.append(shading)

def safe_get_researcher(idx: int, data: MonitoringFormDocumentData):
    """Safely fetch a researcher's name for the first certification block,
    returning empty strings if that researcher slot doesn't exist."""
    try:
        return {"name": data.signatures.researchers[idx], "title": "Researcher"}
    except IndexError:
        return {"name": "", "title": ""}

def clean_template_to_file(template_path: str, temp_out_path: str) -> str:
    """Cleans Word's invisible XML fragmentation and removes duplicate ghost tags."""
    doc = Document(template_path)
    
    def scrub_paragraphs(paragraphs):
        # NOTE: doc.paragraphs / cell.paragraphs never reach text that lives
        # inside a floating text box (w:drawing > wps:txbx > w:txbxContent),
        # which is where proj.title/degree/school_year/term actually live in
        # this template. So this function can never see or fix those tags -
        # that's fine, because they are NOT duplicated in the visible render
        # (Word only shows the modern DrawingML copy; the legacy VML
        # "mc:Fallback" copy some naive text-extraction tools also pick up
        # is never displayed). This scrub is kept only as a safety net for
        # ordinary body/table-cell paragraphs, and is written so it never
        # touches formatting unless it actually needs to fix something.
        for p in paragraphs:
            original = p.text
            if "{{" not in original and "{%" not in original:
                continue
            text = original
            text = re.sub(r'\{\{\s*proj\.title\s*\}\}\{\{\s*proj\.title\s*\}\}', '{{ proj.title }}', text)
            text = re.sub(r'\{\{\s*proj\.degree\s*\}\}\{\{\s*proj\.degree\s*\}\}', '{{ proj.degree }}', text)
            text = re.sub(r'\{\{\s*proj\.school_year\s*\}\}\{\{\s*proj\.school_year\s*\}\}', '{{ proj.school_year }}', text)
            text = re.sub(r'\{\{\s*proj\.term\s*\}\}\{\{\s*proj\.term\s*\}\}', '{{ proj.term }}', text)
            if text == original:
                continue  # nothing actually changed - do NOT touch the paragraph,
                          # p.text = ... would wipe run formatting (font/bold/underline)
                          # even when the content is identical.
            # Something did change: write the new text into the first run and
            # blank out the rest, instead of using p.text = ... (which rebuilds
            # a single plain run and destroys formatting like bold/underline/font).
            if p.runs:
                p.runs[0].text = text
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.text = text

    scrub_paragraphs(doc.paragraphs)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                scrub_paragraphs(cell.paragraphs)

    doc.save(temp_out_path)
    return temp_out_path

def generate_templated_docx(
    json_path: str = "input_data.json", 
    template_path: str = "template.docx", 
    output_name: str = "SPMP_Monitoring"
):
    raw_json = Path(json_path).read_text(encoding="utf-8")
    data = MonitoringFormDocumentData.model_validate_json(raw_json)

    # 1. Clean the template and save to a temporary file
    temp_clean_path = "_temp_cleaned.docx"
    clean_template_to_file(template_path, temp_clean_path)

    # 2. Load the physically cleaned template into Jinja
    doc = DocxTemplate(temp_clean_path)

    # 3. Render all non-table Jinja tags
    # The template has two certification blocks:
    #   cert1 = the researchers' certification (up to 2 student signatories)
    #   cert2 = the client's attestation (1 signatory: the client)
    # SignaturesInfo is a flat model (researchers/client_name/client_title/...),
    # so we map it into the two nested cert1/cert2 shapes the template expects.
    context = {
        "hdr": data.header_info,
        "proj": data.project_info,
        "sig": data.signatures,
        "cert1": {
            "sig1": safe_get_researcher(0, data),
            "sig2": safe_get_researcher(1, data),
        },
        "cert2": {
            "sig1": {
                "name": data.signatures.client_name,
                "title": data.signatures.client_title,
            },
        },
    }
    doc.render(context)

    # 4. Bulletproof Dynamic Monitoring Table Locator
    monitoring_table = None
    for tbl in doc.tables:
        try:
            first_row_raw = "".join(c.text for c in tbl.rows[0].cells).lower().replace(" ", "")
            if "part" in first_row_raw or "chapter" in first_row_raw or "corrections" in first_row_raw:
                monitoring_table = tbl
                break
        except Exception:
            continue
            
    if monitoring_table is None:
        print("\nERROR: Could not find the Monitoring Table!")
        if os.path.exists(temp_clean_path): os.remove(temp_clean_path)
        return

    # 5. Hybrid Native Table Generation
    for item in data.monitoring_items:
        row_cells = monitoring_table.add_row().cells

        # --- CRITICAL CORRUPTION FIX ---
        # Strip vertical merge tags (vMerge) inherited from the header row
        for cell in row_cells:
            tcPr = cell._tc.get_or_add_tcPr()
            v_merge = tcPr.find(qn("w:vMerge"))
            if v_merge is not None:
                tcPr.remove(v_merge)
        # -------------------------------

        if item.is_header:
            # Safely merge cells in a single operation
            row_cells[0].merge(row_cells[-1])
            
            p = row_cells[0].paragraphs[0]
            run = p.add_run(f"{item.section_id} {item.title}".strip())
            run.bold = True
            run.font.size = Pt(MONITORING_HEADER_FONT_SIZE)
            shade_cell(row_cells[0], "E0E0E0")
            
        else:
            row_cells[0].text = f"{item.section_id} {item.title}".strip()
            row_cells[1].text = item.corrections or ""
            row_cells[2].text = item.page_no or ""
            row_cells[3].text = item.client_name or ""
            
            if item.complied:
                row_cells[4].text = "✓"
            else:
                row_cells[5].text = "✓"
                
            row_cells[6].text = item.remarks or ""

            for col_idx, cell in enumerate(row_cells):
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(MONITORING_ITEM_FONT_SIZE)
                    if col_idx in [2, 4, 5]:
                        p.alignment = 1  # 1 = WD_ALIGN_PARAGRAPH.CENTER

    # 6. Save the final file
    output_path = Path(f"outputs/{output_name}.docx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        doc.save(output_path)
        print(f"\nSUCCESS! Pixel-perfect document generated: {output_path}")
    except PermissionError:
        print(f"\nERROR: Could not save '{output_path}'. Please close the file in Word.")
    finally:
        if os.path.exists(temp_clean_path):
            os.remove(temp_clean_path)

if __name__ == "__main__":
    generate_templated_docx(output_name=MONITORING_FORM_TYPE)