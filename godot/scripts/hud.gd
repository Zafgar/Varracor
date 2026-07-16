extends CanvasLayer
## Taistelu-HUD v2: kehystetyt gradientpalkit (HP/Mana/Stamina) joissa
## viivepalkki (menetys näkyy hetken vaaleana ennen valumista) +
## numeroarvot, sekä 3 loitsupaikkaa cooldown-verhoineen. Lukee
## Commanderin arvot _processissa (HUD on puhdas näkymä).

var player: Node

var _bars: Dictionary = {}
var _slots: Array[Dictionary] = []

const SLOT_HINTS := ["1 / Square", "2 / Triangle", "3 / L1"]
const BAR_W := 300.0
const BAR_H := 24.0

const BAR_DEFS := [
	{"key": "hp", "label": "HP",
	 "lo": Color(0.55, 0.10, 0.10), "hi": Color(0.95, 0.35, 0.25)},
	{"key": "mana", "label": "MP",
	 "lo": Color(0.12, 0.22, 0.60), "hi": Color(0.35, 0.60, 1.0)},
	{"key": "stamina", "label": "SP",
	 "lo": Color(0.55, 0.45, 0.10), "hi": Color(0.95, 0.85, 0.35)},
]


func _ready() -> void:
	var root := Control.new()
	root.theme = UITheme.build()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	# Palkit vasempaan yläkulmaan
	var box := VBoxContainer.new()
	box.position = Vector2(24, 24)
	box.add_theme_constant_override("separation", 8)
	root.add_child(box)
	for def in BAR_DEFS:
		_bars[def["key"]] = _bar(box, def)

	# Loitsupaikat alakeskelle
	var slots := HBoxContainer.new()
	slots.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	slots.grow_horizontal = Control.GROW_DIRECTION_BOTH
	slots.position.y = -110
	slots.add_theme_constant_override("separation", 14)
	root.add_child(slots)
	for i in range(3):
		_slots.append(_spell_slot(slots, i))


## Palkki: tumma kehyspaneeli + gradienttitäyttö + viivepalkki + arvoteksti
func _bar(parent: Node, def: Dictionary) -> Dictionary:
	var frame := Panel.new()
	frame.custom_minimum_size = Vector2(BAR_W, BAR_H)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.06, 0.09, 0.92)
	sb.border_color = Color(0.42, 0.38, 0.30)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(7)
	frame.add_theme_stylebox_override("panel", sb)
	parent.add_child(frame)

	# Viivepalkki: näyttää tuoreen menetyksen vaaleana hetken
	var lag := ColorRect.new()
	lag.color = Color(0.9, 0.85, 0.8, 0.55)
	lag.position = Vector2(3, 3)
	lag.size = Vector2(BAR_W - 6, BAR_H - 6)
	frame.add_child(lag)

	# Gradienttitäyttö
	var grad := Gradient.new()
	grad.set_color(0, def["lo"])
	grad.set_color(1, def["hi"])
	var gtex := GradientTexture2D.new()
	gtex.gradient = grad
	gtex.fill_from = Vector2(0, 0)
	gtex.fill_to = Vector2(1, 0)
	var fill := TextureRect.new()
	fill.texture = gtex
	fill.stretch_mode = TextureRect.STRETCH_TILE
	fill.position = Vector2(3, 3)
	fill.size = Vector2(BAR_W - 6, BAR_H - 6)
	frame.add_child(fill)

	# Kiilto: ohut vaalea raita ylälaidassa
	var shine := ColorRect.new()
	shine.color = Color(1, 1, 1, 0.14)
	shine.position = Vector2(3, 3)
	shine.size = Vector2(BAR_W - 6, 5)
	frame.add_child(shine)

	var lbl := Label.new()
	lbl.add_theme_font_size_override("font_size", 14)
	lbl.add_theme_color_override("font_color", Color(0.95, 0.94, 0.90))
	lbl.add_theme_constant_override("outline_size", 4)
	lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	lbl.position = Vector2(10, 2)
	frame.add_child(lbl)
	return {"fill": fill, "lag": lag, "shine": shine, "label": lbl,
		"prefix": def["label"], "w": BAR_W - 6.0}


func _spell_slot(parent: Node, index: int) -> Dictionary:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(130, 76)
	parent.add_child(panel)
	var v := VBoxContainer.new()
	panel.add_child(v)
	var name_lbl := Label.new()
	name_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_lbl.add_theme_font_size_override("font_size", 16)
	v.add_child(name_lbl)
	var hint := UITheme.hint(SLOT_HINTS[index])
	v.add_child(hint)
	# Cooldown-verho: tummenee kun loitsu latautuu
	var shade := ColorRect.new()
	shade.color = Color(0, 0, 0, 0.65)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(shade)
	return {"name": name_lbl, "shade": shade}


func _process(delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	_set_bar("hp", player.hp, player.max_hp, delta)
	_set_bar("mana", player.mana, player.max_mana, delta)
	_set_bar("stamina", player.stamina, player.max_stamina, delta)

	for i in range(_slots.size()):
		var slot: Dictionary = _slots[i]
		if i < player.spells.size():
			(slot["name"] as Label).text = player.spell_display_name(i)
			var cd: float = player.cooldowns[i]
			var max_cd: float = player.cooldown_max(i)
			(slot["shade"] as ColorRect).color.a = \
				0.65 * clamp(cd / max_cd, 0.0, 1.0)
		else:
			(slot["name"] as Label).text = "-"
			(slot["shade"] as ColorRect).color.a = 0.0


func _set_bar(key: String, value: float, max_value: float,
		delta: float) -> void:
	var b: Dictionary = _bars[key]
	var frac: float = clamp(value / max(max_value, 1.0), 0.0, 1.0)
	var w: float = b["w"]
	(b["fill"] as TextureRect).size.x = w * frac
	(b["shine"] as ColorRect).size.x = w * frac
	# Viivepalkki valuu kohti todellista arvoa
	var lag := b["lag"] as ColorRect
	if lag.size.x < w * frac:
		lag.size.x = w * frac
	else:
		lag.size.x = max(w * frac, lag.size.x - w * 0.6 * delta)
	(b["label"] as Label).text = "%s  %d / %d" % [
		b["prefix"], int(value), int(max_value)]
