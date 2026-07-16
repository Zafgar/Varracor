extends Control
## Päävalikko: New Game -> intro, Continue -> areena, Options, Quit.
## Ohjainnavigointi: fokus ensimmäisessä napissa, dpad/tatti liikkuu,
## Cross valitsee. Signaalipohjainen (ei pollausta - lapsentauti #3).

var _buttons: Array[Button] = []


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)

	var bg := ColorRect.new()
	bg.color = UITheme.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_add_dust(bg)

	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	box.grow_vertical = Control.GROW_DIRECTION_BOTH
	box.add_theme_constant_override("separation", 18)
	add_child(box)

	box.add_child(UITheme.title("VARRACOR"))
	box.add_child(UITheme.hint("Gladiator Tycoon — 3D"))
	box.add_child(_spacer(30))

	_btn(box, "NEW GAME", func(): Router.goto("res://scenes/intro.tscn"))
	_btn(box, "CONTINUE", func():
		SaveGame.pending_load = true
		# Jatka siitä skenestä johon tallennettiin
		var scene: String = str(SaveGame.load_state().get(
			"scene", "res://scenes/muckford.tscn"))
		Router.goto(scene))
	# CONTINUE vain jos tallennus on olemassa
	_buttons[1].disabled = not SaveGame.has_save()
	_btn(box, "OPTIONS", func(): Router.goto("res://scenes/options_menu.tscn"))
	_btn(box, "QUIT", func(): get_tree().quit())

	box.add_child(_spacer(24))
	box.add_child(UITheme.hint("PS5: tatti = liiku valikossa, Cross = valitse"))

	_buttons[0].grab_focus()
	Audio.play_music("menu")


func _btn(parent: Node, text: String, action: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(340, 0)
	b.pressed.connect(func():
		Audio.sfx("confirm")
		action.call())
	b.focus_entered.connect(func(): Audio.sfx("click"))
	parent.add_child(b)
	_buttons.append(b)


func _spacer(h: int) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	return c


func _add_dust(parent: Node) -> void:
	# Hienovarainen kultapöly taustalle (siisti, ei räikeä)
	var p := CPUParticles2D.new()
	p.position = Vector2(960, 1100)
	p.amount = 40
	p.lifetime = 9.0
	p.preprocess = 9.0
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(960, 10)
	p.direction = Vector2(0, -1)
	p.spread = 12.0
	p.initial_velocity_min = 20.0
	p.initial_velocity_max = 55.0
	p.scale_amount_min = 1.0
	p.scale_amount_max = 2.6
	p.color = Color(0.86, 0.72, 0.35, 0.16)
	parent.add_child(p)
