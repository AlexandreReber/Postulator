# Standard library imports
import json
import os
import unicodedata
from pathlib import Path
from random import randint
from typing import Dict, Any, Tuple, Optional

# Third-party imports
import google.generativeai as genai
import streamlit as st
from pydantic import ValidationError

# Local imports
from src.postulator.data_structures.custom_data_structures import CV

def contains_special_characters(text: str) -> bool:
    """
    Check if a string contains special characters (non-ASCII characters).
    Returns True if special characters are found, False otherwise.
    """
    import unicodedata
    return any(not c.isascii() for c in text)

def validate_api_key(api_key):
    """Check if the provided Google Gemini API key is valid.
    
    Args:
        api_key: User's API key for authentication
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    
    if contains_special_characters(api_key):
        return False, "API key cannot contain special characters"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Test the API key with a simple generation request
        response = model.generate_content("Test")
        if response:
            return True, "API key is valid"
        return False, "Unable to generate content with the provided API key"
    except Exception as e:
        error_message = str(e).lower()
        if "invalid api key" in error_message:
            return False, "Invalid API key format"
        elif "unauthorized" in error_message:
            return False, "Invalid API key: unauthorized access"
        else:
            return False, f"API key validation failed: {str(e)}"

def save_json_to_file(json_data, file_path):
    """
    Save a JSON object to a file.

    :param json_data: The JSON object to save.
    :param file_path: The path to the file where the JSON object will be saved.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        print(f"JSON data successfully saved to {file_path}")
    except Exception as e:
        print(f"An error occurred while saving the JSON data: {e}")
        

def read_json_from_file(file_path):
    """
    Read a JSON file and return its contents as a Python dictionary.

    :param file_path: The path to the JSON file to read.
    :return: The contents of the JSON file as a Python dictionary.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        print(f"JSON data successfully read from {file_path}")
        return data
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"The file {file_path} is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred while reading the JSON file: {e}")


def load_json_into_pydantic(file_path, model):
    """
    Load a JSON file and parse it into a Pydantic model.

    :param file_path: The path to the JSON file to read.
    :param model: The Pydantic model to parse the JSON data into.
    :return: An instance of the Pydantic model with the JSON data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        print(f"JSON data successfully read from {file_path}")

        # Parse the JSON data into the Pydantic model
        pydantic_object = model(**data)
        print("JSON data successfully loaded into Pydantic model")
        return pydantic_object
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"The file {file_path} is not a valid JSON file.")
    except ValidationError as e:
        print(f"Validation error while parsing JSON data: {e}")
    except Exception as e:
        print(f"An error occurred while reading the JSON file: {e}")

def load_from_gsheet(conn, api_key):
    """Load user data from Google Sheets.
    
    Args:
        conn: Google Sheets connection object
        api_key: User's API key for authentication
    """
    if not st.session_state.api_key_provided:
        return

    # try to load data from the sheet
    with st.empty():
        df = conn.read(worksheet="Feuille 1", usecols=list(range(8)), ttl=0)
    df = df[df["Key"] == api_key]

    if not df.empty:
        st.session_state.sender_name = df["Name"].iloc[0]
        st.session_state.sender_email = df["Email"].iloc[0]
        st.session_state.sender_address = df["Address"].iloc[0]
        st.session_state.sender_phone = ( df["Phone"].iloc[0] ).replace("start","")
        st.session_state.personal_writeup = ( df["Write-up"].iloc[0] ).replace("empty", "")

        print(df)
    
    else:
        st.session_state.sender_name = ""
        st.session_state.sender_email = ""
        st.session_state.sender_address = ""
        st.session_state.sender_phone = ""
        st.session_state.personal_writeup = ""

    with st.empty():
        df = conn.read(worksheet="Feuille 2", usecols=list(range(3)), ttl=0)
    df = df[df["Key"] == api_key]

    if not df.empty:
        st.session_state.cv_text = df["CV text"].iloc[0].replace("empty", "")

        if st.session_state.cv_text:
            print(st.session_state.cv_text)
            from random import randint
            file_path = os.path.join("input", str(randint(0,100)) + "extended_resume.md")
            with open(file_path, "w") as f:
                f.write(st.session_state.cv_text)
            # Store the file path in session state for later use
            st.session_state.cv_path = file_path

        try:
            st.session_state.cv_pydantic = CV.model_validate_json( df["CV pydantic"].iloc[0] )
        except Exception as e:
            print(e)
            st.session_state.cv_pydantic = ""

        print(df)
    
    else:
        st.session_state.cv_text = ""
        st.session_state.cv_pydantic = None


