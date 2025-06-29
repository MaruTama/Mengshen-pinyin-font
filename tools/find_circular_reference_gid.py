import json

def load_glyphs(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data.get('glyf', {})

def detect_circular_references(glyphs):
    def visit(glyph, path):
        if glyph in path:
            return path[path.index(glyph):]  # Circular reference detected
        if glyph not in glyphs or 'references' not in glyphs[glyph]:
            return None
        path.append(glyph)
        for reference in glyphs[glyph]['references']:
            result = visit(reference['glyph'], path)
            if result:
                return result
        path.pop()
        return None

    circular_references = []
    for glyph in glyphs:
        path = []
        result = visit(glyph, path)
        if result:
            circular_references.append(result)
    return circular_references

# Load glyphs from JSON file
file_path = '../tmp/json/template.json'  # ファイルパスを適宜変更してください
glyphs = load_glyphs(file_path)

# Detect circular references
circular_references = detect_circular_references(glyphs)

# Output the results
if circular_references:
    print("Circular references detected:")
    for cycle in circular_references:
        print(" -> ".join(cycle))
else:
    print("No circular references detected.")