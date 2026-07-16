extends CanvasLayer
## Pause-overlay areenaan: Options-nappi (PS5) / Esc avaa. MODAALINEN -
## eventit eivät vuoda pelimaailmaan (korjaa py-version pause-klikkibugin,
## lapsentauti #3). Resume / Options / Main Menu.

var _panel: Control
var _saved_label: Label


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 50
	_panel = Control.new()
	_panel.theme = UITheme.build()
	_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.visible = false
	add_child(_panel)

	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.add_child(dim)

	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	box.grow_vertical = Control.GROW_DIRECTION_BOTH
	box.add_theme_constant_override("separation", 16)
	_panel.add_child(box)

	box.add_child(UITheme.title("PAUSED", 44))
	_btn(box, "RESUME", func(): toggle(false))
	_btn(box, "SAVE GAME", func(): _save_game())
	_btn(box, "OPTIONS", func():
		toggle(false)
		Router.goto("res://scenes/options_menu.tscn"))
	_btn(box, "MAIN MENU", func():
		toggle(false)
		Router.goto("res://scenes/main_menu.tscn", false))

	_saved_label = UITheme.hint("")
	box.add_child(_saved_label)


func _btn(parent: Node, text: String, action: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(300, 0)
	b.pressed.connect(func():
		Audio.sfx("confirm")
		action.call())
	parent.add_child(b)


## SAVE GAME avaa saman slottipaneelin kuin päävalikon LOAD GAME
func _save_game() -> void:
	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		_saved_label.text = "No commander to save"
		return
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.65)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.add_child(dim)
	var panel := PanelContainer.new()
	panel.set_script(load("res://scripts/save_slot_panel.gd"))
	panel.set("mode", "save")
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	dim.add_child(panel)
	panel.connect("slot_picked", func(slot: int):
		if SaveGame.save_slot(slot, players[0].state_dict()):
			_saved_label.text = "Saved to slot %d" % slot
		else:
			_saved_label.text = "Save failed"
		dim.queue_free()
		_focus_first())
	panel.connect("closed", func():
		dim.queue_free()
		_focus_first())


func _focus_first() -> void:
	var first := _panel.find_children("", "Button", true, false)
	if not first.is_empty():
		(first[0] as Button).grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		Audio.sfx("click")
		toggle(not _panel.visible)
		get_viewport().set_input_as_handled()


func toggle(show_menu: bool) -> void:
	_panel.visible = show_menu
	get_tree().paused = show_menu
	if show_menu:
		_focus_first()
