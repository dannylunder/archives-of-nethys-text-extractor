import requests
from bs4 import BeautifulSoup
import time
import chardet
import pandas as pd

def decode_content(content):
    """
    Attempt to decode content using multiple encodings.
    
    Args:
    - content (bytes): The raw byte content.

    Returns:
    - str: Decoded text content.
    """
    encodings = ['utf-8', 'latin-1', 'ISO-8859-1', 'windows-1252']
    
    for encoding in encodings:
        try:
            decoded_content = content.decode(encoding)
            if "\uFFFD" not in decoded_content:
                return decoded_content
        except (UnicodeDecodeError, TypeError):
            continue
    
    # Return raw bytes as a string if all decodings fail
    return content.decode('utf-8', errors='ignore')

def get_all_text_from_webpage(url, retries=3, delay=0.1):
    """
    Fetches and extracts all text from a webpage, with retries on failure and encoding handling.
    
    Args:
    - url (str): The URL of the webpage to scrape.
    - retries (int): The number of retries on failure.
    - delay (float): The delay between retries in seconds.

    Returns:
    - str: Extracted text from the webpage, or None if failed.
    """
    for attempt in range(retries):
        try:
            response = requests.get(url)
            
            if response.status_code in [404, 500]:
                print(f"Error for URL: {url} (status code: {response.status_code})")
                return None

            detected_encoding = chardet.detect(response.content)['encoding']
            print(f"Detected encoding: {detected_encoding}")
            print(f'url: {url}')

            if detected_encoding is not None:
                try:
                    soup = BeautifulSoup(response.content, 'html.parser', from_encoding=detected_encoding)
                    all_text = soup.get_text(separator=' ', strip=True)
                    if "\uFFFD" not in all_text:
                        return all_text
                    else:
                        print("Detected encoding resulted in replacement characters.")
                except Exception as e:
                    print(f"Decoding with detected encoding failed: {e}")
            
            # If no encoding is detected, decode as raw bytes
            all_text = decode_content(response.content)
            return all_text

        except Exception as e:
            print(f"Attempt {attempt + 1} encountered an error: {e}")

        time.sleep(delay)
    
    return None

def prepare_for_print(df=None):
    if df is not None:
        # Split the description by hyphen and create new columns
        try:
            df[['description_part1', 'description_part2']] = df['description'].str.split(' - ', n=1, expand=True)
        except Exception as e:
            print(f'Error while preparing output for print: {e}')
    return df
    
def save_output(fname='output.csv', data=None):
    if data is None:
        return False
    try:
        data = prepare_for_print(df=data)
        data.to_csv(fname, index=False)
    except Exception as e:
        print(f'Error while printing output: {e}')
        return False
    return True


if __name__ == '__main__':

    # Base URL of the webpages to be scraped
    base_url = 'https://2e.aonprd.com/Monsters.aspx?ID='

    # Dictionary to store the text content of each page
    webpage_texts = {}

    # Attempt to scrape pages until a 404 or 500 error is encountered
    id = 1
    consecutive_failures = 0
    max_consecutive_failures = 500

    #creating the dataframe earlier and building it up over time to track the progress.
    data = {
            'ID': [],
            'description': []
            }

    df = pd.DataFrame(data)

    n = 20
    #while consecutive_failures < max_consecutive_failures:
    while consecutive_failures < max_consecutive_failures and id < n+1:
        url = f"{base_url}{id}"
        webpage_text = get_all_text_from_webpage(url)
        if webpage_text and len(webpage_text) > 10:  # Check if text is not too short to be nonsensical
            # webpage_texts[id] = webpage_text
            new_row = pd.DataFrame({'ID': [id], 'description': [webpage_text]})
            print(f"Successfully scraped ID {id}")
            consecutive_failures = 0
        else:
            new_row = pd.DataFrame({'ID': [id], 'description': ["ERROR WHILE PROCESSING DESCRIPTION - ERROR WHILE PROCESSING DESCRIPTION"]})
            print(f"Failed to scrape ID {id}")
            consecutive_failures += 1

        df = pd.concat([df, new_row], ignore_index=True)

        if save_output(fname=f'data/individual_result_for_{id}.csv', data=new_row.copy()):
            print(f'Saved individual result for {id} to data/individual_result_for_{id}.csv')
        else:
            print(f'Unable to save individual result for {id} to data/individual_result_for_{id}.csv')

        if id % 10 == 0:
            if save_output(fname=f'data/results_after_{id}.csv', data=df.copy()):
                print(f'Saved intermediate result for {id} to data/results_after_{id}.csv')
            else:
                print(f'Unable to save intermediate result for {id} to data/results_after{id}.csv')
        
        id += 1

    if save_output(fname=f'data/final_results.csv', data=df.copy()):
        print('Saved final result to data/final_results.csv')
    else:
        print('Unable to save final result to data/final_results.csv')
    # # Create a DataFrame from the scraped data
    # data = {
    #     'ID': list(webpage_texts.keys()),
    #     'description': list(webpage_texts.values())
    # }

    # df = pd.DataFrame(data)

    df = prepare_for_print(df)

    print(df)
