extends Node3D
## Top-down 3D -kamera: seuraa kohdetta pehmeästi, katsoo alas ~55 asteen
## kulmassa (näyttää maailman "ylhäältäpäin" mutta syvyydellä).

@export var target_path: NodePath
@export var height := 18.0
@export var back := 10.0
@export var smooth := 6.0

var _cam: Camera3D


func _ready() -> void:
	_cam = Camera3D.new()
	_cam.current = true
	add_child(_cam)
	_update_pose(true)


func _process(delta: float) -> void:
	_update_pose(false, delta)


func _update_pose(snap: bool, delta: float = 0.0) -> void:
	var target := get_node_or_null(target_path) as Node3D
	if target == null:
		return
	var goal := target.global_position + Vector3(0, height, back)
	if snap:
		global_position = goal
	else:
		global_position = global_position.lerp(goal, clamp(smooth * delta, 0.0, 1.0))
	_cam.look_at(target.global_position, Vector3.UP)
