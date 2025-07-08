# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
Never use cat. Use less.

## Project Overview

This is the Mengshen (萌神) Pinyin Font project - an open source tool that generates Chinese fonts with automatic pinyin (phonetic) annotations. The project creates fonts that display pinyin above Chinese characters, with special support for homographs (多音字) - characters that have different pronunciations depending on context.

**Key Features:**
- Supports Simplified Chinese, Traditional Chinese, and Japanese characters
- Contextual pinyin replacement using OpenType GSUB tables
- Unicode IVS (Ideographic Variant Selector) support
- Two font styles: han_serif and handwritten

## Development Methodology

### Test-Driven Development (TDD)
This project follows strict TDD principles for all development and refactoring work. **ALWAYS** apply the Red-Green-Refactor cycle:

1. **🔴 Red**: Write failing tests first
2. **🟢 Green**: Write minimal code to pass tests  
3. **🔵 Refactor**: Improve code while keeping tests green

### TDD Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run security tests
python -m pytest tests/security/ -v

# Run specific test category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/performance/ --benchmark-only

# Watch tests during development
pytest-watch --clear
```

### Test Requirements
- **Unit test coverage**: 95%+ required
- **Security test coverage**: 100% for security-related code
- **Integration tests**: All major pipelines covered
- **Performance tests**: No regression allowed

### TDD Workflow for Font Development (Complete Pipeline)
```bash
# 1. 🔴 Red: Create characterization tests for existing functionality
python -m pytest tests/integration/test_font_output_baseline.py

# 2. 🔴 Red: Write tests for new feature/refactor  
python -m pytest tests/unit/test_new_feature.py  # Should fail (Red)

# 3. 🟢 Green: Implement minimal code to pass
# Edit source files...
python -m pytest tests/unit/test_new_feature.py  # Should pass (Green)

# 4. 🔵 Refactor: Improve code while keeping tests green
# Refactor source files...
python -m pytest tests/unit/ tests/security/  # All should pass

# 5. 🧪 Pipeline: Complete pipeline validation
# Dictionary generation
cd res/phonics/duo_yin_zi/scripts/
python make_pattern_table.py

cd ../../unicode_mapping_table/  
python make_unicode_pinyin_map_table.py

# Font generation
cd ../../../..
python src/main.py -t han_serif
python src/main.py -t handwritten

# 6. 🎯 Integration: Run full test suite
python -m pytest tests/ --cov=src

# 7. ✅ Validation: Verify no regression
python -m pytest tests/integration/test_complete_pipeline.py
```

## Build Commands

### Font Generation
```bash
# Generate han_serif font (default)
python3 src/main.py

# Generate handwritten font  
python3 src/main.py -t handwritten

# Time the build process
time python3 src/main.py
```

### Dependencies Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install external dependencies (macOS)
brew tap caryll/tap
brew install otfcc-mac64
brew install jq
```

### Pattern Table Generation
```bash
# Generate homograph pattern tables
cd res/phonics/duo_yin_zi/scripts
python3 make_pattern_table.py
```

## Architecture Overview

### Core Pipeline
The font generation follows this pipeline:
1. **Font Dumping**: Convert base fonts (TTF) to editable JSON using otfcc
2. **Pinyin Processing**: Generate pinyin glyphs and pronunciation mappings
3. **Glyph Integration**: Combine base font glyphs with pinyin glyphs
4. **GSUB Table Generation**: Create contextual replacement rules for homographs
5. **Font Assembly**: Build final TTF font from modified JSON

### Key Components

**Main Entry Point:**
- `src/main.py` - CLI interface and font generation orchestration

**Core Font Processing:**
- `src/font.py` - Main Font class that orchestrates the entire build process
- `src/config.py` - Font type definitions and metadata (canvas sizes, tracking)
- `src/pinyin_glyph.py` - Pinyin glyph generation and alphabet processing
- `src/GSUB_table.py` - OpenType GSUB table generation for contextual replacement

**Data Processing:**
- `src/pinyin_getter.py` - Unicode to pinyin mapping and web scraping
- `src/utility.py` - Utility functions for character and glyph operations
- `res/phonics/unicode_mapping_table/` - Unicode to pinyin mapping tables
- `res/phonics/duo_yin_zi/` - Homograph pattern definitions and processing

**External Tool Integration:**
- `src/shell.py` - ⚠️ Shell command execution (contains security vulnerabilities)
- `src/make_template_jsons.py` - Font to JSON conversion using otfcc
- `src/retrieve_latin_alphabet.py` - Latin alphabet extraction for pinyin

### Font Styles and Configuration

The system supports two font styles defined in `src/config.py`:
- **HAN_SERIF_TYPE (1)**: Uses Source Han Serif + M+ fonts
- **HANDWRITTEN_TYPE (2)**: Uses Xiaolai Font + SetoFont

Each style has specific canvas dimensions and tracking settings for optimal pinyin display.

### Homograph Processing

The project implements sophisticated homograph (多音字) handling:
- **Pattern One**: Single character pronunciation changes in phrases
- **Pattern Two**: Multiple character pronunciation changes  
- **Exception Patterns**: Manual overrides for special cases

