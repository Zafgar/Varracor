extends CharacterBody3D
## Pelaajan top-down 3D -ohjaus: WASD liikkuu maailmatasossa, hahmo
## kääntyy kulkusuuntaan. Placeholder-hahmo (kapseli + "miekka").
## Peilaa py-version Commanderin liikettä; kyvyt/loitsut portataan
## GODOT_PORT.md:n vaiheissa.

const SPEED := 8.0
const DASH_SPEED := 22.0
const DASH_TIME := 0.15

var _dash_left := 0.0
var _dash_dir := Vector3.ZERO


func _ready() -> void:
	# Placeholder-runko: sininen kapseli + miekkapalkki (koodilla, ei asseteja)
	var mesh := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.45
	cm.height = 1.8
	mesh.mesh = cm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.25, 0.45, 0.85)
	mesh.material_override = mat
	mesh.position.y = 0.0
	add_child(mesh)

	var sword := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.12, 0.12, 1.2)
	sword.mesh = bm
	var smat := StandardMaterial3D.new()
	smat.albedo_color = Color(0.8, 0.8, 0.85)
	smat.emission_enabled = true
	smat.emission = Color(0.2, 0.9, 0.75)  # vortex-hehku
	smat.emission_energy_multiplier = 0.6
	sword.material_override = smat
	sword.position = Vector3(0.55, 0.2, -0.5)
	add_child(sword)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.45
	shape.height = 1.8
	col.shape = shape
	add_child(col)


func _physics_process(delta: float) -> void:
	var input := Vector3.ZERO
	# Suorat näppäintarkistukset - ei riippuvuutta input map -määrityksiin
	if Input.is_physical_key_pressed(KEY_W):
		input.z -= 1.0
	if Input.is_physical_key_pressed(KEY_S):
		input.z += 1.0
	if Input.is_physical_key_pressed(KEY_A):
		input.x -= 1.0
	if Input.is_physical_key_pressed(KEY_D):
		input.x += 1.0
	input = input.normalized()

	if _dash_left > 0.0:
		_dash_left -= delta
		velocity.x = _dash_dir.x * DASH_SPEED
		velocity.z = _dash_dir.z * DASH_SPEED
	else:
		if Input.is_physical_key_pressed(KEY_SPACE) and input != Vector3.ZERO:
			_dash_left = DASH_TIME
			_dash_dir = input
		velocity.x = input.x * SPEED
		velocity.z = input.z * SPEED

	if not is_on_floor():
		velocity.y -= 20.0 * delta
	else:
		velocity.y = 0.0

	move_and_slide()

	# Käänny kulkusuuntaan
	var flat := Vector3(velocity.x, 0, velocity.z)
	if flat.length() > 0.1:
		look_at(global_position + flat, Vector3.UP)
