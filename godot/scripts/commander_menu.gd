extends CanvasLayer
## Commander-menu (M / PS5-touchpad): kaksi välilehteä -
##   COMMANDER: hahmon tila (taso, HP/MP/SP, STR/INT, ase, kyvyt)
##   MAP: koodipiirretty yleiskartta alueesta pelaajamerkillä
## Pausettaa maailman kuten pause-menu. map_features + world-rajat
## annetaan skenestä (Muckford täyttää omansa).

var player: Node
## Kartan piirtoalue maailmakoordinaateissa: Rect2(min_x, min_z, leveys, syvyys)
var world_rect := Rect2(-45, -30, 85, 60)
## {pos: Vector2(maailma-xz), size: Vector2, color: Color, label: String}
var map_features: Array = []
var area_title := "MUCKFORD"

const MAP_W := 860.0
const MAP_H := 560.0

var _panel: Control
var _tabs: Dictionary = {}
var _pages: Dictionary = {}
var _stats_box: VBoxContainer
var _marker: ColorRect


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 45
	_panel = Control.new()
	_panel.theme = UITheme.build()
	_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.visible = false
	add_child(_panel)

	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.7)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.add_child(dim)

	var frame := PanelContainer.new()
	frame.set_anchors_preset(Control.PRESET_CENTER)
	frame.grow_horizontal = Control.GROW_DIRECTION_BOTH
	frame.grow_vertical = Control.GROW_DIRECTION_BOTH
	_panel.add_child(frame)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	frame.add_child(v)

	# Välilehtinapit
	var tab_row := HBoxContainer.new()
	tab_row.add_theme_constant_override("separation", 10)
	tab_row.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(tab_row)
	for tab_name in ["COMMANDER", "MAP"]:
		var b := Button.new()
		b.text = tab_name
		b.toggle_mode = true
		b.pressed.connect(func():
			Audio.sfx("click")
			_show_page(tab_name))
		tab_row.add_child(b)
		_tabs[tab_name] = b

	# Sivut
	_pages["COMMANDER"] = _build_commander_page()
	_pages["MAP"] = _build_map_page()
	for key in _pages:
		v.add_child(_pages[key])

	v.add_child(UITheme.hint("M / Touchpad — close      Circle / Esc — close"))


func _build_commander_page() -> Control:
	var page := PanelContainer.new()
	page.custom_minimum_size = Vector2(MAP_W, MAP_H)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 30)
	page.add_child(h)
	# "Muotokuva": tyylitelty commander-siluetti
	var portrait := PanelContainer.new()
	portrait.custom_minimum_size = Vector2(280, 0)
	var pv := VBoxContainer.new()
	pv.alignment = BoxContainer.ALIGNMENT_CENTER
	portrait.add_child(pv)
	pv.add_child(UITheme.title("⚔", 130))
	var nm := UITheme.title("COMMANDER", 30)
	pv.add_child(nm)
	pv.add_child(UITheme.hint("The one who lost the seam"))
	h.add_child(portrait)

	_stats_box = VBoxContainer.new()
	_stats_box.add_theme_constant_override("separation", 8)
	_stats_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(_stats_box)
	return page


