extends Control
## Optiot: Master/Music/SFX-liu'ut (AudioServer-väylät) + fullscreen.
## Asetukset säilyvät user://settings.cfg:ssä. Circle/Esc = takaisin.

const CFG := "user://settings.cfg"

var _sliders: Dictionary = {}


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = UITheme.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	box.grow_vertical = Control.GROW_DIRECTION_BOTH
	box.add_theme_constant_override("separation", 16)
	add_child(box)

	box.add_child(UITheme.title("OPTIONS", 48))
	for bus in ["Master", "Music", "SFX"]:
		box.add_child(_volume_row(bus))

	var fs := CheckButton.new()
	fs.text = "Fullscreen"
	fs.button_pressed = DisplayServer.window_get_mode() \
		== DisplayServer.WINDOW_MODE_FULLSCREEN
	fs.toggled.connect(_on_fullscreen)
	box.add_child(fs)

	var back := Button.new()
	back.text = "BACK"
	back.pressed.connect(func():
		Audio.sfx("back")
		_save()
		Router.back())
	box.add_child(back)
	box.add_child(UITheme.hint("Circle / Esc palaa"))

	_load()
	back.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("pause"):
		Audio.sfx("back")
		_save()
		Router.back()


func _volume_row(bus: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	var lbl := Label.new()
	lbl.text = bus
	lbl.custom_minimum_size = Vector2(120, 0)
	row.add_child(lbl)
	var s := HSlider.new()
	s.min_value = 0.0
	s.max_value = 1.0
	s.step = 0.05
	s.custom_minimum_size = Vector2(340, 24)
	var idx := AudioServer.get_bus_index(bus)
	s.value = db_to_linear(AudioServer.get_bus_volume_db(idx)) if idx >= 0 else 1.0
	s.value_changed.connect(func(v: float):
		var i := AudioServer.get_bus_index(bus)
		if i >= 0:
			AudioServer.set_bus_volume_db(i, linear_to_db(max(v, 0.0001)))
		Audio.sfx("click"))
	row.add_child(s)
	_sliders[bus] = s
	return row


func _on_fullscreen(on: bool) -> void:
	DisplayServer.window_set_mode(
		DisplayServer.WINDOW_MODE_FULLSCREEN if on
		else DisplayServer.WINDOW_MODE_WINDOWED)
	Audio.sfx("confirm")


func _save() -> void:
	var cfg := ConfigFile.new()
	for bus in _sliders:
		cfg.set_value("audio", bus, _sliders[bus].value)
	cfg.set_value("video", "fullscreen",
		DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN)
	cfg.save(CFG)


func _load() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(CFG) != OK:
		return
	for bus in _sliders:
		var v: float = cfg.get_value("audio", bus, 1.0)
		_sliders[bus].value = v
	if cfg.get_value("video", "fullscreen", false):
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
