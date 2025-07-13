# Gemini Development Guidelines for Mengshen Pinyin Font

This document provides instructions for Gemini on how to perform key verification tasks within this repository.

## Verifying Functional Equivalence of Refactored Architecture

To ensure that the refactored architecture in `src/mengshen_font` maintains functional equivalence with the legacy code, you must verify that both implementations produce binary-identical font files.

Follow these steps for verification:

### Step 1: Generate Baseline Font from Legacy Code

First, generate the font file using the original legacy implementation. This will serve as the trusted baseline for comparison. After generation, copy the output to the `baselines` directory.

```bash
# Generate the font using the legacy entry point
python src/main.py -t han_serif

# Copy the generated font to the baselines directory for safekeeping
cp outputs/Mengshen-HanSerif.ttf baselines/legacy_han_serif_baseline.ttf
```

### Step 2: Generate Font from Refactored Architecture

Next, generate the font file using the new, refactored architecture's entry point.

```bash
# Generate the font using the new architecture's entry point
python -m src.mengshen_font.cli.main -t han_serif

# Copy the generated font to the baselines directory for comparison
cp outputs/Mengshen-HanSerif.ttf baselines/refactored_current.ttf
```

### Step 3: Perform Binary-Level Verification

Finally, perform a binary comparison of the two generated font files. The `cmp` command is used for this purpose. If the files are identical, the command will produce no output and exit with a status code of 0. Any output indicates a discrepancy between the two files.

```bash
# Compare the baseline and the refactored output.
# No output from this command means the files are identical.
cmp baselines/legacy_han_serif_baseline.ttf baselines/refactored_current.ttf
```

**Success Criterion:** The `cmp` command must produce no output. This confirms that the refactoring has not introduced any regressions and that the new architecture is functionally equivalent to the legacy one.

## Detailed Analysis of Font Differences

If the binary-level verification (Step 3 above) indicates a difference, you can perform a more detailed analysis to pinpoint the exact discrepancies within the font tables. This involves dumping the font files to JSON and comparing specific sections.

### Step 1: Dump Fonts to JSON

Use `otfccdump` to convert both the legacy and refactored font files into human-readable JSON format.

```bash
# Dump the legacy font to JSON
otfccdump baselines/legacy_han_serif_baseline.ttf --pretty -o tmp/legacy_han_serif_baseline.json

# Dump the refactored font to JSON
otfccdump baselines/refactored_current.ttf --pretty -o tmp/refactored_current.json
```

### Step 2: Compare Specific Font Tables

You can use `jq` to extract specific tables (e.g., `glyf` for glyph data, `cmap` for character-to-glyph mappings, `head` for font metadata) from the JSON dumps and then compare them using `diff`.

#### Comparing the `glyf` Table (Glyph Data)

The `glyf` table contains the actual outlines of the glyphs. Differences here indicate changes in how glyphs are constructed or included.

```bash
# Extract glyf table from legacy font JSON
jq '.glyf' tmp/legacy_han_serif_baseline.json > tmp/legacy_glyf.json

# Extract glyf table from refactored font JSON
jq '.glyf' tmp/refactored_current.json > tmp/refactored_glyf.json

# Compare the glyf tables
diff -u tmp/legacy_glyf.json tmp/refactored_glyf.json > tmp/glyf_diff.txt
```

#### Comparing the `cmap` Table (Character-to-Glyph Mappings)

The `cmap` table maps character codes to glyph IDs. Differences here might indicate changes in character support or how glyphs are referenced.

```bash
# Extract cmap table from legacy font JSON
jq '.cmap' tmp/legacy_han_serif_baseline.json > tmp/legacy_cmap.json

# Extract cmap table from refactored font JSON
jq '.cmap' tmp/refactored_current.json > tmp/refactored_cmap.json

# Compare the cmap tables
diff -u tmp/legacy_cmap.json tmp/refactored_cmap.json > tmp/cmap_diff.txt
```

#### Comparing the `head` Table (Font Header Metadata)

The `head` table contains general information about the font, such as creation/modification dates, bounding box, and units per em.

```bash
# Extract head table from legacy font JSON
jq '.head' tmp/legacy_han_serif_baseline.json > tmp/legacy_head.json

# Extract head table from refactored font JSON
jq '.head' tmp/refactored_current.json > tmp/refactored_head.json

# Compare the head tables
diff -u tmp/legacy_head.json tmp/refactored_head.json > tmp/head_diff.txt
```

### Step 3: Analyze the Difference Files

After running the comparison commands, examine the generated `_diff.txt` files (e.g., `tmp/glyf_diff.txt`, `tmp/cmap_diff.txt`, `tmp/head_diff.txt`). These files will show the line-by-line differences between the corresponding tables.

*   **Large diff files:** If the diff files are very large, you might need to use `head`, `tail`, `grep`, or other command-line tools to narrow down the areas of interest.
*   **Interpreting differences:**
    *   Differences in `glyf` often mean changes in glyph outlines or components.
    *   Differences in `cmap` mean changes in which characters are supported or how they map to glyphs.
    *   Differences in `head` or other metadata tables might be due to build environment (timestamps, tool versions) or intentional changes in font properties.

By systematically comparing these tables, you can identify the root cause of the binary differences and determine if they are intentional (e.g., due to new features) or unintentional regressions.
