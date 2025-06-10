from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List, Optional

# ---------------------
# Letter-related models
# ---------------------

#ask the user to provide this
class SenderInfo(BaseModel):
    """Sender's information."""
    name: str = Field(..., description="Full name of the sender.")
    address: str = Field(..., description="Postal address of the sender.")
    email: str = Field(..., description="Email address of the sender.")
    phone: str = Field(..., description="Phone number of the sender.")

#ask the user to provide this ? the ai may be able to find by itself I think
class RecipientInfo(BaseModel):
    """Recipient's information."""
    name: Optional[str] = Field(None, description="Name of the recipient (optional).")
    institution: str = Field(..., description="Name of the institution/company.")
    department: Optional[str] = Field(None, description="Department/division (optional).")
    address: Optional[str] = Field(None, description="Address of the institution (optional).")

#let the user define the required number of paragraphs and the strategic purpose of the paragraphs if he wants so
class Paragraph(BaseModel):
    strategic_purpose: str = Field(..., description="Strategic purpose of the paragraph in the argumentation")
    content: str = Field(..., description="Content of the paragraph")

# the user should be able to choose the number of paragraphs, by default we put 3 core paragraphs
class LetterContent(BaseModel):
    """Content of the motivation letter."""
    formal_opening: str = Field(..., description="FORMAL OPENING. e.g 'Dear Sir or Madam,' in English or 'Madame, Monsieur,' in French.")
    opening_paragraph: Paragraph = Field(..., description="OPENING PARAGRAPH. Establish relevance + last formation + overview of motivation")
    core_paragraphs: List[Paragraph] = Field(..., description="CORE PARAGRAPHS OF THE LETTER.")
    closing_paragraph: Paragraph = Field(..., description="LAST PARAGRAPH. Strategic purpose: Reinforce enthusiasm + call to action")
    gratitude: str = Field(..., description="GRATITUDE AND AVAILABILITY FOR INTERVIEW")
    final_greeting: str = Field(..., description="FORMAL CLOSING. e.g 'Sincerely,' or 'Regards' but it should not include the sender name.")

class MotivationLetter(BaseModel):
    """Complete motivation letter model."""
    sender: SenderInfo = Field(..., description="Sender's information.")
    recipient: RecipientInfo = Field(..., description="Recipient's information.")
    subject: str = Field("Motivation letter", description="Subject of the letter.")
    content: LetterContent = Field(..., description="Content of the letter.")

# -----------------
# CV-related models
# -----------------

class Education(BaseModel):
    institution: str = Field(..., description="Name of the educational institution")
    location: str = Field(..., description="City/Country of the institution")
    period: str = Field(..., description="Time period of education")
    degree: str = Field(..., description="Degree or program name")
    achievements: Optional[str] = Field(None, description="Notable achievements like rankings or honors")
    thesis: Optional[str] = Field(None, description="Thesis title if applicable")
    classes: List[str] = Field(default_factory=list, description="List attended classes or courses")

class Experience(BaseModel):
    organization: str = Field(..., description="Name of the organization")
    location: str = Field(..., description="Location of the organization")
    period: str = Field(..., description="Time period of the experience")
    supervision: Optional[str] = Field(None, description="Supervision details")
    subject: Optional[str] = Field(..., description="Project or role subject")
    role: str = Field(..., description="Role played")
    description: List[str] = Field(..., description="Detailed description points")
    technologies: Optional[List[str]] = Field(default_factory=list, description="Technologies or tools used")
    skills_highlighted: Optional[List[str]] = Field(..., description="Key skills highlighted")

class Project(BaseModel):
    name: str = Field(..., description="Project name")
    technologies: Optional[List[str]] = Field(default_factory=list, description="Technologies used")
    role: str = Field(..., description="Role played in the project")
    skills_highlighted: Optional[List[str]] = Field(..., description="Key skills highlighted")
    description: str = Field(..., description="Project description")

class PersonalInfo(BaseModel):
    name: str = Field(..., description="Full name")
    location: str = Field(..., description="Current location")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")

class Skills(BaseModel):
    programming_languages: Optional[List[str]] = Field(..., description="Programming languages and frameworks")
    languages: Optional[List[str]] = Field(..., description="Spoken languages")
    softwares: Optional[List[str]] = Field(..., description="Softwares mastered: should never include packages or libraries from programming languages")
    hobbies: Optional[List[str]] = Field(..., description="Personal interests and hobbies: put packages or librairies in the form 'Python(pandas, numpy)'")

class CV(BaseModel):
    personal_info: PersonalInfo = Field(..., description="Personal information")
    education: List[Education] = Field(..., description="Educational background")
    experience: Optional[List[Experience]] = Field(..., description="Professional experience")
    projects: Optional[List[Project]] = Field(..., description="Notable projects")
    skills: Skills = Field(..., description="Skills and interests")
    additional_info: Optional[List[str]] = Field(default_factory=list, description="Additional information: everything that cannot be put in the other sections")
