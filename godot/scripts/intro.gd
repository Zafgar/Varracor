extends Control
## Alkuintro: sama narraatio kuin py-versiossa (menus/intro_screen.py),
## toteutettuna kunnolla: feidatut tekstikohtaukset + tunnelmapartikkelit
## per kohtaus, ohitus milloin vain (Cross/Space). Päättyy areenaan.

const SLIDES := [
	{"text": "In the Age of War, Varrakor burned.", "mood": "war"},
	{"text": "Three Kings ruled over divided realms.", "mood": "royal"},
	{"text": "Until the world broke apart.", "mood": "vortex"},
	{"text": "Catastrophes spread across the land.", "mood": "plague"},
	{"text": "A reluctant truce was forged in shadow.", "mood": "shadow"},
	{"text": "The Arenas were sanctioned by Arkon.", "mood": "holy"},
	{"text": "A child found the Vortex Blade.", "mood": "mystic"},
	{"text": "The Abyssal Weave awakens.", "mood": "weave"},
	{"text": "Three years of war against the Rift.", "mood": "battle"},
	{"text": "The road leads to Muckford...", "mood": "storm"},
]

const MOODS := {
	"war":    {"bg": Color(0.10, 0.05, 0.03), "pc": Color(1.0, 0.5, 0.2, 0.5), "dir": Vector2(0, -1), "amount": 70},
	"royal":  {"bg": Color(0.08, 0.07, 0.04), "pc": Color(0.9, 0.75, 0.35, 0.4), "dir": Vector2(0, -0.3), "amount": 40},
	"vortex": {"bg": Color(0.05, 0.03, 0.10), "pc": Color(0.3, 1.0, 0.8, 0.5), "dir": Vector2(0.4, -0.6), "amount": 60},
	"plague": {"bg": Color(0.04, 0.07, 0.04), "pc": Color(0.5, 0.8, 0.4, 0.4), "dir": Vector2(0.2, 0.4), "amount": 50},
	"shadow": {"bg": Color(0.05, 0.05, 0.06), "pc": Color(0.6, 0.6, 0.7, 0.25), "dir": Vector2(0.5, 0), "amount": 30},
	"holy":   {"bg": Color(0.09, 0.08, 0.05), "pc": Color(1.0, 0.95, 0.7, 0.45), "dir": Vector2(0, -0.5), "amount": 45},
	"mystic": {"bg": Color(0.06, 0.04, 0.09), "pc": Color(0.8, 0.6, 1.0, 0.45), "dir": Vector2(-0.2, -0.4), "amount": 50},
	"weave":  {"bg": Color(0.03, 0.06, 0.07), "pc": Color(0.4, 1.0, 0.85, 0.5), "dir": Vector2(0.3, -0.5), "amount": 55},
	"battle": {"bg": Color(0.10, 0.04, 0.03), "pc": Color(1.0, 0.35, 0.25, 0.5), "dir": Vector2(0.6, -0.8), "amount": 80},
	"storm":  {"bg": Color(0.03, 0.05, 0.08), "pc": Color(0.6, 0.7, 0.9, 0.5), "dir": Vector2(-0.3, 1.0), "amount": 110},
}

const SLIDE_TIME := 5.0

var _bg: ColorRect
var _label: Label
var _particles: CPUParticles2D
var _index := -1
var _t := 0.0


func _ready() -> void:
	theme = UITheme.build()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg = ColorRect.new()
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_bg)

	_particles = CPUParticles2D.new()
	_particles.position = Vector2(960, 540)
	_particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_particles.emission_rect_extents = Vector2(1000, 600)
	_particles.lifetime = 6.0
	_particles.preprocess = 4.0
	add_child(_particles)

	_label = Label.new()
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.set_anchors_preset(Control.PRESET_CENTER)
	_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_label.grow_vertical = Control.GROW_DIRECTION_BOTH
	_label.add_theme_font_size_override("font_size", 42)
	add_child(_label)

	var hint := UITheme.hint("Cross / Space — skip")
	hint.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	hint.position.y = -60
	add_child(hint)

	Audio.play_music("intro")
	_next_slide()


func _process(delta: float) -> void:
	_t += delta
	# Tekstin feidi sisään/ulos kohtauksen sisällä
	var a := 1.0
	if _t < 0.7:
		a = _t / 0.7
	elif _t > SLIDE_TIME - 0.7:
		a = max(0.0, (SLIDE_TIME - _t) / 0.7)
	_label.modulate.a = a
	if _t >= SLIDE_TIME:
		_next_slide()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("skip") or event.is_action_pressed("ui_accept"):
		Audio.sfx("whoosh")
		_finish()


func _next_slide() -> void:
	_index += 1
	if _index >= SLIDES.size():
		_finish()
		return
	_t = 0.0
	var slide: Dictionary = SLIDES[_index]
	var mood: Dictionary = MOODS[slide["mood"]]
	_label.text = slide["text"]
	var tw := create_tween()
	tw.tween_property(_bg, "color", mood["bg"], 1.0)
	_particles.color = mood["pc"]
	_particles.direction = mood["dir"]
	_particles.amount = mood["amount"]
	_particles.initial_velocity_min = 25.0
	_particles.initial_velocity_max = 80.0
	_particles.spread = 20.0
	Audio.sfx("click")


func _finish() -> void:
	# Intro päättyy metsätien avausopetukseen (matka kohti Muckfordia)
	Router.goto("res://scenes/forest_road.tscn", false)
