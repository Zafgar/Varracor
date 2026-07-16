extends CharacterBody3D
## Harjoitusvihollinen: tumma kapseli joka jahtaa pelaajaa lähietäisyydellä
## ja tekee kontaktivahinkoa. Kuuluu "enemies"-ryhmään (Commanderin lyönnit
## ja loitsut osuvat ryhmän kautta). Kuolema = punainen purske.

const SPEED := 3.2
const AGGRO_RANGE := 14.0
const CONTACT_RANGE := 1.4
const CONTACT_DMG := 6.0
const CONTACT_CD := 1.0

var max_hp := 40.0
var hp := 40.0

var _hit_cd := 0.0
var _mesh: MeshInstance3D
var _mat: StandardMaterial3D


func _ready() -> void:
	add_to_group("enemies")
	_mesh = MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.45
	cm.height = 1.2
	_mesh.mesh = cm
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = Color(0.42, 0.26, 0.22)
	_mesh.material_override = _mat
	add_child(_mesh)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.45
	shape.height = 1.2
	col.shape = shape
	add_child(col)


func _physics_process(delta: float) -> void:
	_hit_cd = max(0.0, _hit_cd - delta)
	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		return
	var target := players[0] as Node3D
	var to_target := target.global_position - global_position
	to_target.y = 0.0
	var dist := to_target.length()

	if dist <= CONTACT_RANGE and _hit_cd <= 0.0:
		_hit_cd = CONTACT_CD
		if target.has_method("take_damage"):
			target.take_damage(CONTACT_DMG)
	elif dist <= AGGRO_RANGE and dist > CONTACT_RANGE * 0.8:
		var dir := to_target.normalized()
		velocity.x = dir.x * SPEED
		velocity.z = dir.z * SPEED
		look_at(global_position + dir, Vector3.UP)
	else:
		velocity.x = 0.0
		velocity.z = 0.0

	if not is_on_floor():
		velocity.y -= 20.0 * delta
	else:
		velocity.y = 0.0
	move_and_slide()


func take_damage(amount: float) -> void:
	hp -= amount
	# Osumavälähdys: hetkeksi vaaleampi
	_mat.albedo_color = Color(0.9, 0.5, 0.4)
	var tw := create_tween()
	tw.tween_property(_mat, "albedo_color", Color(0.42, 0.26, 0.22), 0.25)
	if hp <= 0.0:
		_die()


func _die() -> void:
	var p := CPUParticles3D.new()
	p.position = global_position
	p.emitting = true
	p.one_shot = true
	p.amount = 32
	p.lifetime = 0.6
	p.explosiveness = 1.0
	p.initial_velocity_min = 3.0
	p.initial_velocity_max = 8.0
	p.spread = 180.0
	p.color = Color(0.8, 0.25, 0.2)
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.06
	(p.mesh as SphereMesh).height = 0.12
	get_parent().add_child(p)
	var timer := get_tree().create_timer(0.8)
	timer.timeout.connect(p.queue_free)
	Audio.sfx("hit")
	queue_free()
