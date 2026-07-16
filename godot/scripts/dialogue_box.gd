extends CanvasLayer
## Dialogilaatikko: puhujan nimi kullalla + kirjoituskone-teksti +
## valinnaiset vastausvaihtoehdot. Toimii await-tyylillä:
##   await dlg.say("Commander", "...")           # jatka Cross/Space/LMB
##   var i: int = await dlg.ask("X", "...", ["A", "B"])
## Skene pausetetaan dialogin ajaksi (tämä layer ajaa pausen läpi).

signal advanced
signal chose(index: int)

const TYPE_SPEED := 45.0   # merkkiä sekunnissa

var _panel: PanelContainer
var _name_lbl: Label
var _text_lbl: Label
var _choice_box: VBoxContainer
var _hint: Label
var _typing := false
var _choosing := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 40
	var root := Control.new()
	root.theme = UITheme.build()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	_panel = PanelContainer.new()
	_panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_panel.offset_left = 320
	_panel.offset_right = -320
	_panel.offset_top = -240
	_panel.offset_bottom = -50
	_panel.visible = false
	root.add_child(_panel)

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	_panel.add_child(v)

	_name_lbl = Label.new()
	_name_lbl.add_theme_color_override("font_color", UITheme.GOLD)
	_name_lbl.add_theme_font_size_override("font_size", 26)
	v.add_child(_name_lbl)

	_text_lbl = Label.new()
	_text_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text_lbl.custom_minimum_size = Vector2(0, 60)
	v.add_child(_text_lbl)

	_choice_box = VBoxContainer.new()
	_choice_box.add_theme_constant_override("separation", 6)
	v.add_child(_choice_box)

	_hint = UITheme.hint("Cross / Space — continue")
	v.add_child(_hint)


func say(speaker: String, text: String) -> void:
	_show_line(speaker, text)
	_hint.visible = true
	await advanced


func ask(speaker: String, text: String, options: Array) -> int:
	_show_line(speaker, text)
	_hint.visible = false
	# Odota että teksti on kirjoitettu ennen valintoja
	while _typing:
		await get_tree().process_frame
	_choosing = true
	for i in range(options.size()):
		var b := Button.new()
		b.text = str(options[i])
		var idx := i
		b.pressed.connect(func():
			Audio.sfx("confirm")
			chose.emit(idx))
		_choice_box.add_child(b)
	(_choice_box.get_child(0) as Button).grab_focus()
	var picked: int = await chose
	_choosing = false
	for c in _choice_box.get_children():
		c.queue_free()
	return picked


func close() -> void:
	_panel.visible = false
	get_tree().paused = false


func _show_line(speaker: String, text: String) -> void:
	get_tree().paused = true
	_panel.visible = true
	_name_lbl.text = speaker
	_text_lbl.text = text
	_text_lbl.visible_characters = 0
	_typing = true
	Audio.sfx("click")


func _process(delta: float) -> void:
	if _typing:
		_text_lbl.visible_characters += int(ceil(TYPE_SPEED * delta))
		if _text_lbl.visible_characters >= _text_lbl.text.length():
			_text_lbl.visible_characters = -1
			_typing = false


func _unhandled_input(event: InputEvent) -> void:
	if not _panel.visible or _choosing:
		return
	if event.is_action_pressed("skip") or event.is_action_pressed("ui_accept") \
			or event.is_action_pressed("attack"):
		get_viewport().set_input_as_handled()
		if _typing:
			# Ensimmäinen painallus näyttää koko rivin heti
			_text_lbl.visible_characters = -1
			_typing = false
		else:
			advanced.emit()
