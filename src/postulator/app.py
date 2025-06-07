from src.postulator.crew import Postulator
from src.postulator.data_structures.custom_data_structures import *
import json
import os
import streamlit as st
from src.postulator.utils import *
from streamlit_gsheets import GSheetsConnection

from src.postulator.data_structures.custom_data_structures import CV, PersonalInfo, Education, Experience, Project, Skills

from src.postulator.translations import TRANSLATIONS

from streamlit_pdf_viewer import pdf_viewer

def app():
    # Set page config
    st.set_page_config(
        page_title="Motivation Letter Generator",
        page_icon="✍️",
        layout="wide"
    )

    # Add custom CSS
    st.markdown("""
    <style>
        .stApp {
            max-width: 800px !important;  /* Reduced from 1000px */
            margin: 0 auto !important;
            padding: 0 20px;
        }
        .main-header {
            text-align: center;
            padding: 2rem 0;
        }
        .input-section {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        /* Force container width */
        .block-container {
            max-width: 800px !important;
            padding: 0 !important;
        }
        /* Ensure PDF viewer stays within bounds */
        .pdf-viewer {
            width: 100% !important;
            max-width: 800px !important;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)


    # Initialize session state
    if 'feedback' not in st.session_state:
        st.session_state.feedback_asked = None
    if 'preview_letter' not in st.session_state:
        st.session_state.preview_letter = None
    if 'approve_btn' not in st.session_state:
        st.session_state.approve_btn = None
    if 'refuse_btn' not in st.session_state:
        st.session_state.refuse_btn = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'cleaned' not in st.session_state:
        st.session_state.cleaned = None
    if 'latex_letter' not in st.session_state:
        st.session_state.latex_letter = None
    if 'cv_path' not in st.session_state:
        st.session_state.cv_path = None
    if 'i' not in st.session_state:
        st.session_state.i = 0
    if 'api_key_validated' not in st.session_state:
        st.session_state.api_key_validated = False
    if 'personal_writeup' not in st.session_state:
        st.session_state.personal_writeup = None
    if "pydantic_letter" not in st.session_state:
        st.session_state.pydantic_letter = None
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    if "personal_info" not in st.session_state:
        st.session_state.personal_info = False
    if "cv_pydantic" not in st.session_state:
        st.session_state.cv_pydantic = ""
    if "cv_text" not in st.session_state:
        st.session_state.cv_text = ""
    if "sender_name" not in st.session_state:
        st.session_state.sender_name = ""
    if "sender_email" not in st.session_state:
        st.session_state.sender_email = ""
    if "sender_address" not in st.session_state:
        st.session_state.sender_address = ""
    if "sender_phone" not in st.session_state:
        st.session_state.sender_phone = ""
    if "letter_generator" not in st.session_state:
        st.session_state.letter_generator = False
    if "interface_language" not in st.session_state:
        st.session_state.interface_language = "English"
    if "user_usage" not in st.session_state:
        st.session_state.user_usage = None
    if "api_key_provided" not in st.session_state:
        st.session_state.api_key_provided = False

    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state.conn = conn

    # Get translations for selected language
    t = TRANSLATIONS[st.session_state.interface_language]

    st.markdown('<div class="main-header"><h1>✍️ Postulator </h1></div>', unsafe_allow_html=True)

    if not st.session_state.api_key_validated:
        # API Key Input Section
        st.markdown("<h3 style='text-align: center; margin-bottom: 2rem;'>Your AI-powered Cover Letter Generator</h3>", unsafe_allow_html=True)
        
        # Add language selector at the top
        interface_language = st.selectbox(
            "Interface Language",
            #t["language_selector"],
            options=["English", "French"],
            help="Select the language for your motivation letter"
        )

        if interface_language != st.session_state.interface_language:
            st.session_state.interface_language = interface_language
            st.rerun()
        
        api_key = st.text_input(t["api_key_input"], type="password", help="Get your free API key from Google AI Studio")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(t["submit"], key="submit_api_key"):
                is_valid, message = validate_api_key(api_key.replace(" ",""))
                if is_valid:
                    st.session_state.api_key_validated = True
                    os.environ["GEMINI_API_KEY"] = api_key
                    st.session_state.api_key_provided = True

                    from src.postulator.utils import load_from_gsheet

                    load_from_gsheet(conn, api_key)

                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            st.page_link("https://aistudio.google.com/app/apikey", label=t["get_api_key"], use_container_width=True,)

        # Add explanation about API key requirement
        st.info(t["api_key_info"])

        if st.button(t["try"], key="without_api_key"):
            st.session_state.api_key_validated = True
            os.environ["GEMINI_API_KEY"] = st.secrets["gemini_api_test"]
            st.session_state.api_key_provided = False

            st.rerun()

    if not st.session_state.personal_info and st.session_state.api_key_validated:

        if "indic" not in st.session_state:
            st.session_state.indic = True

        # Sender Information Section
        st.markdown(f"## {t['personal_info_title']}")

        if not "tmp_cv_pdf" in st.session_state:
                st.session_state.tmp_cv_pdf = None

        if not "cv_path_pdf" in st.session_state:
            st.session_state.cv_path_pdf = None

        if "edit_cv" not in st.session_state:
            st.session_state.edit_cv = False

        if not (st.session_state.cv_pydantic or st.session_state.cv_text) or (st.session_state.cv_path_pdf is None and st.session_state.edit_cv) and not (st.session_state.cv_pydantic and st.session_state.edit_cv):# and not ((st.session_state.cv_pydantic or st.session_state.cv_text) and not st.session_state.cv_path_pdf and st.session_state.indic):

            #st.markdown("### Upload your CV")
            uploaded_cv = st.file_uploader(t["cv_upload"],
                                            type=['pdf'], #label_visibility="collapsed", 
                                            key="pdf"+str(st.session_state.i) )
            if uploaded_cv:
                st.success(f"Successfully uploaded: {uploaded_cv.name}")

                file_path = os.path.join("input", (os.environ["GEMINI_API_KEY"])[:5] + "tmp_cv.pdf")
                st.session_state.cv_path_pdf = file_path
                with open(file_path, "wb") as f:
                    f.write(uploaded_cv.getvalue())

                import pymupdf4llm

                cv_pdf = pymupdf4llm.to_markdown(file_path)

                print("CV from pdf: \n", cv_pdf)

                #st.session_state.tmp_cv_pdf = cv_pdf

                from src.postulator.crew import CVParser

                inputs = {
                    "schema": CV.model_json_schema(),
                    "cv_pdf": cv_pdf,
                }

                result = CVParser(os.environ["GEMINI_API_KEY"]).crew().kickoff(inputs=inputs).raw#.replace("```json", "").replace("```", "")

                print(result)

                # Delete the temporary PDF file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Temporary file {file_path} deleted successfully")

                print(st.session_state.cv_pydantic.model_dump_json(indent=4))

                st.warning("It is an experimental feature. Please check below if your CV is correctly parsed.")

                from src.postulator.utils import update_gsheet

                st.session_state.indic = False

                #st.session_state.personal_info = True
                st.rerun()

        if st.session_state.cv_path_pdf or (st.session_state.cv_pydantic and st.session_state.edit_cv):

            #st.markdown("### Upload your CV")
            if st.button("Remove CV", key="remove_cv_btn"):
                #os.remove(st.session_state.cv_path)
                st.success("CV removed successfully!")
                st.session_state.cv_path_pdf = None
                st.session_state.cv_pydantic = None
                st.session_state.i += 1
                st.rerun()
        
        # A boolean that indicates if we have already a pydantic cv for the user
        cv_old = True if st.session_state.cv_pydantic else False
    
        # Personal Information
        col1, col2 = st.columns(2)
        with col1:
            sender_name = st.text_input(t["full_name"], st.session_state.cv_pydantic.personal_info.name if st.session_state.cv_pydantic else st.session_state.sender_name)
            st.session_state.sender_name = sender_name
            sender_email = st.text_input(t["email"], st.session_state.cv_pydantic.personal_info.email if st.session_state.cv_pydantic else st.session_state.sender_email)
            st.session_state.sender_email = sender_email
        with col2:
            sender_address = st.text_input(t["address"], st.session_state.cv_pydantic.personal_info.location if st.session_state.cv_pydantic else st.session_state.sender_address)
            st.session_state.sender_address = sender_address
            sender_phone = st.text_input(t["phone"], st.session_state.cv_pydantic.personal_info.phone if st.session_state.cv_pydantic else st.session_state.sender_phone)
            st.session_state.sender_phone = sender_phone

        if "cv_upload" not in st.session_state:
            st.session_state.cv_upload = False
        if "cv_form" not in st.session_state:
            st.session_state.cv_form = False

        if (st.session_state.cv_pydantic or st.session_state.cv_text) and not st.session_state.cv_path_pdf and st.session_state.indic and not st.session_state.edit_cv:
            st.success(t["cv_loaded"])#"Your CV has been successfully loaded from memory! 😊 You can upload a new one or edit it manually.")#Below you can now edit it or upload a new one.")

            if not st.session_state.edit_cv:
                column1, column2 = st.columns(2)
                with column1:
                    if st.button(t["continue"], key="continue_btn"):
                        st.session_state.personal_info = True
                        st.session_state.letter_generator = True

                        from src.postulator.utils import load_user_usage
                        load_user_usage(conn, st.session_state.sender_name)

                        st.rerun()
                with column2:
                    if st.button(t["edit_cv"], key="edit_cv_btn"):
                        st.session_state.edit_cv = True
                        st.rerun()
                #st.stop()
        else:
            st.session_state.edit_cv = True

        st.session_state.cv_form = True
            
        if st.session_state.cv_form and st.session_state.edit_cv:


            # Personal Information
            personal_info = PersonalInfo(
                name=st.session_state.sender_name,
                location=st.session_state.sender_address,
                email=st.session_state.sender_email,
                phone=st.session_state.sender_phone
            )

            # A boolean that indicates if we have already a pydantic cv for the user
            cv_old = True if st.session_state.cv_pydantic else False

            # Education
            st.header("Education")
            education_list = []
            num_education = st.number_input("Number of Education Entries", 
                                            min_value=0, 
                                            value= len(st.session_state.cv_pydantic.education) if cv_old else 0)

            old_num_edu = len(st.session_state.cv_pydantic.education) if cv_old else 0
            
            for i in range(num_education):
                st.subheader(f"Education #{i+1}")
                tmp_old = st.session_state.cv_pydantic.education[i] if i <= old_num_edu else None
                education = Education(
                    institution=st.text_input(f"Institution #{i+1}", tmp_old.institution if tmp_old else ""),
                    location=st.text_input(f"Location #{i+1}", tmp_old.location if tmp_old else ""),
                    period=st.text_input(f"Period #{i+1} (e.g., 2022-2023)", tmp_old.period if tmp_old else ""),
                    degree=st.text_input(f"Degree #{i+1}", tmp_old.degree if tmp_old else ""),
                    achievements=st.text_input(f"Achievements #{i+1} (optional)", tmp_old.achievements if tmp_old else ""),
                    thesis=st.text_input(f"Thesis Title #{i+1} (optional)",  tmp_old.thesis if tmp_old else ""),
                    classes=st.text_area(f"Classes #{i+1} (one per line)", "\n".join(tmp_old.classes) if tmp_old else "").split('\n')
                )
                education_list.append(education)

            # Experience
            st.header("Professional Experience")
            experience_list = []
            num_experience = st.number_input("Number of Experience Entries", 
                                             min_value=0, 
                                             value= len(st.session_state.cv_pydantic.experience) if cv_old else 0)

            for i in range(num_experience):
                st.subheader(f"Experience #{i+1}")
                #tmp_old = st.session_state.cv_pydantic.experience[i] if (i < old_num_edu and st.session_state.cv_pydantic.experience) else None
                tmp_old = st.session_state.cv_pydantic.experience[i] if (i <= old_num_edu) else None
                experience = Experience(
                    organization=st.text_input(f"Organization #{i+1}", tmp_old.organization if tmp_old else ""),
                    location=st.text_input(f"Organization Location #{i+1}", tmp_old.location if tmp_old else ""),
                    period=st.text_input(f"Period #{i+1}", tmp_old.period if tmp_old else ""),
                    supervision=st.text_input(f"Supervision Details #{i+1} (optional)", tmp_old.supervision if tmp_old else ""),
                    subject=st.text_input(f"Project/Role Subject #{i+1}", tmp_old.subject if tmp_old else ""),
                    role=st.text_input(f"Role #{i+1}", tmp_old.role if tmp_old else ""),
                    description=st.text_area(f"Description Points #{i+1} (one per line)", "\n".join(tmp_old.description) if tmp_old else "" ).split('\n'),
                    technologies=st.text_input(f"Technologies Used #{i+1} (comma-separated)", ",".join(tmp_old.technologies) if (tmp_old and tmp_old.technologies) else "").split(','),# if st.text_input(f"Technologies Used #{i+1} (comma-separated)") else [],
                    skills_highlighted=st.text_input(f"Skills Highlighted #{i+1} (comma-separated)", ",".join(tmp_old.skills_highlighted) if (tmp_old and tmp_old.skills_highlighted) else "" ).split(',')
                )
                experience_list.append(experience)

            # Projects
            st.header("Projects")
            projects_list = []
            num_projects = st.number_input("Number of Projects", 
                                           min_value=0, 
                                           value= len(st.session_state.cv_pydantic.projects) if (cv_old and st.session_state.cv_pydantic.projects) else 0)

            old_num_proj = len(st.session_state.cv_pydantic.projects) if (cv_old and st.session_state.cv_pydantic.projects) else 0
            
            for i in range(num_projects):
                st.subheader(f"Project #{i+1}")
                tmp_old = st.session_state.cv_pydantic.projects[i] if (i <= old_num_proj and st.session_state.cv_pydantic.projects) else None
                project = Project(
                    name=st.text_input(f"Project Name #{i+1}", tmp_old.name if tmp_old else ""),
                    technologies=st.text_input(f"Project Technologies #{i+1} (comma-separated)", ",".join(tmp_old.technologies) if (tmp_old and tmp_old.technologies) else "").split(','),# if st.text_input(f"Project Technologies #{i+1} (comma-separated)") else [],
                    role=st.text_input(f"Project Role #{i+1}", tmp_old.role if tmp_old else ""),
                    skills_highlighted=st.text_input(f"Project Skills #{i+1} (comma-separated)", ",".join(tmp_old.skills_highlighted) if (tmp_old and tmp_old.skills_highlighted) else "").split(','),# if st.text_input(f"Project Skills #{i+1} (comma-separated)") else [],
                    description=st.text_area(f"Project Description #{i+1}", tmp_old.description if tmp_old else ""),
                )
                projects_list.append(project)

            # Skills
            st.header("Skills")
            tmp_old = st.session_state.cv_pydantic.skills if cv_old else None
            skills = Skills(
                languages=st.text_input("Spoken Languages (comma-separated)", ",".join(tmp_old.languages) if (tmp_old and tmp_old.languages) else "").split(','),
                softwares=st.text_input("Software Skills (comma-separated)", ",".join(tmp_old.softwares) if (tmp_old and tmp_old.softwares) else "").split(','),
                programming_languages=st.text_input("Programming Languages (comma-separated)", ",".join(tmp_old.programming_languages) if (tmp_old and tmp_old.programming_languages) else "").split(','),
                hobbies=st.text_input("Hobbies (comma-separated)", ",".join(tmp_old.hobbies) if (tmp_old and tmp_old.hobbies)else "").split(',')
            )

            # Additional Information
            st.header("Additional Information")
            tmp_old = st.session_state.cv_pydantic.additional_info if cv_old else None
            additional_info = st.text_area("Additional Information (one per line)", "\n".join(tmp_old) if tmp_old else "").split('\n')

            if not (st.session_state.cv_form or st.session_state.cv_upload):
                st.stop()

            if st.button(t["submit_personal_info"], type="primary"):
                if st.session_state.cv_upload and  not (st.session_state.cv_path and st.session_state.sender_name and st.session_state.sender_email and st.session_state.sender_phone):
                    st.error("Please fill in all required fields")
                elif st.session_state.cv_form:

                    try:
                        cv = CV(
                            personal_info=personal_info,
                            education=education_list,
                            experience=experience_list,
                            projects=projects_list,
                            skills=skills,
                            additional_info=additional_info
                        )
                        st.success(t["cv_generated"])
                        print(cv)

                        st.session_state.cv_pydantic = cv

                        print(cv.model_dump_json(indent=4))

                    except Exception as e:
                        st.error(f"Error generating CV: {str(e)}")

                    
                    if not (st.session_state.cv_pydantic and 
                                sender_name and 
                                sender_email and 
                                sender_phone
                                ):
                        st.error("Please fill in all required fields (Full Name, Address, Email, Phone Number)")
                    else:
                        from src.postulator.utils import update_gsheet
                        # update the sheet with the new data
                        update_gsheet(conn, os.environ["GEMINI_API_KEY"], spreadsheet="Feuille 1")

                        update_gsheet(conn, os.environ["GEMINI_API_KEY"], spreadsheet="Feuille 2")

                        from src.postulator.utils import load_user_usage
                        load_user_usage(conn, st.session_state.sender_name)

                        st.session_state.personal_info = True
                        st.session_state.letter_generator = True
                        st.rerun()
                    

                    st.error("Please fill in all required fields")
                else:
                    from src.postulator.utils import update_gsheet
                    # update the sheet with the new data
                    update_gsheet(conn, os.environ["GEMINI_API_KEY"], spreadsheet="Feuille 1")

                    update_gsheet(conn, os.environ["GEMINI_API_KEY"], spreadsheet="Feuille 2")

                    from src.postulator.utils import load_user_usage
                    load_user_usage(conn, st.session_state.name)

                    st.session_state.personal_info = True
                    st.session_state.letter_generator = True
                    st.rerun()

    if st.session_state.letter_generator:
        # Job Information Section
        st.markdown(f"## {t["job_info_title"]}")
        job_posting = st.text_input(
            t["job_url"],
            help=t["job_url_help"] #"Provide either the URL of the job posting or paste the text from the job posting as text"
        )
        st.warning(t["linkedin_warning"]) #"⚠️ LinkedIn job URLs are not supported yet. Please paste the job description text directly. \n If the generator doesn't work, try to paste the text directly.")
        
        language = st.selectbox(
            t["letter_language"],
            options=["English", "French", "German", "Spanish"],
            help= t["language_help"]
        )
        st.session_state.language = language
        
        personal_writeup = st.text_area(
            t["personal_notes"],
            st.session_state.personal_writeup,#.replace("empty", ""),
            help=t["notes_help"]   #"Add any personal information or notes that might be relevant for the current application"
        )
        st.session_state.personal_writeup = personal_writeup

        st.info(t["personnal_notes_info"])

        # Recipient Information Section
        st.markdown(f"## {t["recipient_info"]}")
        col1, col2 = st.columns(2)
        with col1:
            recipient_name = st.text_input(t["recipient_name"])
            st.session_state.recipient_name = recipient_name  # Store in session state for later use in the tex
            recipient_institution = st.text_input(t["company_name"])
            st.session_state.recipient_institution = recipient_institution  # Store in session state for later use in the tex
        with col2:
            recipient_department = st.text_input(t["department"])
            st.session_state.recipient_department = recipient_department  # Store in session state for later use in the tex
            recipient_address = st.text_input(t["company_address"])
            st.session_state.recipient_address = recipient_address  # Store in session state for later use in the tex

        column1, column2 = st.columns(2)
        with column1:
            if st.button(t["generate_letter"], type="primary"):
                if not (st.session_state.cv_pydantic or st.session_state.cv_text) and not (job_posting and 
                        st.session_state.sender_name and 
                        st.session_state.sender_email and 
                        st.session_state.sender_phone and 
                        st.session_state.recipient_institution):
                    st.error("Please fill in all required fields")
                elif (not st.session_state.api_key_provided) and st.session_state.user_usage >= 2:
                    st.error("You reached the limit of 2 letters without providing your API key. Please provide your API key to run the app for free.")
                else:
                    print("Write-up: ", st.session_state.personal_writeup)
                    print("Write-up type: ", type(st.session_state.personal_writeup))
                    print("Write-up test:", st.session_state.personal_writeup != "")
                    
                    from src.postulator.utils import update_gsheet
                    update_gsheet(conn, os.environ["GEMINI_API_KEY"], spreadsheet="Feuille 1")

                    with st.spinner(t["generating"]):

                        print( st.session_state.cv_pydantic.model_dump_json(indent=4) if st.session_state.cv_form else st.session_state.cv_text )

                        try:
                            # Load config and add schema
                            inputs = {
                                "job_posting": job_posting,
                                "language": language,
                                "personal_writeup": personal_writeup,
                                "schema" : json.dumps( MotivationLetter.model_json_schema() ),
                                "resume" : st.session_state.cv_text if st.session_state.cv_text else st.session_state.cv_pydantic.model_dump_json() #st.session_state.cv_pydantic.model_dump_json() if st.session_state.cv_form else st.session_state.cv_text,
                                } 

                            # Generate letter
                            result = Postulator(os.environ["GEMINI_API_KEY"],st.session_state.cv_path).crew().kickoff(inputs=inputs)

                            print(result.tasks_output)
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
        with column2:
            if st.button(t["edit_cv"], key="edit_cv_btn_bis"):
                st.session_state.edit_cv = True
                st.session_state.personal_info = False
                st.session_state.letter_generator = False
                st.rerun()

        
        if st.session_state.feedback_asked:

            st.markdown("---")
            st.markdown(f"### {t["letter_preview"]}")

            if os.path.exists("output/motivation_letter_tmp.pdf"):
                st.markdown("""
                    <style>
                        .pdf-viewer {
                            width: 100%;
                            max-width: 1000px;
                            margin: 0 auto;
                        }
                    </style>
                """, unsafe_allow_html=True)
                with st.container():
                    st.markdown('<div class="pdf-viewer">', unsafe_allow_html=True)
                    pdf_viewer("output/motivation_letter_tmp.pdf",
                            height=1200,
                            rendering= "unwrap",
                            )
                    st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown(f"### {t["approval"]}")
            st.markdown(t["satisfaction"])

            col1, col2 = st.columns([1, 1])

            with col1:
                with open("output/motivation_letter_tmp.pdf", "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                    if st.download_button(
                                label=t["download_pdf"],
                                data=pdf_bytes,
                                file_name="motivation_letter.pdf",
                                mime="application/pdf",
                            ):
                        
                        st.success(t["download_success"])

            with col2:
                st.button(t["refuse_edit"], type="secondary", key="refuse_btn")
            
            if st.session_state.refuse_btn:
                st.session_state.edit_mode = True

            if st.session_state.edit_mode:
                pydantic_letter = st.session_state.pydantic_letter
                
                st.markdown(f"### {t["edit_letter"]}")
                    
                subject = st.text_input(
                    "Subject",
                    value=pydantic_letter.subject,
                )
                
                # Formal Opening
                formal_opening = st.text_area(
                    "Formal Opening",
                    value=pydantic_letter.content.formal_opening,
                )

                # Opening Paragraph
                opening_purpose = pydantic_letter.content.opening_paragraph.strategic_purpose
                opening_content = st.text_area(
                    "Opening Paragraph",
                    value=pydantic_letter.content.opening_paragraph.content
                )

                # Core Paragraphs
                core_paragraphs = []
                for i, para in enumerate(pydantic_letter.content.core_paragraphs):
                    purpose = para.strategic_purpose
                    content = st.text_area(
                        f"Core paragraph {i+1}",
                        value=para.content,
                        key=f"core_content_{i}"
                    )
                    core_paragraphs.append({"purpose": purpose, "content": content})

                # Closing Paragraph
                closing_purpose = pydantic_letter.content.closing_paragraph.strategic_purpose
                closing_content = st.text_area(
                    "Closing Paragraph",
                    value=pydantic_letter.content.closing_paragraph.content
                )

                # Gratitude and Final Greeting
                gratitude = st.text_area(
                    "Gratitude",
                    value=pydantic_letter.content.gratitude
                )
                final_greeting = st.text_area(
                    "Final Greeting",
                    value=pydantic_letter.content.final_greeting
                )

                # Update the pydantic_letter with the edited values
                if st.button(t["update_letter"], type="primary"):
                    # Create updated letter content
                    updated_content = LetterContent(
                        formal_opening=formal_opening,
                        opening_paragraph=Paragraph(
                            strategic_purpose=opening_purpose,
                            content=opening_content
                        ),
                        core_paragraphs=[
                            Paragraph(
                                strategic_purpose=p["purpose"],
                                content=p["content"]
                            ) for p in core_paragraphs
                        ],
                        closing_paragraph=Paragraph(
                            strategic_purpose=closing_purpose,
                            content=closing_content
                        ),
                        gratitude=gratitude,
                        final_greeting=final_greeting
                    )
                    
                    # Update the full letter
                    st.session_state.pydantic_letter.content = updated_content
                    st.session_state.pydantic_letter.subject = subject

                    from src.postulator.tools.custom_tool import letter_writer
                    latex_letter = letter_writer._letter_from_pydantic(pydantic_letter)
                    st.session_state.latex_letter = latex_letter

                    # Compile the updated letter
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
                        print(f"Error writing to file: {str(e)}")

                    st.session_state.edit_mode = False

                    st.rerun()

if __name__ == "__main__":
    app()