def update_gsheet(conn, api_key, spreadsheet="Feuille 1"):
    """Update Google Sheets with user data.
    
    Args:
        conn: Google Sheets connection object
        api_key: User's API key for authentication
        spreadsheet: Sheet name to update ("Feuille 1" or "Feuille 2")
    """
    if not st.session_state.api_key_provided:
        return

    if spreadsheet=="Feuille 1":
        print(f"Update Feuille 1 for {api_key}")
        with st.empty():
            df = conn.read(worksheet="Feuille 1", usecols=list(range(6)), ttl=0)

        if df[df["Key"] == api_key].empty:
            df.loc[len(df)] = [api_key, 
                            st.session_state.sender_name, 
                            st.session_state.sender_email, 
                            st.session_state.sender_address, 
                            "start" + str( st.session_state.sender_phone ), 
                            st.session_state.personal_writeup if st.session_state.personal_writeup != "" else "empty",
                            ]
        else:
            df.loc[df[df["Key"] == api_key].index, "Name"] = st.session_state.sender_name
            df.loc[df[df["Key"] == api_key].index, "Email"] = st.session_state.sender_email
            df.loc[df[df["Key"] == api_key].index, "Address"] = st.session_state.sender_address
            df.loc[df[df["Key"] == api_key].index, "Phone"] = "start" + str( st.session_state.sender_phone )
            df.loc[df[df["Key"] == api_key].index, "Write-up"] = st.session_state.personal_writeup if st.session_state.personal_writeup != "" else "empty"
            
        conn.update(worksheet="Feuille 1", data=df)
    
    if spreadsheet=="Feuille 2":
        print(f"Update Feuille 2 for {api_key}")
        with st.empty():
            df = conn.read(worksheet="Feuille 2", usecols=list(range(3)), ttl=0)

        if df[df["Key"] == api_key].empty:
            df.loc[len(df)] = [api_key,
                            st.session_state.cv_text if st.session_state.cv_text != "" else "empty",
                            st.session_state.cv_pydantic.model_dump_json() if st.session_state.cv_pydantic else "empty",
                            ]
        else:
            df.loc[df[df["Key"] == api_key].index, "CV text"] = st.session_state.cv_text if st.session_state.cv_text != "" else "empty"
            df.loc[df[df["Key"] == api_key].index, "CV pydantic"] = st.session_state.cv_pydantic.model_dump_json() if st.session_state.cv_pydantic else "empty"
        
        conn.update(worksheet="Feuille 2", data=df)

def load_user_usage(conn, name):
    with st.empty():
        df = conn.read(worksheet="Feuille 3", usecols=list(range(5)), ttl=0)
    df = df[df["Name"] == name.lower().replace(" ", ",")]

    if not df.empty:
        st.session_state.user_usage = df["Usage"].iloc[0]
        print(df)
    
    else:
        st.session_state.user_usage = 0

def update_user_usage(conn, name):
    print(f"Update Feuille 3 for {name}")
    with st.empty():
        df = conn.read(worksheet="Feuille 3", usecols=list(range(5)), ttl=0)

    if df[df["Name"] == name.lower().replace(" ", ",")].empty:
        df.loc[len(df)] = [
                        st.session_state.sender_name.lower().replace(" ", ","), 
                        st.session_state.sender_email, 
                        st.session_state.sender_address, 
                        "start" + str( st.session_state.sender_phone ), 
                        st.session_state.user_usage,
                        ]
    else:
        df.loc[ df[df["Name"] == name.lower().replace(" ", ",")].index, "Usage"] = st.session_state.user_usage
    
    conn.update(worksheet="Feuille 3", data=df)