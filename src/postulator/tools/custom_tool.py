from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field, PrivateAttr
import streamlit as st

from src.postulator.data_structures.custom_data_structures import CV

from datetime import datetime
from babel.dates import format_date
import locale

def get_formatted_date(language: str) -> str:
    """
    Returns the current date formatted according to the specified language.
    
    Args:
        language (str): Language code ('English', 'French', 'German', 'Spanish')
    
    Returns:
        str: Formatted date string
    """
    language_codes = {
        'English': 'en',
        'French': 'fr',
        'German': 'de',
        'Spanish': 'es'
    }
    
    lang_code = language_codes.get(language, 'en')
    
    try:
        return format_date(datetime.now(), format='long', locale=lang_code)
    except Exception:
        # Fallback to English if there's any error
        return format_date(datetime.now(), format='long', locale='en')
    
class human_feedback_input(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description=""" Should look like:
                   
Here is the draft of the motivation letter in JSON format:

```json
(put the json structure here)
```

Details about what you need the user to give a feedback about.
                   """) # "The draft of the letter ") #"What you need a feedback about and the draft")

class human_feedback(BaseTool):
    name: str = "Get human feedback and save"
    description: str = (
        "Ask the human user to give a feedback and retrieve the provided response."
        "If the human is satisfied, he can save the letter."
    )
    args_schema: Type[BaseModel] = human_feedback_input

    def _run(self,argument:str) -> str:
        try:
            #print(argument)
            splited = argument.split("```")
            #print( f"Len splited: {len(splited)}")
            if len(splited)>3: raise
            elif len(splited)==1:
                filtered = argument
            else:
                filtered = [ string for string in splited if "json" in string]
            if len(filtered) != 1: raise
            cleaned = (filtered[0]).replace("json\n","").replace("json","")
        except:
            return(""" Remember that the tool argument should look like:
                   
Here is the draft of the motivation letter in JSON format:

```json
(put the json structure here)
```

Details about what you need the user to give a feedback about.
                   """)
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            #print(f"JSON parsing failed: {e}")
            #print(f"The str we tried to parse was \n {cleaned}")
            return(f"JSON parsing failed: {e}")
            # Handle error here

         # Full structure available
        json_str_propre = json.dumps(data, indent=2)

        pydantic_letter = MotivationLetter.model_validate_json( json_str_propre )

        letter_for_feedback = letter_writer._letter_for_feedback(pydantic_letter)
        latex_letter = letter_writer._letter_from_pydantic(pydantic_letter)

        #
        content = pydantic_letter.content
        tmp = len(content.core_paragraphs)
        if tmp < 3:
            return(f"Your letter contains only {tmp} core paragraphs, whereas at least 3 core paragraphs are expected.")

        try:
            with open("output/motivation_letter_tmp.tex", 'w', encoding='utf-8') as file:
                file.write(latex_letter)

            import subprocess

            # Run pdflatex to compile the document (twice for references)
            try:
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", "output", "output/motivation_letter_tmp.tex"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                # Run again to resolve references (e.g., table of contents)
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", "output", "output/motivation_letter_tmp.tex"],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Compilation failed: {e.stderr}")

        except Exception as e:
            return(f"Error writing to file: {str(e)}")

        # check if the number of pages of the letter is acceptable
        import PyPDF2#.PdfReader
        with open("output/motivation_letter_tmp.pdf", "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(reader.pages)

            if num_pages > 2:
                return(f"Your letter is too long. It is {num_pages} pages long instead of 1 page.")
            
            if num_pages == 2:
                page = reader.pages[1]  # First page
                text = page.extract_text()

                # Split text into "lines" (approximate)
                lines = text.split("\n")
                num_lines = len(lines) #return(f"Your letter is too long. It is {num_pages} pages long instead of 1 page with {num_lines} lines on the second page.")
                #return(f"Your letter is too long. There is {num_lines} extra lines in the letter. Make make small changes (circa {15*num_lines} words to remove) to fill a single page completely")
                #return(f"Your letter is too long. Make make small changes to remove circa {8*num_lines} words (only from paragraphs, not from other parts) while keeping it pleasant to read.")
                return(f"Your letter is too long. Make it approximatively {2*num_lines} words shorter (only rework opening, core and closing paragraphs, not other parts) while keeping it pleasant to read."
                       f"Remember that the core paragraphs are expected to be larger than the opening and closing paragraphs.")

        print(80*"_")
        print(letter_for_feedback)
        print(80*"_")
        print(splited[-1])
        print(80*"_")
        print("Are you satisfied with the provided content?\n Type 'save' to keep the current version")
        print(80*"_")
        #response = input()
        print(80*"_")

        st.session_state.pydantic_letter = pydantic_letter
        st.session_state.feedback_asked = True
        st.session_state.preview_letter = letter_for_feedback
        st.session_state.latex_letter = latex_letter
        st.session_state.cleaned = cleaned

        #st.rerun()

        st.session_state.user_usage += 1

        from src.postulator.utils import update_user_usage
        update_user_usage(st.session_state.conn, st.session_state.sender_name)

        return("Your great letter was accepted by the human and successfully saved \n\n" + cleaned)

        #import time

        if st.session_state.feedback:
            feedback = st.session_state.feedback
            return feedback
        else:
            st.stop()


class cleaner_input(BaseModel):
    """Input schema for MyCustomTool."""
    text: str = Field(..., description="Your final answer.")


class final_response_cleaner(BaseTool):
    """Tool to clean the agent's final output by removing specified strings."""
    name: str = "Final answer cleaner"
    description: str = "Make sure the final output match the expected format."
    args_schema: Type[BaseModel] = cleaner_input

    # Private attributes (not part of the schema)
    _strings_to_remove: List[str] = PrivateAttr()

    def __init__(self, strings_to_remove: List[str] = [], result_as_answer=False):
        """
        Initializes the CleanAgentOutputTool.

        Args:
            strings_to_remove: A list of strings to remove from the agent's output.
        """
        super().__init__(result_as_answer=result_as_answer)#result_as_answer=result_as_answer)
        self._strings_to_remove = strings_to_remove

    def _run(self, text: str) -> str:
        """
        Cleans the given text by removing the specified strings.

        Args:
            text: The agent's final output text.

        Returns:
            The cleaned text.
        """
        for string_to_remove in self._strings_to_remove:
            text = text.replace(string_to_remove, "")
        return text


class letter_input(BaseModel):
    """Input schema for MyCustomTool."""
    text: str = Field(..., description="The letter in a structured JSON format matching the provided schema.")

import json
from src.postulator.data_structures.custom_data_structures import MotivationLetter

class letter_writer(BaseTool):
    """Tool to clean the agent's final output and write the letter."""
    name: str = "Beautiful letter"
    description: str = "Produce a beautiful letter from your final output."
    args_schema: Type[BaseModel] = cleaner_input

    # Private attributes (not part of the schema)
    _strings_to_remove: List[str] = PrivateAttr()

    def __init__(self, strings_to_remove: List[str] = ['```json\n', '```', '```json'], result_as_answer=True):
        super().__init__(result_as_answer=result_as_answer)#result_as_answer=result_as_answer)
        self._strings_to_remove = strings_to_remove

    def _run(self, text: str) -> str:
        
        # clean the output
        for string_to_remove in self._strings_to_remove:
            text = text.replace(string_to_remove, "")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"The str we tried to parse was \n {text}")
            return(f"JSON parsing failed: {e}")
            # Handle error here
        
        # Full structure available
        json_str_propre = json.dumps(data, indent=2)

        pydantic_letter = MotivationLetter.model_validate_json( json_str_propre )

        latex_letter = self._letter_from_pydantic(pydantic_letter)

        return latex_letter

    @staticmethod
    def _letter_for_feedback(pydantic_letter: MotivationLetter) -> str:
        """Generates a motivation letter from a Pydantic model."""
        sender = pydantic_letter.sender
        recipient = pydantic_letter.recipient
        content = pydantic_letter.content

        letter = f"""
    % ========== SENDER INFO ==========
    % Strategic purpose: Professional presentation of contact details
    {sender.name} 
    {sender.address} 
    {sender.email} 
    {sender.phone} 

    % ========== RECIPIENT INFO ==========
    % Strategic purpose: Demonstrate targeted application
    {recipient.name or ''} 
    {recipient.institution}
    {recipient.department or ''} 
    {recipient.address or ''}

    % ========== SUBJECT LINE ==========
    % Strategic purpose: Immediate context setting
    {pydantic_letter.subject}

    ________________________________________________________________________

    % ========== FORMAL OPENING ==========
    {content.formal_opening}

    % ========== OPENING PARAGRAPH ==========
    % Strategic purpose: {content.opening_paragraph.strategic_purpose}
    {content.opening_paragraph.content}

    { "\n".join(
            [ f""" 
    % ========== CORE PARAGRAPH {i+1} ==========
    % Strategic purpose: {content.core_paragraphs[i].strategic_purpose}
    {content.core_paragraphs[i].content}
    """ for i in range(len(content.core_paragraphs))]) }

    % ========== LAST PARAGRAPH ==========
    % Strategic purpose: {content.closing_paragraph.strategic_purpose}
    {content.closing_paragraph.content}

    % ========== GRATITUDE AND AVAILABILITY ==========
    {content.gratitude}

    % ========== FORMAL CLOSING ==========
    {content.final_greeting}
    
    {sender.name}
    """
        return letter

    @staticmethod
    def _letter_from_pydantic(pydantic_letter: MotivationLetter) -> str:
        """Generates a motivation letter from a Pydantic model."""
        sender = pydantic_letter.sender
        recipient = pydantic_letter.recipient
        content = pydantic_letter.content

        letter = f"""
    \\documentclass[11pt]{{letter}}
    \\usepackage[a4paper, top=25mm, bottom=25mm, left=25mm, right=25mm]{{geometry}}
    \\linespread{{1}}

    \\begin{{document}}
    \\thispagestyle{{empty}}

    % ========== SENDER INFO ==========
    % Strategic purpose: Professional presentation of contact details
    \\hfill {st.session_state.sender_name}\\\\
    \\strut\\hfill {st.session_state.sender_address}\\\\
    \\strut\\hfill {st.session_state.sender_email}\\\\
    \\strut\\hfill {st.session_state.sender_phone}

    % ========== RECIPIENT INFO ==========
    % Strategic purpose: Demonstrate targeted application
    \\vspace{{0.15cm}}
    {st.session_state.recipient_name or ''} { "\\\\" if st.session_state.recipient_name else ''} {st.session_state.recipient_institution} \\\\ {st.session_state.recipient_department or ''} { "\\\\" if st.session_state.recipient_department else '' }{st.session_state.recipient_address or ''} { "\\\\" if st.session_state.recipient_address else '' }

    % ========== DATE ==========
    \\vspace{{0.15cm}}
    \\hfill {get_formatted_date(st.session_state.language)}

    % ========== SUBJECT LINE ==========
    % Strategic purpose: Immediate context setting
    \\vspace{{0.5cm}}
    \\begin{{large}}
    \\textbf{{{pydantic_letter.subject.replace("%","\\%")}}}
    \\end{{large}}

    \\vspace{{0.15cm}}
    \\hrule
    \\vspace{{0.5cm}}

    % ========== FORMAL OPENING ==========
    {content.formal_opening.replace("%","\\%")}\\vspace{{0.15cm}}

    % ========== OPENING PARAGRAPH ==========
    % Strategic purpose: {content.opening_paragraph.strategic_purpose.replace("%","\\%")}
    {content.opening_paragraph.content.replace("%","\\%")}

    { "\n".join(
            [ f""" 
    % ========== CORE PARAGRAPH {i+1} ==========
    % Strategic purpose: {content.core_paragraphs[i].strategic_purpose.replace("%","\\%")}
    {content.core_paragraphs[i].content.replace("%","\\%")}
    """ for i in range(len(content.core_paragraphs))]) }

    % ========== LAST PARAGRAPH ==========
    % Strategic purpose: {content.closing_paragraph.strategic_purpose.replace("%","\\%")}
    {content.closing_paragraph.content.replace("%","\\%")}

    % ========== GRATITUDE AND AVAILABILITY ==========
    {content.gratitude.replace("%","\\%")}

    % ========== FORMAL CLOSING ==========
    \\vspace{{0.15cm}}
    {content.final_greeting.replace("%","\\%")}
    \\vspace{{1cm}}\\\\
    {sender.name}
    \\end{{document}}
    """
        return letter


