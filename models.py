from typing import List, Optional
from pydantic import BaseModel, Field


class HeaderInfo(BaseModel):
    institution: str = Field(..., description="Name of the university/institution")
    location: str = Field(..., description="Campus location")
    department: str = Field(..., description="Department or course program")
    form_type: str = Field(
        ...,
        description=(
            "Name of this specific monitoring form, e.g. 'SPMP Project Monitoring', "
            "'SRS Project Monitoring', or 'SDD Project Monitoring'. The template is "
            "generic, so any of the three compliance sheets can be produced by "
            "changing this value (and the monitoring_items)."
        ),
    )
    issue_no: str = Field(..., description="Document issue number")
    revision_no: str = Field(..., description="Document revision number")
    effective_date: str = Field(..., description="Form effective date")
    page_info: str = Field(..., description="Pagination text (e.g. 'Page 1 of 2')")
    logo_path: Optional[str] = Field(
        default=None,
        description="Optional path to a logo image file placed in the header's logo cell.",
    )


class ProjectInfo(BaseModel):
    title: str = Field(..., description="Title of Thesis / Feasibility Study / Capstone Project")
    candidates: List[str] = Field(..., description="Names of student researchers/candidates")
    degree: str = Field(..., description="Degree program name")
    school_year: str = Field(..., description="Academic school year")
    term: str = Field(..., description="Academic term/semester")


class TableColumns(BaseModel):
    """Editable column labels for the monitoring table. Kept in the data model
    (instead of hardcoded in the generator) so the same script can render the
    SPMP, SRS, or SDD compliance sheet just by swapping these labels."""

    part_chapter: str = "Part/Chapter"
    corrections: str = "Corrections/Suggestions/Recommendations"
    page_no: str = "Page No."
    page_no_footnote: Optional[str] = Field(
        default="1", description="Superscript footnote marker rendered next to the Page No. header."
    )
    client_name: str = "Name of Client"
    complied: str = "Complied?"
    complied_yes: str = "Yes"
    complied_no: str = "No"
    remarks: str = "Remarks with signature of client"


class MonitoringItem(BaseModel):
    section_id: str = Field(default="", description="Section or chapter numbering")
    title: str = Field(..., description="Section title or description")
    is_header: bool = Field(default=False, description="True if this row is a section header/divider row")
    corrections: Optional[str] = Field(
        default="", description="Corrections/Suggestions/Recommendations noted for this section"
    )
    page_no: Optional[str] = Field(default="", description="Page number of the actual revision")
    client_name: Optional[str] = Field(default="", description="Name of evaluator/client")
    complied: Optional[bool] = Field(default=True, description="True renders a check under Yes, False under No")
    remarks: Optional[str] = Field(default="", description="Remarks, with signature of client")


class Signatory(BaseModel):
    name: str = Field(..., description="Full name printed under the signature line")
    title: str = Field(..., description="Title/role printed under the name (e.g. 'Researcher')")


class Certification(BaseModel):
    """One attestation block: a statement followed by one or more signature lines,
    laid out side by side. Replaces the two hardcoded certification paragraphs
    that used to live in the generator script."""

    statement: str = Field(..., description="Certification/attestation statement text")
    signatories: List[Signatory] = Field(..., description="People who sign under this statement, left to right")


class SignaturesInfo(BaseModel):
    certifications: List[Certification] = Field(
        ...,
        description=(
            "Ordered list of certification blocks, e.g. the researchers' certification "
            "followed by the client/professor attestation."
        ),
    )


class MonitoringFormDocumentData(BaseModel):
    header_info: HeaderInfo
    project_info: ProjectInfo
    table_columns: TableColumns = Field(default_factory=TableColumns)
    monitoring_items: List[MonitoringItem]
    notes: List[str] = Field(
        default_factory=lambda: [
            "Student-researchers are required to submit this Compliance Sheet for them to be given grades.",
            "Please indicate page numbers of the actual revision based on the revised copy of the manuscript.",
        ],
        description="Numbered footnotes rendered above the certification block.",
    )
    signatures: SignaturesInfo
