# Postulator - AI-Powered Cover Letter Generator ✍️

Postulator is a web application that leverages Google's Gemini AI to generate personalized cover letters. Built with Streamlit, it offers an intuitive interface for creating professional cover letters based on your CV and job requirements.

## Online version

The app is hosted using Streamlit Community Cloud ; you can use it for free [here](https://postulator.streamlit.app/).

## Our Mission

Postulator is committed to democratizing access to professional job application materials. We believe that everyone deserves an equal opportunity to present themselves effectively in the job market, regardless of their background, writing experience, or socioeconomic status. Our AI-powered platform helps level the playing field by:

- 🎯 Providing high-quality writing assistance to all job seekers
- 🌍 Breaking down language and communication barriers
- 💪 Empowering candidates from diverse backgrounds to compete fairly

## Features

- 🤖 AI-powered cover letter generation using Google's Gemini API
- 📄 CV parsing and management
- 🌐 Bilingual support (English and French)
- 🎨 Modern, responsive user interface
- 📝 Interactive CV builder
- 📊 PDF preview and export functionality

## Prerequisites

- Python 3.12
- Google Gemini API key (free from Google AI Studio)
- Google Sheets API credentials (for data storage)
- Serper API key (free tier available)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd postulator
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment:
- Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Configure your Google Sheets credentials and provide API keys in `.streamlit/secrets.toml` using the example provided in `structure_secrets.toml`. (For now a connection to a google drive sheet is required, no local version is provided)

## Usage

1. Start the application:
```bash
streamlit run main.py
```

2. Enter your Google Gemini API key
3. Upload your CV or use the interactive CV builder
4. Input job details and preferences
5. Generate and customize your cover letter
6. Export the final letter in PDF format

## Project Structure

```
├── src/
│   └── postulator/
│       ├── config                  # AI agent configuration
│       │    └── ....yaml           # Description of agents and tasks
│       ├── data_structures         # AI agent configuration
│       │    └── ....py             # Custom pydantic data structure definition
│       ├── tools                   # AI agent configuration
│       │    └── custom_tools.py    # Custom tools definition
│       ├── app.py                  # Main Streamlit application
│       ├── crew.py                 # Crews of AI agent configuration
│       ├── translations.py         # Multilingual support
│       └── utils.py                # Helper functions
├── input/                          # CV templates and examples
├── output/                         # Generated letters and PDFs
└── requirements.txt                # Project dependencies
```

## Features in Detail

### CV Management
- Upload existing CV in PDF format
- Interactive CV builder with structured sections
- Automatic CV parsing and data extraction

### Cover Letter Generation
- AI-powered content generation
- Professional formatting
- Multiple language support
- PDF export functionality

### User Interface
- Clean, intuitive design
- Responsive layout
- Real-time preview
- Progress tracking

## License

See the LICENSE file for details.