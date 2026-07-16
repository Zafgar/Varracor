extends Node
## InputSetup (autoload): rekisteröi peliohjaus-actionit koodissa.
## POHJANA PS5 DUALSENSE (SDL-mappaus toimii suoraan Godotissa):
##   Vasen tatti  = liike          Ristinappi (Cross) = dash / valinta
##   Options      = pause          Ympyrä (Circle)    = takaisin
## Näppäimistö (WASD/Space/Esc) toimii rinnalla kehitystä varten.
## UI-navigointi käyttää Godotin sisäänrakennettuja ui_*-actioneita,
## jotka tukevat ohjainta valmiiksi (dpad/tatti + Cross/Circle).

const DEADZONE := 0.2


func _ready() -> void:
	_axis("move_left", KEY_A, JOY_AXIS_LEFT_X, -1.0)
	_axis("move_right", KEY_D, JOY_AXIS_LEFT_X, 1.0)
	_axis("move_up", KEY_W, JOY_AXIS_LEFT_Y, -1.0)
	_axis("move_down", KEY_S, JOY_AXIS_LEFT_Y, 1.0)
	_button("dash", KEY_SPACE, JOY_BUTTON_A)          # Cross
	_button("pause", KEY_ESCAPE, JOY_BUTTON_START)    # Options
	_button("skip", KEY_SPACE, JOY_BUTTON_A)          # intro skip


func _axis(action: String, key: Key, axis: JoyAxis, value: float) -> void:
	_ensure(action)
	var k := InputEventKey.new()
	k.physical_keycode = key
	InputMap.action_add_event(action, k)
	var j := InputEventJoypadMotion.new()
	j.axis = axis
	j.axis_value = value
	InputMap.action_add_event(action, j)


func _button(action: String, key: Key, btn: JoyButton) -> void:
	_ensure(action)
	var k := InputEventKey.new()
	k.physical_keycode = key
	InputMap.action_add_event(action, k)
	var j := InputEventJoypadButton.new()
	j.button_index = btn
	InputMap.action_add_event(action, j)


func _ensure(action: String) -> void:
	if InputMap.has_action(action):
		InputMap.action_erase_events(action)
	else:
		InputMap.add_action(action, DEADZONE)