func _build_map_page() -> Control:
	var page := PanelContainer.new()
	page.custom_minimum_size = Vector2(MAP_W, MAP_H)
	var canvas := Control.new()
	canvas.custom_minimum_size = Vector2(MAP_W, MAP_H)
	page.add_child(canvas)

	# Pohja
	var bg := ColorRect.new()
	bg.color = Color(0.10, 0.13, 0.09)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	canvas.add_child(bg)
	var title := UITheme.title(area_title, 34)
	title.position = Vector2(20, 10)
	canvas.add_child(title)

	# Kohteet skenestä
	for f in map_features:
		var r := ColorRect.new()
		r.color = f["color"]
		var p: Vector2 = _to_map(f["pos"])
		var s := Vector2(f["size"].x / world_rect.size.x * MAP_W,
			f["size"].y / world_rect.size.y * MAP_H)
		r.position = p - s / 2.0
		r.size = s
		canvas.add_child(r)
		if str(f.get("label", "")) != "":
			var lbl := Label.new()
			lbl.text = str(f["label"])
			lbl.add_theme_font_size_override("font_size", 15)
			lbl.add_theme_color_override("font_color", UITheme.TEXT)
			lbl.add_theme_constant_override("outline_size", 5)
			lbl.add_theme_color_override("font_outline_color",
				Color(0, 0, 0, 0.9))
			lbl.position = p - Vector2(len(str(f["label"])) * 4.0, 10)
			canvas.add_child(lbl)

	# Pelaajamerkki (kulta) - päivittyy _processissa
	_marker = ColorRect.new()
	_marker.color = UITheme.GOLD
	_marker.size = Vector2(12, 12)
	_marker.rotation_degrees = 45.0
	canvas.add_child(_marker)
	var mlbl := Label.new()
	mlbl.text = "YOU"
	mlbl.add_theme_font_size_override("font_size", 13)
	mlbl.add_theme_color_override("font_color", UITheme.GOLD)
	_marker.add_child(mlbl)
	mlbl.position = Vector2(10, -6)
	return page


func _to_map(world_xz: Vector2) -> Vector2:
	return Vector2(
		(world_xz.x - world_rect.position.x) / world_rect.size.x * MAP_W,
		(world_xz.y - world_rect.position.y) / world_rect.size.y * MAP_H)


func _show_page(tab_name: String) -> void:
	for key in _pages:
		(_pages[key] as Control).visible = key == tab_name
		(_tabs[key] as Button).button_pressed = key == tab_name
	if tab_name == "COMMANDER":
		_refresh_stats()


func _refresh_stats() -> void:
	for c in _stats_box.get_children():
		c.queue_free()
	if player == null:
		return
	var weapon: String = "Vortex Blade" if player.has_sword else "Fists"
	var spell_names: Array[String] = []
	for i in range(player.spells.size()):
		spell_names.append(player.spell_display_name(i))
	var rows := [
		["Level", str(player.level)],
		["HP", "%d / %d" % [int(player.hp), int(player.max_hp)]],
		["Mana", "%d / %d" % [int(player.mana), int(player.max_mana)]],
		["Stamina", "%d / %d" % [int(player.stamina), int(player.max_stamina)]],
		["Strength", str(player.strength)],
		["Intelligence", str(player.intelligence)],
		["Weapon", weapon],
		["Spells", ", ".join(spell_names) if spell_names.size() > 0 else "— none —"],
	]
	for row in rows:
		var h := HBoxContainer.new()
		var k := Label.new()
		k.text = str(row[0])
		k.custom_minimum_size = Vector2(200, 0)
		k.add_theme_color_override("font_color", UITheme.MUTED)
		h.add_child(k)
		var val := Label.new()
		val.text = str(row[1])
		val.add_theme_color_override("font_color", UITheme.TEXT)
		h.add_child(val)
		_stats_box.add_child(h)


func _process(_delta: float) -> void:
	if _panel.visible and _marker and player and is_instance_valid(player):
		_marker.position = _to_map(Vector2(
			player.global_position.x, player.global_position.z)) \
			- Vector2(6, 6)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("menu"):
		toggle(not _panel.visible)
		get_viewport().set_input_as_handled()
	elif _panel.visible and (event.is_action_pressed("ui_cancel")
			or event.is_action_pressed("pause")):
		toggle(false)
		get_viewport().set_input_as_handled()


func toggle(show_menu: bool) -> void:
	Audio.sfx("click")
	_panel.visible = show_menu
	get_tree().paused = show_menu
	if show_menu:
		_show_page("COMMANDER")
		(_tabs["COMMANDER"] as Button).grab_focus()
