import os
import re
import json
import csv
from pypdf import PdfReader
from docx import Document
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
class DataIngestionPipeline:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size        
        self.chunk_overlap = chunk_overlap
    def clean_text(self, text):
        """Normalizes text by clearing blank lines, extra spaces, and weird artifacts."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.,;:!?@\'\"\-\[\]`\(\)]', '', text)
        return text.strip()
    def split_into_chunks(self, text):
        """Splits text into chunks of configurable sizes with an optional rolling overlap."""
        chunks = []
        start = 0
        text_length = len(text)
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += self.chunk_size - self.chunk_overlap
            if self.chunk_size <= self.chunk_overlap:
                break
                
        return chunks
    def parse_txt_or_md(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def parse_pdf(self, file_path):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

    def parse_docx(self, file_path):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def parse_csv(self, file_path):
        text_lines = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                text_lines.append(" ".join(row))
        return "\n".join(text_lines)
    def process_file(self, file_path, metadata=None):
        """Parses, cleans, and chunks an individual file."""
        ext = os.path.splitext(file_path)[1].lower()
        raw_text = ""

        try:
            if ext in ['.txt', '.md']:
                raw_text = self.parse_txt_or_md(file_path)
            elif ext == '.pdf':
                raw_text = self.parse_pdf(file_path)
            elif ext == '.docx':
                raw_text = self.parse_docx(file_path)
            elif ext == '.csv':
                raw_text = self.parse_csv(file_path)
            else:
                print(f"[INGEST SKIP] Unsupported format: {ext}")
                return []
        except Exception as e:
            print(f"[INGEST ERROR] Failed to parse {file_path}: {e}")
            return []

        cleaned_text = self.clean_text(raw_text)
        chunks = self.split_into_chunks(cleaned_text)
        processed_chunks = []
        for i, chunk_text in enumerate(chunks):
            parent_folder = os.path.basename(os.path.dirname(file_path))
            file_name = os.path.basename(file_path)
            
            processed_chunks.append({
                "chunk_id": f"{parent_folder}_{file_name}_chunk_{i}",
                "text": chunk_text,
                "metadata": metadata or {}
            })
        return processed_chunks

    def scan_and_ingest_data_vault(self):
        """Scans the data directory for documents and companion metadata JSONs."""
        all_processed_chunks = []
        print("==========================================")
        print(" Starting Ingestion & Normalization Engine")
        print("==========================================\n")
        for root, dirs, files in os.walk(DATA_DIR):
            metadata = {}
            if "metadata.json" in files:
                try:
                    with open(os.path.join(root, "metadata.json"), "r", encoding="utf-8") as mj:
                        metadata = json.load(mj)
                except Exception as e:
                    print(f"[METADATA ERROR] Could not read metadata in {root}: {e}")
            for file in files:
                if file in ["metadata.json", ".gitkeep", "synth_data.py"]:
                    continue 
                file_path = os.path.join(root, file)
                print(f"[PROCESSING] Ingesting: data/{os.path.relpath(file_path, DATA_DIR)}")
                
                chunks = self.process_file(file_path, metadata=metadata)
                all_processed_chunks.extend(chunks)
        output_vault_path = os.path.join(DATA_DIR, "processed_vault.json")
        with open(output_vault_path, "w", encoding="utf-8") as out_f:
            json.dump(all_processed_chunks, out_f, indent=4)

        print(f"\nPipeline Complete! Stored {len(all_processed_chunks)} normalized chunks inside data/processed_vault.json")

if __name__ == "__main__":
    pipeline = DataIngestionPipeline(chunk_size=500, chunk_overlap=50)
    pipeline.scan_and_ingest_data_vault()