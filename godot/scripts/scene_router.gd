extends Node
## Router (autoload): scene-vaihdot feidillä. Korvaa py-version
## merkkijonotilakoneen (lapsentauti #2) - jokainen näkymä on scene ja
## siirtymä on yksi kutsu: Router.goto("res://scenes/x.tscn").

var _fade: ColorRect
var _busy := false
var _history: Array[String] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)


func goto(path: String, remember := true) -> void:
	if _busy:
		return
	_busy = true
	if remember:
		var cur := get_tree().current_scene
		if cur and cur.scene_file_path != "":
			_history.append(cur.scene_file_path)
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, 0.25)
	await tw.finished
	get_tree().paused = false
	get_tree().change_scene_to_file(path)
	var tw2 := create_tween()
	tw2.tween_property(_fade, "color:a", 0.0, 0.25)
	await tw2.finished
	_busy = false


func back(fallback := "res://scenes/main_menu.tscn") -> void:
	var target: String = _history.pop_back() if not _history.is_empty() else fallback
	goto(target, false)
