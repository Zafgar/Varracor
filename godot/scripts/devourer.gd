extends CharacterBody3D
## Mnemonic Devourer: intron skriptattu bossi. Korkea lähes musta hahmo,
## hehkuvat violetit silmät, pyörivä varjopartikkeliverho + violetti valo.
## Tarina voittaa aina: forest_road.gd keskeyttää taistelun HP-rajoilla
## (vahva-haara) ja päättää sen muistinpyyhintään - hp ei laske alle
## lattian ennen kuin skripti sallii.

signal hp_changed

const CONTACT_RANGE := 2.2
const CONTACT_CD := 1.4

var max_hp := 420.0
var hp := 420.0
var hp_floor := 60.0        # skripti laskee tätä vaiheittain
var active := false          # false = seisoo paikallaan, haavoittumaton
var enraged := false

var _hit_cd := 0.0
var _bolt_cd := 3.0
var _mat: StandardMaterial3D
var _t := 0.0


func _ready() -> void:
	add_to_group("enemies")
	# Runko: korkea tumma kapseli
	var mesh := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.8
	cm.height = 3.4
	mesh.mesh = cm
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = Color(0.06, 0.05, 0.09)
	_mat.emission_enabled = true
	_mat.emission = Color(0.30, 0.10, 0.45)
	_mat.emission_energy_multiplier = 0.35
	mesh.material_override = _mat
	mesh.position.y = 0.6
	add_child(mesh)

	# Silmät: kaksi hehkuvaa violettia palloa
	for dx in [-0.28, 0.28]:
		var eye := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.09
		sm.height = 0.18
		eye.mesh = sm
		var emat := StandardMaterial3D.new()
		emat.albedo_color = Color(0.85, 0.4, 1.0)
		emat.emission_enabled = true
		emat.emission = Color(0.85, 0.4, 1.0)
		emat.emission_energy_multiplier = 5.0
		eye.material_override = emat
		eye.position = Vector3(dx, 2.0, -0.65)
		add_child(eye)

	# Varjoverho: hitaasti leijuva tumma-violetti partikkelikehä
	var p := CPUParticles3D.new()
	p.amount = 60
	p.lifetime = 2.2
	p.preprocess = 2.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 1.2
	p.gravity = Vector3(0, 0.8, 0)
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.7
	p.color = Color(0.35, 0.15, 0.5, 0.5)
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.07
	(p.mesh as SphereMesh).height = 0.14
	p.position.y = 1.2
	add_child(p)

	var light := OmniLight3D.new()
	light.light_color = Color(0.55, 0.25, 0.85)
	light.omni_range = 9.0
	light.light_energy = 2.2
	light.position.y = 1.8
	add_child(light)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.8
	shape.height = 3.4
	col.shape = shape
	col.position.y = 0.6
	add_child(col)


func _physics_process(delta: float) -> void:
	_t += delta
	# Uhkaava leijunta paikallaan
	if not active:
		return
	_hit_cd = max(0.0, _hit_cd - delta)
	_bolt_cd = max(0.0, _bolt_cd - delta)

	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		return
	var target := players[0] as Node3D
	var to_target := target.global_position - global_position
	to_target.y = 0.0
	var dist := to_target.length()
	var dir := to_target.normalized()
	look_at(global_position + dir, Vector3.UP)

	var speed := 3.4 if enraged else 2.2
	if dist <= CONTACT_RANGE and _hit_cd <= 0.0:
		_hit_cd = CONTACT_CD
		if target.has_method("take_damage"):
			target.take_damage(18.0 if enraged else 12.0)
		Audio.sfx("roar")
	elif dist > CONTACT_RANGE * 0.8:
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed
		move_and_slide()

	# Varjoammus: violetti bolt kohti pelaajaa
	if _bolt_cd <= 0.0 and dist > 3.0:
		_bolt_cd = 1.6 if enraged else 2.8
		var bolt := Area3D.new()
		bolt.set_script(load("res://scripts/bolt.gd"))
		bolt.set("damage", 16 if enraged else 10)
		bolt.set("direction", dir)
		bolt.set("tint", Color(0.6, 0.25, 0.95))
		bolt.set("hits_group", "player")
		bolt.position = global_position + dir * 1.4 + Vector3.UP * 1.8
		get_parent().add_child(bolt)
		Audio.sfx("whoosh")


func take_damage(amount: float) -> void:
	if not active:
		return   # ennen taistelua haavoittumaton
	hp = max(hp_floor, hp - amount)
	_mat.emission_energy_multiplier = 1.4
	var tw := create_tween()
	tw.tween_property(_mat, "emission_energy_multiplier",
		0.9 if enraged else 0.35, 0.3)
	hp_changed.emit()
