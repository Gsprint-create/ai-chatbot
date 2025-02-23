#!/bin/bash
# Install Tesseract-OCR on Render
apt-get update && apt-get install -y tesseract-ocr
pip install -r requirements.txt
