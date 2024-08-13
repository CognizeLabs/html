import csv
import re
from intent_classifier import process_email  # Import the function from intent_classifier.py

# Function to clean the email content
def clean_text(text: str) -> str:
    # Remove \r\n, \n\n, and other repeated newlines
    text = re.sub(r'[\r\n]+', ' ', text)
    # Replace any other multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Read the CSV file, process the data, and write to a new CSV
def process_csv(input_file: str, output_file: str):
    with open(input_file, mode='r', newline='', encoding='utf-8') as infile, \
         open(output_file, mode='w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["emailContent", "caseCategory", "caseUrgency", "sentiment", "confidence"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in reader:
            # Clean and combine email subject and body
            subject = clean_text(row['emailContentSubject'])
            body = clean_text(row['emailContentBody'])
            
            # Format the email content with "Details" on a new line
            combined_content = f"Subject: {subject}\nDetails: {body}"

            # Call the process_email function from intent_classifier.py
            processed_data = process_email(subject, body)

            # Update the row with new data
            row["emailContent"] = combined_content
            row.update(processed_data)

            # Write the updated row to the new CSV
            writer.writerow(row)

# Usage
input_csv = 'input.csv'  # Path to your input CSV file
output_csv = 'output.csv'  # Path to your output CSV file
process_csv(input_csv, output_csv)
