export interface PinyinCanvas {
  width: number
  height: number
  base_line: number
  tracking: number
}

export interface Canvas {
  pinyin: PinyinCanvas
  hanzi: { width: number; height: number }
  is_avoid_overlapping_mode: boolean
  x_scale_reduction_for_avoid_overlapping: number
}

export interface FontRef {
  source: string
  path: string
  original_filename: string
  sha256: string
  family_name: string
  units_per_em: number
  glyph_count: number
  name_renderable?: boolean
}

export interface LicenseEntry {
  name_id: number
  label: string
  value: string
}

export interface LicenseInfo {
  entries: LicenseEntry[]
  acknowledged: boolean
  acknowledged_at: string | null
  font_sha256: string | null
}

export interface TaskState {
  status: 'idle' | 'running' | 'done' | 'error'
  stage: string | null
  progress: number
  error: string | null
  started_at?: string | null
  finished_at?: string | null
}

export interface ReadingOverride {
  mode: 'replace' | 'append'
  pronunciations: string[]
}

export interface Project {
  id: string
  name: string
  created_at: string
  updated_at: string
  step: string
  base_font: FontRef | null
  pinyin_font: FontRef | null
  license: { base: LicenseInfo; pinyin: LicenseInfo }
  canvas: Canvas
  glyph_overrides: {
    readings: Record<string, ReadingOverride>
    excluded_characters: string[]
    // Keyed by the letter's ASCII name (e.g. "eh1" for ê̄)
    custom_glyphs?: Record<string, CustomGlyph>
  }
  output: { family_name: string; style_name: string; version: string }
  artifacts: Record<string, string>
  tasks: { prepare: TaskState; build: TaskState }
}

export interface PreviewItem {
  char: string
  pinyin: string
  svg: string
}

export interface PreviewResponse {
  items: PreviewItem[]
  warnings: string[]
}

export interface OutlineGlyph {
  glyph: string
  path: string
  advance_width: number
  a: number
  d: number
  x: number
  y: number
  label: string | null
}

export interface PreviewDetail {
  char: string
  pinyin: string
  hanzi: OutlineGlyph
  pinyin_glyphs: OutlineGlyph[]
  upem: number
  hanzi_width: number
  hanzi_height: number
  total_height: number
  descent: number
  base_line: number
  pinyin_width: number
  pinyin_height: number
  tracking: number
}

export interface GlyphEntry {
  name: string
  font: 'base' | 'pinyin' | 'output' | 'custom'
  char: string | null
  codepoints: string[]
  advance_width: number
  category: string
  overridden: boolean
  // Only on category 'pronunciation' (built-font .ssNN variants)
  label?: string
  variant?: string
  variant_label?: string
  reading?: string | null
}

export interface GlyphPage {
  total: number
  page: number
  size: number
  glyphs: GlyphEntry[]
}

export interface IvsSequence {
  selector: string
  glyph_suffix: string
  reading: string | null
  description: string
}

export interface GlyphDetail extends GlyphEntry {
  readings: string[]
  tables: { id: string; label: string }[]
  ivs: IvsSequence[]
}

export interface DuoyinziRow {
  char: string
  readings: string[]
  pattern_one: { index: number; pinyin: string; phrases: string[] }[]
  pattern_two_phrases: string[]
  exceptional_phrases: string[]
}

export interface PhrasePattern {
  phrase: string
  ignore: string | null
  sequence: { char: string; lookup: string | null }[]
}

export interface DuoyinziDetail extends DuoyinziRow {
  pattern_two_detail: PhrasePattern[]
  exceptional_detail: PhrasePattern[]
}

export interface GsubOverview {
  languages: Record<string, { features: string[] }>
  features: Record<string, string[]>
  lookups: Record<string, { type: string; rule_count: number }>
  lookup_order: string[]
}

export interface GsubRules {
  lookup: string
  type: string
  total: number
  page: number
  size: number
  rules: Record<string, unknown>[]
  glyph_chars: Record<string, string>
}

export interface IvsRow {
  char: string
  glyph: string
  readings: string[]
  sequences: IvsSequence[]
}

export interface GraphRule {
  lookup: string
  rule: number
  context: string[][]
  target_at: number | null
  sub_lookup: string | null
  output_glyph: string | null
  output_reading: string | null
  ignore: boolean
}

export interface GraphData {
  char: string
  glyph: string | null
  readings: string[]
  rules: GraphRule[]
}

export interface SimApplied {
  lookup: string
  rule: number
  ignored?: boolean
  sub_lookup?: string
  from?: string
  to?: string
}

export interface SimChar {
  char: string
  glyph: string | null
  final_glyph: string | null
  reading: string | null
  default_reading: string | null
  applied: SimApplied[]
}

export interface VerifyChar {
  char: string
  expected: string
  actual: string | null
  default: string | null
  status: 'ok' | 'fallback' | 'wrong'
}

export interface VerifyRow {
  phrase: string
  source: string
  status: 'ok' | 'fallback' | 'wrong'
  chars: VerifyChar[]
}

export interface VerifyReport {
  total: number
  counts: { ok: number; fallback: number; wrong: number }
  results: VerifyRow[]
}

// otfcc-format glyph outline (TrueType quadratic contours)
export interface OtfGlyph {
  advanceWidth: number
  contours: { x: number; y: number; on: boolean }[][]
}

/** How a missing pinyin letter is composed: base letter + a tone mark. */
export interface LetterRecipe {
  base: string
  mark_source: string
  mark_contours: number[] | null
  dx: number
  dy: number
  scale: number
  flip_y: boolean
}

export interface CustomGlyph {
  letter: string
  recipe: LetterRecipe
  font_sha256: string
  glyph: OtfGlyph
}

export type LetterStatus = 'font' | 'custom' | 'missing'

export interface PinyinLetter {
  letter: string
  name: string
  status: LetterStatus
  // A saved custom glyph composed from a different pinyin font
  stale: boolean
  default_recipe: LetterRecipe | null
  recipe: LetterRecipe | null
}

export interface PinyinLetters {
  upem: number
  ascent: number
  descent: number
  letters: PinyinLetter[]
}

export interface LetterPreview {
  letter: string
  name: string
  glyph: OtfGlyph
  advance_width: number
  base_path: string
  mark_path: string
  mark_contours: number[]
  source_contour_count: number
  auto_dx: number
  auto_dy: number
  upem: number
  ascent: number
  descent: number
}
