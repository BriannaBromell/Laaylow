# reword_descriptions.py
import os
from openai import OpenAI
import configparser
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import re

# Configuration file name
config_file = 'config.txt'
default_prompt = (
    "Instructions: Reword the following text while preserving all HTML tags and structure. "
    "Only modify the text content within <p> and </p> tags. Do not alter or remove any HTML tags, attributes, or other markup. "
    "Ensure the output is valid HTML and retains the original structure."
)

# Load configuration
config = configparser.ConfigParser()

# Create default config if it doesn't exist
if not os.path.exists(config_file):
    config['DEFAULT'] = {
        'OpenAI': 'False',
        'OpenAI_key': '',
        'prompt': default_prompt,
        'edit_post_paragraph': 'False'  # New setting
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print(f"Created '{config_file}' with default settings. Please edit this file.")

config.read(config_file)

# Get OpenAI setting
use_openai = config.getboolean('DEFAULT', 'OpenAI')

# Get API key if using OpenAI
openai_api_key = None
if use_openai:
    openai_api_key = config.get('DEFAULT', 'OpenAI_key').strip()
    if not openai_api_key:
        print("Warning: 'OpenAI_key' is empty in config.txt. OpenAI will likely fail.")
    client = OpenAI(api_key=openai_api_key)
    model_name = "gpt-3.5-turbo"  # You can change to other models if you have access
else:
    # Initialize local LLM pipeline
    try:
        print("Downloading and initializing a small language model (may take a few minutes)...")
        model_name = "google/flan-t5-base"  # Using T5 model for rephrasing
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        print("Local language model initialized.")
    except Exception as e:
        print(f"Error initializing local language model: {e}")
        use_openai = True  # Fallback to OpenAI if local fails
        print("Falling back to OpenAI. Please configure your API key in config.txt.")

# Get settings
prompt = config.get('DEFAULT', 'prompt')
edit_post_paragraph = config.getboolean('DEFAULT', 'edit_post_paragraph')  # New setting

output_reworded_folder = 'reworded_descriptions'
input_extracted_folder = 'extracted_descriptions'
max_length = 1024

def extract_and_reinsert_paragraphs(text, reword_function):
    """
    Extracts text between <p> and </p> tags, rewords it, and reinserts it.
    """
    # Find all <p>...</p> content
    paragraphs = re.findall(r'<p>(.*?)</p>', text, re.DOTALL)
    if not paragraphs:
        return text  # No <p> tags found, return original text

    # Reword each paragraph
    reworded_paragraphs = []
    for paragraph in paragraphs:
        # Ensure the paragraph is plain text (no HTML tags)
        plain_text = re.sub(r'<.*?>', '', paragraph)  # Remove any nested HTML tags
        reworded_paragraph = reword_function(plain_text.strip())
        if reworded_paragraph:
            reworded_paragraphs.append(reworded_paragraph)
        else:
            reworded_paragraphs.append(paragraph)  # Fallback to original if rewording fails

    # Reinsert reworded paragraphs into the original text
    def replace_paragraph(match):
        if reworded_paragraphs:
            return f"<p>{reworded_paragraphs.pop(0)}</p>"
        return match.group(0)  # Fallback to original if something goes wrong

    updated_text = re.sub(r'<p>.*?</p>', replace_paragraph, text, flags=re.DOTALL)
    return updated_text
def reword_description(text):
    """Rewords a single description using either OpenAI or a local LLM."""
    if use_openai:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.5,  # Adjust temperature
                max_tokens=max_length,  # Adjust max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error communicating with OpenAI: {e}")
            return None
    else:
        try:
            input_text = default_prompt + text
            input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)
            outputs = model.generate(input_ids, max_length=max_length, num_beams=5, early_stopping=True)
            reworded_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the "paraphrase: " prefix if it exists in the output
            if reworded_text.startswith("paraphrase: "):
                reworded_text = reworded_text[len("paraphrase: "):].strip()
            
            return reworded_text
        except Exception as e:
            print(f"Error using local language model: {e}")
            return None

def process_extracted_descriptions(input_folder, output_folder):
    """
    Reads each text file from the input folder, sends its content for rewording,
    and saves the reworded text to a new file in the output folder, sorted by row number.
    """
    os.makedirs(output_folder, exist_ok=True)
    extracted_files = [f for f in os.listdir(input_folder) if f.startswith("row_") and f.endswith(".txt")]

    def get_row_number(filename):
        try:
            parts = filename.split("_")
            return int(parts[1])
        except (IndexError, ValueError):
            return float('inf')  # Put files with parsing issues at the end

    sorted_files = sorted(extracted_files, key=get_row_number)

    for filename in sorted_files:
        input_filepath = os.path.join(input_folder, filename)
        output_filename = os.path.join(output_folder, filename)

        try:
            with open(input_filepath, 'r', encoding='utf-8') as infile:
                original_text = infile.read()

            print(f"Rewording: {filename} using {'OpenAI' if use_openai else 'Local LLM'}")
            if edit_post_paragraph:
                # Reword the entire text
                reworded_text = reword_description(original_text)
            else:
                # Extract, reword, and reinsert <p> content only
                reworded_text = extract_and_reinsert_paragraphs(original_text, reword_description)

            if reworded_text:
                with open(output_filename, 'w', encoding='utf-8') as outfile:
                    outfile.write(reworded_text)
                print(f"Saved reworded description to: {output_filename}")
            else:
                print(f"Failed to reword: {filename}")

        except FileNotFoundError:
            print(f"Error: Extracted file not found: {input_filepath}")
        except Exception as e:
            print(f"An error occurred processing {filename}: {e}")

if __name__ == "__main__":
    print("Starting the description rewording process...")
    print(f"Using prompt:\n{prompt}\n---")
    print(f"Edit post paragraph mode: {'Enabled' if edit_post_paragraph else 'Disabled'}")
    process_extracted_descriptions(input_extracted_folder, output_reworded_folder)
    print("Description rewording process completed. Reworded files are in the 'reworded_descriptions' folder.")