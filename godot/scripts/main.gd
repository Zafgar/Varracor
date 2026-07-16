extends Node3D
## Varracor 3D -prototyyppi: top-down 3D -areena, pelaaja ja pari
## harjoitusvihollista. KAIKKI rakennetaan koodilla (sama placeholder-
## filosofia kuin py-versiossa - ei asseteja, mesh-primitiivit riittävät
## kunnes oikea grafiikka tehdään).

const ARENA_W := 60.0
const ARENA_D := 40.0

var player: CharacterBody3D


func _ready() -> void:
	_build_environment()
	_build_arena()
	player = _spawn_player()
	_spawn_dummies()
	_build_camera()
	# Data-putken savutesti: sama kaava kuin py-versiossa
	print("[Varracor3D] stat_target(20) = ", Catalogs.stat_target(20))
	print("[Varracor3D] Arcane Dart T1 dmg @INT50 = ",
		Catalogs.scaled_damage(1, 50, "nuke"))


func _build_environment() -> void:
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55.0, 35.0, 0.0)
	sun.shadow_enabled = true
	add_child(sun)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.06, 0.06, 0.09)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.35, 0.35, 0.42)
	e.glow_enabled = true          # spell-hehkut ilmaiseksi GPU:lla
	env.environment = e
	add_child(env)


func _build_arena() -> void:
	# Lattia
	var floor_body := StaticBody3D.new()
	var floor_mesh := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(ARENA_W, ARENA_D)
	floor_mesh.mesh = plane
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.32, 0.27, 0.20)   # muckford-savimaa
	floor_mesh.material_override = mat
	floor_body.add_child(floor_mesh)
	var floor_col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(ARENA_W, 0.1, ARENA_D)
	floor_col.shape = box
	floor_col.position.y = -0.05
	floor_body.add_child(floor_col)
	add_child(floor_body)

	# Seinät + esteet
	for wall in [
		[Vector3(0, 1, -ARENA_D / 2), Vector3(ARENA_W, 2, 1)],
		[Vector3(0, 1, ARENA_D / 2), Vector3(ARENA_W, 2, 1)],
		[Vector3(-ARENA_W / 2, 1, 0), Vector3(1, 2, ARENA_D)],
		[Vector3(ARENA_W / 2, 1, 0), Vector3(1, 2, ARENA_D)],
		[Vector3(-10, 1, -5), Vector3(4, 2, 4)],
		[Vector3(12, 1, 7), Vector3(5, 2, 3)],
	]:
		add_child(_make_block(wall[0], wall[1], Color(0.22, 0.20, 0.17)))


func _make_block(pos: Vector3, size: Vector3, color: Color) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.position = pos
	var mesh := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mesh.mesh = bm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mesh.material_override = mat
	body.add_child(mesh)
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	col.shape = shape
	body.add_child(col)
	return body


func _spawn_player() -> CharacterBody3D:
	var p := CharacterBody3D.new()
	p.set_script(load("res://scripts/player.gd"))
	p.position = Vector3(0, 1, 8)
	add_child(p)
	return p


func _spawn_dummies() -> void:
	# Harjoitusrotat: pienet tummat kapselit (placeholder)
	for i in range(3):
		var d := CharacterBody3D.new()
		d.position = Vector3(-6 + i * 6, 0.5, -8)
		var mesh := MeshInstance3D.new()
		var cm := CapsuleMesh.new()
		cm.radius = 0.45
		cm.height = 1.0
		mesh.mesh = cm
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.35, 0.28, 0.24)
		mesh.material_override = mat
		mesh.rotation_degrees.x = 90.0   # rotta makaa vaakatasossa
		d.add_child(mesh)
		var col := CollisionShape3D.new()
		var shape := CapsuleShape3D.new()
		shape.radius = 0.45
		shape.height = 1.0
		col.shape = shape
		d.add_child(col)
		add_child(d)


func _build_camera() -> void:
	var rig := Node3D.new()
	rig.set_script(load("res://scripts/camera_rig.gd"))
	rig.set("target_path", player.get_path())
	add_child(rig)
