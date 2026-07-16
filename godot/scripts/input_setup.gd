extends Node
## InputSetup (autoload): peliohjaus-actionit koodissa. MOLEMMAT toimivat:
##   PS5 DualSense: vasen tatti liike, oikea tatti tähtäys, R2 lyönti,
##     Cross dash, Square/Triangle/L1 loitsut 1-3, Options pause
##   Näppäimistö+hiiri: WASD liike, hiiri tähtäys, LMB lyönti,
##     Space dash, 1/2/3 loitsut, Esc pause
## UI käyttää Godotin ui_*-actioneita (toimivat kummallakin valmiiksi).

const DEADZONE := 0.2


func _ready() -> void:
	_axis("move_left", KEY_A, JOY_AXIS_LEFT_X, -1.0)
	_axis("move_right", KEY_D, JOY_AXIS_LEFT_X, 1.0)
	_axis("move_up", KEY_W, JOY_AXIS_LEFT_Y, -1.0)
	_axis("move_down", KEY_S, JOY_AXIS_LEFT_Y, 1.0)
	# Tähtäys oikealla tatilla (hiiri hoidetaan raycastilla commanderissa)
	_axis("aim_left", KEY_NONE, JOY_AXIS_RIGHT_X, -1.0)
	_axis("aim_right", KEY_NONE, JOY_AXIS_RIGHT_X, 1.0)
	_axis("aim_up", KEY_NONE, JOY_AXIS_RIGHT_Y, -1.0)
	_axis("aim_down", KEY_NONE, JOY_AXIS_RIGHT_Y, 1.0)

	_button("dash", KEY_SPACE, JOY_BUTTON_A)            # Cross
	_button("pause", KEY_ESCAPE, JOY_BUTTON_START)      # Options
	_button("skip", KEY_SPACE, JOY_BUTTON_A)
	_button("menu", KEY_M, JOY_BUTTON_TOUCHPAD)         # Commander-menu/kartta

	# Lyönti: LMB + R2-liipaisin
	_mouse_and_trigger("attack", MOUSE_BUTTON_LEFT, JOY_AXIS_TRIGGER_RIGHT)
	# Loitsut 1-3: numerot + Square/Triangle/L1
	_button("cast_1", KEY_1, JOY_BUTTON_X)              # Square
	_button("cast_2", KEY_2, JOY_BUTTON_Y)              # Triangle
	_button("cast_3", KEY_3, JOY_BUTTON_LEFT_SHOULDER)  # L1


func _axis(action: String, key: Key, axis: JoyAxis, value: float) -> void:
	_ensure(action)
	if key != KEY_NONE:
		var k := InputEventKey.new()
		k.physical_keycode = key
		InputMap.action_add_event(action, k)
	var j := InputEventJoypadMotion.new()
	j.axis = axis
	j.axis_value = value
	InputMap.action_add_event(action, j)


func _button(action: String, key: Key, btn: JoyButton) -> void:
	_ensure(action)
	if key != KEY_NONE:
		var k := InputEventKey.new()
		k.physical_keycode = key
		InputMap.action_add_event(action, k)
	var j := InputEventJoypadButton.new()
	j.button_index = btn
	InputMap.action_add_event(action, j)


func _mouse_and_trigger(action: String, mouse_btn: MouseButton,
		trigger: JoyAxis) -> void:
	_ensure(action)
	var m := InputEventMouseButton.new()
	m.button_index = mouse_btn
	InputMap.action_add_event(action, m)
	var t := InputEventJoypadMotion.new()
	t.axis = trigger
	t.axis_value = 1.0
	InputMap.action_add_event(action, t)


func _ensure(action: String) -> void:
	if InputMap.has_action(action):
		InputMap.action_erase_events(action)
	else:
		InputMap.add_action(action, DEADZONE)
