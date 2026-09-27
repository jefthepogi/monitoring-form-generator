from typing import List, Optional
from pydantic import BaseModel, Field


class HeaderInfo(BaseModel):
    institution: str = Field(..., description="Name of the university/institution")
    location: str = Field(..., description="Campus location")
    department: str = Field(..., description="Department or course program")
    form_type: str = Field(..., description="Name of the form (e.g. 'SPMP Project Monitoring')")
    issue_no: str = Field(..., description="Document issue number")
    revision_no: str = Field(..., description="Document revision number")
    effective_date: str = Field(..., description="Form effective date")
    page_info: str = Field(..., description="Pagination text (e.g. Page 1 of 2)")


class ProjectInfo(BaseModel):
    title: str = Field(..., description="Title of Thesis / Capstone Project")
    candidates: List[str] = Field(..., description="List of student researchers")
    degree: str = Field(..., description="Degree program name")
    school_year: str = Field(..., description="Academic school year")
    term: str = Field(..., description="Academic term/semester")


class MonitoringItem(BaseModel):
    section_id: str = Field(default="", description="Section or chapter numbering")
    title: str = Field(..., description="Section title or description")
    is_header: bool = Field(default=False, description="True if item is a section header row")
    corrections: Optional[str] = Field(default="", description="Corrections/Suggestions/Recommendations text")
    page_no: Optional[str] = Field(default="", description="Page number of actual revision")
    client_name: Optional[str] = Field(default="", description="Name of evaluator/client")
    complied: Optional[bool] = Field(default=True, description="True for Yes, False for No")
    remarks: Optional[str] = Field(default="", description="Remarks or comments")


class SignaturesInfo(BaseModel):
    researchers: List[str] = Field(..., description="Names of student researchers")
    client_name: str = Field(..., description="Client/Respondent full name")
    client_title: str = Field(..., description="Client/Respondent title")
    professor_name: str = Field(..., description="Software Engineering Professor name")
    professor_title: str = Field(..., description="Professor designation title")


class MonitoringFormDocumentData(BaseModel):
    header_info: HeaderInfo
    project_info: ProjectInfo
    monitoring_items: List[MonitoringItem]
    signatures: SignaturesInfo