Pattern files are located in `res/phonics/duo_yin_zi/` and processed by scripts in the `scripts/` subdirectory.

## File Structure

**Input Assets:**
- `res/fonts/han-serif/` - Source Han Serif base fonts
- `res/fonts/handwritten/` - Handwritten style base fonts
- `res/phonics/` - Pinyin and homograph data

**Generated Outputs:**
- `outputs/` - Final TTF font files and pattern tables
- `tmp/json/` - Intermediate JSON representations of fonts

**Tools:**
- `tools/` - Utility scripts for font conversion and analysis

## Important Notes

### TDD Development Rules
**MANDATORY**: All code changes must follow TDD methodology:

1. **Never write production code without a failing test first**
2. **Write only enough test code to demonstrate a failure**  
3. **Write only enough production code to make the failing test pass**
4. **Refactor both test and production code while keeping tests passing**

### Security Warning (TDD Priority)
The `src/shell.py` file contains a critical security vulnerability with `subprocess.run(cmd, shell=True)`. 

**TDD Fix Approach**:
```bash
# 1. Write security tests first (Red)
def test_no_shell_injection_vulnerability():
    assert not contains_shell_true("src/shell.py")

# 2. Fix implementation (Green)  
# 3. Refactor safely (Blue)
```

This allows arbitrary command injection and must be fixed using TDD before any other work.

### External Dependencies
- **otfcc**: Font parsing and generation (required)
- **jq**: JSON processing (required)
- Python packages listed in requirements.txt

### Font Sources
- Source Han Serif CN Regular (han_serif style)
- M+ M Type-1 medium (pinyin for han_serif)
- Xiaolai MonoSC (handwritten style)
- SetoFont SP (pinyin for handwritten)

### Character Coverage
- Simplified Chinese: Based on Table of General Standard Chinese Characters
- Traditional Chinese: Based on Big-5-2003 standard  
- Japanese: Based on Jōyō kanji list
- Includes hiragana and katakana support

## Refactoring Guidelines

### TDD-First Refactoring
For detailed refactoring strategy and modernization plans, see `REFACTOR.md`. **ALL refactoring must follow TDD principles**:

**TDD Refactoring Process**:
1. **Create characterization tests** for existing behavior
2. **Write tests for desired new behavior** (Red)
3. **Refactor incrementally** while keeping tests green
4. **Ensure no regression** in font output quality

### Refactoring Phases (TDD-Driven)
- **Phase 1**: Security fixes with security tests first
- **Phase 2**: Python 3.11+ migration with modernization tests
- **Phase 3**: Data structure improvements with type safety tests
- **Phase 4**: Architecture refactoring with integration tests  
- **Phase 5**: Performance optimization with benchmark tests
- **Phase 6**: Pinyin data integration with data consistency tests
- **Phase 7**: Docker containerization with deployment tests

**Critical TDD Rule**: No phase can be considered complete without:
- [ ] 🔴 All tests written and initially failing
- [ ] 🟢 All tests passing with implementation
- [ ] 🔵 Code refactored to high quality
- [ ] 🧪 Complete pipeline validation (dictionary + font generation)
- [ ] 🎯 Integration tests passing
- [ ] ✅ No regression in output quality
- [ ] 95%+ test coverage achieved

**Pipeline Validation Commands** (must pass for each phase):
```bash
# Quick pipeline validation
cd res/phonics/duo_yin_zi/scripts && python make_pattern_table.py
cd ../../unicode_mapping_table && python make_unicode_pinyin_map_table.py  
cd ../../../.. && python src/main.py -t han_serif

# Full validation
python -m pytest tests/integration/test_complete_pipeline.py -v
```

## Refactoring Documentation Requirements

### REFACTOR.md Update Policy
**MANDATORY**: When completing any refactoring work, you MUST update `REFACTOR.md` to reflect the current status:

1. **Phase Status Updates**: Change phase status from "未着手" → "🔄 実装中" → "✅ 完了"
2. **Implementation Details**: Update code examples to reflect actual implementation
3. **Completion Criteria**: Mark completed items with ✅ and update checklists
4. **Benefits Documentation**: Update benefits section to reflect actual improvements achieved
5. **File Changes**: Document specific files modified and their new functionality

### Required Updates After Each Phase
```markdown
**Phase X: [Name]** ✅ 完了
**状態**: ✅ 完了

**実装完了状況:**
- [x] Task 1 ✅ (具体的な変更内容)
- [x] Task 2 ✅ (修正されたファイル名)
- [x] Task 3 ✅ (テスト結果)

**実装したアプローチのメリット**:
- **セキュリティ**: 具体的なセキュリティ改善
- **パフォーマンス**: 測定可能な改善結果
- **保守性**: 実装された改善内容
```

### Documentation Workflow
1. **開始時**: Phase status を "🔄 実装中" に更新
2. **実装完了時**: 実装内容を詳細に記録
3. **テスト完了時**: 検証結果とメリットを更新  
4. **Phase完了時**: 全チェックボックスを ✅ に変更

**Critical Rule**: リファクタリング作業完了後は必ず `REFACTOR.md` を最新状態に更新してください。これにより、プロジェクトの進捗と現在の実装状況を正確に把握できます。