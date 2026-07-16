extends CharacterBody3D
## Harjoitusvihollinen: tumma kapseli joka jahtaa pelaajaa lähietäisyydellä
## ja tekee kontaktivahinkoa. Kuuluu "enemies"-ryhmään (Commanderin lyönnit
## ja loitsut osuvat ryhmän kautta). Kuolema = punainen purske.

const CONTACT_CD := 1.0

# Parametrisoitu: metsätien rotat ja areenan harjoitusviholliset
# käyttävät samaa runkoa eri arvoilla (aseta ennen add_childia)
var speed := 3.2
var aggro_range := 14.0
var contact_range := 1.4
var contact_dmg := 6.0
var max_hp := 40.0
var hp := -1.0
var body_color := Color(0.42, 0.26, 0.22)
var body_radius := 0.45
var body_height := 1.2
var lying := false   # rotta: kapseli vaakatasossa + kuono

var _hit_cd := 0.0
var _mesh: MeshInstance3D
var _mat: StandardMaterial3D


func _ready() -> void:
	add_to_group("enemies")
	if hp < 0.0:
		hp = max_hp
	_mesh = MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = body_radius
	cm.height = body_height
	_mesh.mesh = cm
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = body_color
	_mesh.material_override = _mat
	add_child(_mesh)

	if lying:
		_mesh.rotation_degrees.x = 90.0
		# Kuono: pieni vaalea kartio eteen
		var snout := MeshInstance3D.new()
		var cone := CylinderMesh.new()
		cone.top_radius = 0.02
		cone.bottom_radius = body_radius * 0.55
		cone.height = 0.4
		snout.mesh = cone
		var smat := StandardMaterial3D.new()
		smat.albedo_color = body_color.lightened(0.25)
		snout.material_override = smat
		snout.rotation_degrees.x = -90.0
		snout.position = Vector3(0, 0.05, -body_height * 0.5 - 0.15)
		add_child(snout)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = body_radius
	shape.height = body_height
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

	if dist <= contact_range and _hit_cd <= 0.0:
		_hit_cd = CONTACT_CD
		if target.has_method("take_damage"):
			target.take_damage(contact_dmg)
	elif dist <= aggro_range and dist > contact_range * 0.8:
		var dir := to_target.normalized()
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed
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
	tw.tween_property(_mat, "albedo_color", body_color, 0.25)
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
