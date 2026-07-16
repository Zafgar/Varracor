extends CanvasLayer
## Pause-overlay areenaan: Options-nappi (PS5) / Esc avaa. MODAALINEN -
## eventit eivät vuoda pelimaailmaan (korjaa py-version pause-klikkibugin,
## lapsentauti #3). Resume / Options / Main Menu.

var _panel: Control


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
	_btn(box, "OPTIONS", func():
		toggle(false)
		Router.goto("res://scenes/options_menu.tscn"))
	_btn(box, "MAIN MENU", func():
		toggle(false)
		Router.goto("res://scenes/main_menu.tscn", false))


func _btn(parent: Node, text: String, action: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(300, 0)
	b.pressed.connect(func():
		Audio.sfx("confirm")
		action.call())
	parent.add_child(b)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		Audio.sfx("click")
		toggle(not _panel.visible)
		get_viewport().set_input_as_handled()


func toggle(show_menu: bool) -> void:
	_panel.visible = show_menu
	get_tree().paused = show_menu
	if show_menu:
		var first := _panel.find_children("", "Button", true, false)
		if not first.is_empty():
			(first[0] as Button).grab_focus()
