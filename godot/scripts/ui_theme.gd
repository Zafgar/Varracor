class_name UITheme
extends RefCounted
## Siisti UI-teema koodilla (ei asseteja): tumma paneeli + kultakorostus,
## selkeä FOKUS-tyyli ohjainnavigointia varten (PS5: dpad/tatti liikkuu,
## Cross valitsee, Circle palaa). Sama identiteetti kuin py-versiossa.

const BG := Color(0.07, 0.065, 0.09)
const PANEL := Color(0.11, 0.10, 0.13, 0.96)
const GOLD := Color(0.86, 0.72, 0.35)
const TEXT := Color(0.92, 0.90, 0.85)
const MUTED := Color(0.62, 0.60, 0.58)


static func build() -> Theme:
	var t := Theme.new()

	var normal := _box(Color(0.16, 0.15, 0.19), Color(0.32, 0.30, 0.28))
	var hover := _box(Color(0.22, 0.20, 0.24), GOLD)
	var focus := _box(Color(0.24, 0.21, 0.16), GOLD, 3)
	var pressed := _box(Color(0.30, 0.26, 0.18), GOLD)

	t.set_stylebox("normal", "Button", normal)
	t.set_stylebox("hover", "Button", hover)
	t.set_stylebox("focus", "Button", focus)
	t.set_stylebox("pressed", "Button", pressed)
	t.set_color("font_color", "Button", TEXT)
	t.set_color("font_hover_color", "Button", GOLD)
	t.set_color("font_focus_color", "Button", GOLD)
	t.set_font_size("font_size", "Button", 28)

	t.set_stylebox("panel", "PanelContainer", _box(PANEL, Color(0.35, 0.30, 0.22)))
	t.set_color("font_color", "Label", TEXT)
	t.set_font_size("font_size", "Label", 22)

	var grabber := _box(GOLD, GOLD)
	t.set_stylebox("slider", "HSlider", _box(Color(0.20, 0.19, 0.23), Color(0.32, 0.30, 0.28), 1, 4))
	t.set_stylebox("grabber_area", "HSlider", grabber)
	t.set_stylebox("grabber_area_highlight", "HSlider", grabber)
	return t


static func _box(bg: Color, border: Color, border_w := 2, radius := 10) -> StyleBoxFlat:
	var b := StyleBoxFlat.new()
	b.bg_color = bg
	b.border_color = border
	b.set_border_width_all(border_w)
	b.set_corner_radius_all(radius)
	b.content_margin_left = 26
	b.content_margin_right = 26
	b.content_margin_top = 12
	b.content_margin_bottom = 12
	return b


static func title(text: String, size := 64) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", GOLD)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


static func hint(text: String) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 18)
	l.add_theme_color_override("font_color", MUTED)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l
