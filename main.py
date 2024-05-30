import streamlit as st
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import fitz  # PyMuPDF
import spacy
from dotenv import load_dotenv
import os

load_dotenv()


API_KEY = os.getenv("api_key")
API_KEY = API_KEY.replace(';','')
YOUTUBE_API_SERVICE_NAME = os.getenv("YOUTUBE_API_SERVICE_NAME")
YOUTUBE_API_VERSION = os.getenv("YOUTUBE_API_VERSION")


# Load spaCy model
nlp = spacy.load('en_core_web_sm')

def get_content_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headers = ' '.join(h.get_text() for h in soup.find_all(['h1', 'h2', 'h3']))
        paragraphs = ' '.join(p.get_text() for p in soup.find_all('p'))
        
        content = headers * 3 + ' ' + paragraphs
        return content
    except Exception as e:
        st.error(f"Error fetching content from URL: {e}")
        return None

def get_content_from_pdf(file):
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return None

import re

def preprocess_text(text):
    # Convert text to lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    return text

def summarize_text_spacy(text):
    try:
        # Preprocess the text
        text = preprocess_text(text)
        
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        sentences = sorted(sentences, key=lambda x: len(x), reverse=True)
        
        summary = ' '.join(sentences[:5])
        
        return summary
    except Exception as e:
        st.error(f"Error summarizing text with spaCy: {e}")
        return text


def search_youtube_videos(query):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=6
    ).execute()
    
    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append({
                'title': search_result['snippet']['title'],
                'url': f"https://www.youtube.com/watch?v={search_result['id']['videoId']}",
                'embed_url': f"https://www.youtube.com/embed/{search_result['id']['videoId']}",
                'thumbnail': search_result['snippet']['thumbnails']['high']['url']
            })
    return videos


def main():
    st.set_page_config(layout="wide")
    st.title("YouTube Video Recommender and Summarizer")
    st.sidebar.header("How to Use")
    st.sidebar.markdown("1. **Enter URL**: Paste the URL of the website from which you want to extract content or Upload the pdf file (not more than 25mb)")
    st.sidebar.markdown("2. **Get Recommendations**: Click the button to extract content from the URL and get recommended YouTube videos.")
    st.sidebar.markdown("3. **View Recommendations**: Scroll down to see the recommended YouTube videos based on the extracted content.")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Your feedback to improve the system is always welcomed :)**")
    st.sidebar.markdown("Feel free to reach out to us through the contact form below.")
    st.sidebar.markdown("[About Me](https://janakpariyar.com.np)")

    
    st.markdown("<h3>Choose input type:</h3>", unsafe_allow_html=True)
    input_option = st.radio("Choose input type:", ["URL", "PDF Upload"], key="input_option")
    
    if input_option == "URL":
        url = st.text_input("Enter the URL of the website:")
        if st.button("Get Recommendations"):
            content = get_content_from_url(url)
            if content:
                st.write("Extracted Content:", content[:500] + "...")
                summarized_content = summarize_text_spacy(content)
                st.write("Summarized Content:", summarized_content[:200])
                
                videos = search_youtube_videos(summarized_content)
                if videos:
                    st.header("Recommended YouTube Videos:")
                    col1, col2, col3 = st.columns(3)
                    for i, video in enumerate(videos):
                        with [col1, col2, col3][i % 3]:
                            st.write(f"""
                                <div style='margin: 10px; width: 100%;'>
                                    <iframe width="100%" height="200" src="{video['embed_url']}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                                    <h4 style='text-align: center;'>{video['title']}</h4>
                                </div>
                            """, unsafe_allow_html=True)

    elif input_option == "PDF Upload":
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
        if st.button("Get Recommendations") and uploaded_file is not None:
            content = get_content_from_pdf(uploaded_file)
            if content:
                st.write("Extracted Content:", content[:500] + "...")
                summarized_content = summarize_text_spacy(content)
                st.write("Summarized Content:", summarized_content)
                
                videos = search_youtube_videos(summarized_content)
                if videos:
                    st.header("Recommended YouTube Videos:")
                    col1, col2, col3 = st.columns(3)
                    for i, video in enumerate(videos):
                        with [col1, col2, col3][i % 3]:
                            st.write(f"""
                                <div style='margin: 10px; width: 100%;'>
                                    <iframe width="100%" height="200" src="{video['embed_url']}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                                    <h4 style='text-align: center;'>{video['title']}</h4>
                                </div>
                            """, unsafe_allow_html=True)

    
    # Apply CSS for better styling and responsiveness
    st.markdown("""
        <style>
        .stApp {
            padding: 2rem;
        }
        img {
            border-radius: 10px;
        }
        h4 {
            font-size: 1.1rem;
            margin: 0.5rem 0;
        }
        @media (max-width: 768px) {
            .stImage {
                width: 100%;
                height: auto;
            }
        }
        /* Custom CSS for Query Submission Form */
        #contact {
            font-family: 'Roboto', sans-serif;
        }
        #contact h4 {
            color: #333;
            text-align: center;
        }
        #contact textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            outline: none;
            transition: border-color 0.3s ease;
            resize: vertical;
        }
        #contact textarea:focus {
            border-color: #3498db;
        }
        #contact button {
            display: block;
            width: 10%;
            padding: 12px 20px;
            margin-top: 20px;
            background-color: #3498db;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        #contact button:hover {
            background-color: #2980b9;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render the contact form HTML in the footer
    st.markdown(contact_form_html, unsafe_allow_html=True)

# Contact form HTML
contact_form_html = """
<section id="contact" class="bg-gray-200 p-8">
    <div class="container mx-auto">
        <h4 class="text-3xl font-bold mb-8">Help Me Improve</h4>
        <form action="https://formspree.io/f/moqgzbzy" method="POST" class="bg-white p-6 rounded-lg shadow-md">
            <div class="mb-6">
                <label for="message" class="block text-gray-700 font-bold mb-2">Message</label>
                <textarea id="message" name="message" rows="4" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"></textarea>
            </div>
            <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" style="width: 30%;">Submit</button>
        </form>
    </div>
</section>
"""

if __name__ == "__main__":
    main()
