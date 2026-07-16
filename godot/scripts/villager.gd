extends CharacterBody3D
## Kyläläinen: kevyt POI-kuljeskelu kotipisteen ympärillä (valitse piste,
## kävele, seisoskele). Pelkkää elävöitystä - ei vielä dialogia.

var home := Vector3.ZERO
var roam_radius := 10.0
var tint := Color(0.5, 0.4, 0.3)

const SPEED := 1.6

var _target := Vector3.ZERO
var _idle := 0.0


func _ready() -> void:
	home = global_position
	var mesh := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.35
	cm.height = 1.6
	mesh.mesh = cm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = tint
	mesh.material_override = mat
	add_child(mesh)
	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.35
	shape.height = 1.6
	col.shape = shape
	add_child(col)
	_pick_target()


func _physics_process(delta: float) -> void:
	if _idle > 0.0:
		_idle -= delta
		velocity.x = 0.0
		velocity.z = 0.0
	else:
		var to_target := _target - global_position
		to_target.y = 0.0
		if to_target.length() < 0.5:
			_idle = randf_range(2.0, 6.0)
			_pick_target()
		else:
			var dir := to_target.normalized()
			velocity.x = dir.x * SPEED
			velocity.z = dir.z * SPEED
			look_at(global_position + dir, Vector3.UP)
	if not is_on_floor():
		velocity.y -= 20.0 * delta
	else:
		velocity.y = 0.0
	move_and_slide()


func _pick_target() -> void:
	var a := randf_range(0.0, TAU)
	var r := randf_range(2.0, roam_radius)
	_target = home + Vector3(cos(a) * r, 0, sin(a) * r)