import PyPDF2

class PdfReaderToolInput(BaseModel):
    """Input schema for PDF to Text conversion tool."""
    pdf_path: str = Field(..., description="Path to the PDF file to read")

class PdfReaderTool(BaseTool):
    name: str = "PDF reader"
    description: str = (
        "Read a PDF file and return its content"
    )
    args_schema: Type[BaseModel] = PdfReaderToolInput

    def _run(self, pdf_path: str) -> str:
        """Convert PDF to text with comprehensive error handling."""
        try:
            # Read PDF file
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                text = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:  # Handle empty pages
                        text.append(page_text)
                
                if not text:  # Handle PDFs with no extractable text
                    return("PDF contains no extractable text (might be scanned/image-based)")
                
                return '\n'.join(text)
                
        except FileNotFoundError:
            return(f"File not found: {pdf_path}")
        except PermissionError:
            return(f"Permission denied for file: {pdf_path}")
        except PyPDF2.errors.PdfReadError:
            return("Invalid or corrupted PDF file")
        except Exception as e:
            return(f"Conversion failed: {str(e)}")


class cv_cleaner_input(BaseModel):
    """Input schema for MyCustomTool."""
    text: str = Field(..., description="Your final answer.")

class cv_final_response_cleaner(BaseTool):
    """Tool to clean the agent's final output by removing specified strings."""
    name: str = "Final answer cleaner"
    description: str = "Make sure the final output match the expected format."
    args_schema: Type[BaseModel] = cleaner_input

    # Private attributes (not part of the schema)
    _strings_to_remove: List[str] = PrivateAttr()

    def __init__(self, strings_to_remove: List[str] = ["```json", "```"], result_as_answer=False):
        """
        Initializes the CleanAgentOutputTool.

        Args:
            strings_to_remove: A list of strings to remove from the agent's output.
        """
        super().__init__(result_as_answer=result_as_answer)#result_as_answer=result_as_answer)
        self._strings_to_remove = strings_to_remove

    def _run(self, text: str) -> str:
        """
        Cleans the given text by removing the specified strings.

        Args:
            text: The agent's final output text.

        Returns:
            The cleaned text.
        """
        for string_to_remove in self._strings_to_remove:
            text = text.replace(string_to_remove, "")
        
        try:
            st.session_state.cv_pydantic = CV.model_validate_json( text )
            st.session_state.indic = False

            #st.session_state.personal_info = True
            st.rerun()
            return("Great job, the CV was successfully parsed! \n \n" + st.session_state.cv_pydantic.model_dump_json(indent=4))
        except Exception as e:
            return( str(e) )

