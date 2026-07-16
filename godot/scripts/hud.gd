extends CanvasLayer
## Taistelu-HUD: HP/Mana/Stamina-palkit + 3 loitsupaikkaa cooldown-
## täyttöineen ja näppäinvihjeineen (molemmat ohjaustavat näkyvissä).
## Lukee Commanderin arvot _processissa (HUD on puhdas näkymä).

var player: Node

var _bars: Dictionary = {}
var _slots: Array[Dictionary] = []

const SLOT_HINTS := ["1 / Square", "2 / Triangle", "3 / L1"]


func _ready() -> void:
	var root := Control.new()
	root.theme = UITheme.build()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	# Palkit vasempaan yläkulmaan
	var box := VBoxContainer.new()
	box.position = Vector2(24, 24)
	box.add_theme_constant_override("separation", 6)
	root.add_child(box)
	_bars["hp"] = _bar(box, Color(0.80, 0.25, 0.22))
	_bars["mana"] = _bar(box, Color(0.30, 0.45, 0.90))
	_bars["stamina"] = _bar(box, Color(0.85, 0.75, 0.30))

	# Loitsupaikat alakeskelle
	var slots := HBoxContainer.new()
	slots.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	slots.grow_horizontal = Control.GROW_DIRECTION_BOTH
	slots.position.y = -110
	slots.add_theme_constant_override("separation", 14)
	root.add_child(slots)
	for i in range(3):
		_slots.append(_spell_slot(slots, i))


func _bar(parent: Node, color: Color) -> Dictionary:
	var back := ColorRect.new()
	back.color = Color(0.08, 0.08, 0.10, 0.85)
	back.custom_minimum_size = Vector2(280, 18)
	parent.add_child(back)
	var fill := ColorRect.new()
	fill.color = color
	fill.position = Vector2(2, 2)
	fill.size = Vector2(276, 14)
	back.add_child(fill)
	return {"fill": fill, "w": 276.0}


func _spell_slot(parent: Node, index: int) -> Dictionary:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(120, 74)
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


func _process(_delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	_set_bar("hp", player.hp, player.max_hp)
	_set_bar("mana", player.mana, player.max_mana)
	_set_bar("stamina", player.stamina, player.max_stamina)

	for i in range(_slots.size()):
		var slot: Dictionary = _slots[i]
		if i < player.spells.size():
			var spec: Dictionary = Catalogs.spell_spec(player.spells[i])
			(slot["name"] as Label).text = str(spec.get("name", player.spells[i]))
			var cd: float = player.cooldowns[i]
			var max_cd: float = player.ARCH_CD.get(
				str(spec.get("archetype", "nuke")), 1.8)
			(slot["shade"] as ColorRect).color.a = \
				0.65 * clamp(cd / max_cd, 0.0, 1.0)
		else:
			(slot["name"] as Label).text = "-"


func _set_bar(key: String, value: float, max_value: float) -> void:
	var b: Dictionary = _bars[key]
	var frac: float = clamp(value / max(max_value, 1.0), 0.0, 1.0)
	(b["fill"] as ColorRect).size.x = b["w"] * frac
