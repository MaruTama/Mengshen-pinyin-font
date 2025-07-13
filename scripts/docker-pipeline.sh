#!/bin/bash
set -e

echo "🚀 Starting Mengshen Font Generation Pipeline (Refactored Version)"
echo "=================================================="

# Function to print status
print_status() {
    echo "📋 $1"
}

# Function to print error
print_error() {
    echo "❌ ERROR: $1" >&2
}

# Function to print success
print_success() {
    echo "✅ $1"
}

cd /app

print_status "Step 1: Generating pattern tables..."
cd res/phonics/duo_yin_zi/scripts/
python make_pattern_table.py
print_success "Pattern tables generated"

print_status "Step 2: Generating Unicode mapping tables..."
cd ../../unicode_mapping_table/
python make_unicode_pinyin_map_table.py
print_success "Unicode mapping tables generated"

cd /app

print_status "Step 3: Creating template JSONs..."
print_status "  - Creating han_serif template..."
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style han_serif
print_success "han_serif template created"

print_status "  - Creating handwritten template..."
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style handwritten  
print_success "handwritten template created"

print_status "Step 4: Extracting Latin alphabets..."
print_status "  - Extracting for han_serif..."
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style han_serif
print_success "han_serif Latin alphabets extracted"

print_status "  - Extracting for handwritten..."
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style handwritten
print_success "handwritten Latin alphabets extracted"

print_status "Step 5: Generating fonts..."
print_status "  - Generating han_serif font..."
PYTHONPATH=src python -m refactored.cli.main -t han_serif
print_success "han_serif font generated"

print_status "  - Generating handwritten font..."
PYTHONPATH=src python -m refactored.cli.main -t handwritten
print_success "handwritten font generated"

print_success "🎉 All fonts generated successfully!"
echo "=================================================="
echo "Generated files can be found in:"
echo "  - ./outputs/Mengshen-HanSerif.ttf"
echo "  - ./outputs/Mengshen-Handwritten.ttf"
echo "=================================================="