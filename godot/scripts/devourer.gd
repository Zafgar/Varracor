extends CharacterBody3D
## Mnemonic Devourer: intron skriptattu bossi. Kyvyt peilaavat py-versiota
## (units/mnemonic_devourer.py):
##   1. VORTEX BARRAGE - kirkuu ja ampuu sarjan hakeutuvia varjoammuksia
##   2. TELEPORT STRIKE - katoaa purskeeseen, ilmestyy pelaajan taakse, isku
##   3. VORTEX PULL (vain raivona) - imee pelaajan luokseen
## Ulkoasu: leijuva kaapuhahmo - viittakartio, hehkuvat violetit silmät,
## lonkerokruunu, pyörivä auralenkki jaloissa, varjopartikkeliverho.
## Tarina voittaa aina: forest_road.gd ohjaa hp_floor-lattiaa.

signal hp_changed

const CONTACT_RANGE := 2.2
const CONTACT_CD := 1.4

var max_hp := 420.0
var hp := 420.0
var hp_floor := 60.0        # skripti laskee tätä vaiheittain
var active := false          # false = seisoo paikallaan, haavoittumaton
var enraged := false

var _hit_cd := 0.0
var _t := 0.0
var _vis: Node3D
var _aura: MeshInstance3D
var _mat: StandardMaterial3D

# Kykyjen tila (py: ability_1/2/3)
var _barrage_cd := 4.0
var _barrage_shots := 0
var _barrage_t := 0.0
var _tp_cd := 8.0
var _tp_phase := 0
var _tp_t := 0.0
var _pull_cd := 6.0
var _pull_t := 0.0


func _ready() -> void:
	add_to_group("enemies")
	_vis = Node3D.new()
	add_child(_vis)

	# Viittakartio alaosaan (leijuva kaapu)
	var cloak := MeshInstance3D.new()
	var cc := CylinderMesh.new()
	cc.top_radius = 0.55
	cc.bottom_radius = 1.25
	cc.height = 2.2
	cloak.mesh = cc
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = Color(0.05, 0.04, 0.08)
	_mat.emission_enabled = true
	_mat.emission = Color(0.30, 0.10, 0.45)
	_mat.emission_energy_multiplier = 0.35
	cloak.material_override = _mat
	cloak.position.y = 0.4
	_vis.add_child(cloak)

	# Ylävartalo + pää
	var torso := MeshInstance3D.new()
	var tm := CapsuleMesh.new()
	tm.radius = 0.55
	tm.height = 1.8
	torso.mesh = tm
	torso.material_override = _mat
	torso.position.y = 1.9
	_vis.add_child(torso)
	var head := MeshInstance3D.new()
	var hs := SphereMesh.new()
	hs.radius = 0.38
	hs.height = 0.76
	head.mesh = hs
	head.material_override = _mat
	head.position.y = 2.9
	_vis.add_child(head)

	# Lonkerokruunu: taipuneet piikit pään ympärillä
	for i in range(6):
		var a := TAU * i / 6.0
		var tendril := MeshInstance3D.new()
		var tc := CylinderMesh.new()
		tc.top_radius = 0.015
		tc.bottom_radius = 0.06
		tc.height = 0.85
		tendril.mesh = tc
		tendril.material_override = _mat
		tendril.position = Vector3(cos(a) * 0.3, 3.25, sin(a) * 0.3)
		tendril.rotation_degrees = Vector3(
			cos(a) * 35.0, 0, -sin(a) * 35.0)
		_vis.add_child(tendril)

	# Silmät: kaksi hehkuvaa violettia palloa
	var emat := StandardMaterial3D.new()
	emat.albedo_color = Color(0.85, 0.4, 1.0)
	emat.emission_enabled = true
	emat.emission = Color(0.85, 0.4, 1.0)
	emat.emission_energy_multiplier = 5.0
	for dx in [-0.16, 0.16]:
		var eye := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		eye.mesh = sm
		eye.material_override = emat
		eye.position = Vector3(dx, 2.92, -0.33)
		_vis.add_child(eye)

	# Auralenkki jaloissa (pyörii hitaasti)
	_aura = MeshInstance3D.new()
	var am := TorusMesh.new()
	am.inner_radius = 1.1
	am.outer_radius = 1.35
	_aura.mesh = am
	var amat := StandardMaterial3D.new()
	amat.albedo_color = Color(0.5, 0.2, 0.8, 0.7)
	amat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	amat.emission_enabled = true
	amat.emission = Color(0.5, 0.2, 0.8)
	amat.emission_energy_multiplier = 1.8
	_aura.material_override = amat
	_aura.position.y = -0.55
	_vis.add_child(_aura)

	# Varjoverho: leijuva tumma-violetti partikkelikehä
	var p := CPUParticles3D.new()
	p.amount = 80
	p.lifetime = 2.4
	p.preprocess = 2.0
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 1.3
	p.gravity = Vector3(0, 0.9, 0)
	p.initial_velocity_min = 0.2
	p.initial_velocity_max = 0.8
	p.color = Color(0.35, 0.15, 0.5, 0.5)
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.07
	(p.mesh as SphereMesh).height = 0.14
	p.position.y = 1.4
	_vis.add_child(p)

	var light := OmniLight3D.new()
	light.light_color = Color(0.55, 0.25, 0.85)
	light.omni_range = 10.0
	light.light_energy = 2.4
	light.position.y = 2.0
	_vis.add_child(light)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.8
	shape.height = 3.4
	col.shape = shape
	col.position.y = 1.4
	add_child(col)


func _physics_process(delta: float) -> void:
	_t += delta
	# Uhkaava leijunta + auran pyörintä aina
	_vis.position.y = 0.25 + sin(_t * 1.4) * 0.15
	_aura.rotation.y += delta * 0.8
	if not active:
		return

	_hit_cd = max(0.0, _hit_cd - delta)
	var cd_rate := 2.0 if enraged else 1.0   # raivona kyvyt latautuvat 2x
	_barrage_cd = max(0.0, _barrage_cd - delta * cd_rate)
	_tp_cd = max(0.0, _tp_cd - delta * cd_rate)
	_pull_cd = max(0.0, _pull_cd - delta * cd_rate)

	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		return
	var target := players[0] as Node3D
	var to_target := target.global_position - global_position
	to_target.y = 0.0
	var dist := to_target.length()
	var dir := to_target.normalized()
	look_at(global_position + dir, Vector3.UP)

	# Käynnissä olevat kyvyt ajavat kaiken muun yli
	if _barrage_shots > 0:
		_run_barrage(delta, target)
		return
	if _tp_phase > 0:
		_run_teleport(delta, target)
		return
	if _pull_t > 0.0:
		_run_pull(delta, target)
		return

	# Kykyjen aloitus (py-prioriteetit: pull raivona, teleport kaukaa,
	# barrage muuten)
	if enraged and _pull_cd <= 0.0 and dist < 12.0 and dist > 3.0:
		_pull_cd = 10.0
		_pull_t = 0.9
		Audio.sfx("drain")
		return
	if _tp_cd <= 0.0 and dist > 7.0:
		_tp_cd = 9.0
		_tp_phase = 1
		_tp_t = 0.45
		Audio.sfx("warp")
		_warp_burst()
		_vis.visible = false
		return
	if _barrage_cd <= 0.0:
		_barrage_cd = 11.0
		_barrage_shots = 8 if enraged else 5
		_barrage_t = 0.0
		Audio.sfx("shriek")
		return

	# Perusliike + kontakti-isku
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


## Kyky 1: VORTEX BARRAGE - ammussarja paikallaan kirkuen
func _run_barrage(delta: float, target: Node3D) -> void:
	_barrage_t -= delta
	if _barrage_t <= 0.0:
		_barrage_t = 0.32
		_barrage_shots -= 1
		var dir := (target.global_position - global_position)
		dir.y = 0.0
		dir = dir.normalized()
		_shoot_bolt(dir, 12 if enraged else 9)
		# Silmien välähdys joka laukauksella
		_mat.emission_energy_multiplier = 1.2
		var tw := create_tween()
		tw.tween_property(_mat, "emission_energy_multiplier",
			0.9 if enraged else 0.35, 0.25)


## Kyky 2: TELEPORT STRIKE - katoa, ilmesty pelaajan taakse, iske
func _run_teleport(delta: float, target: Node3D) -> void:
	_tp_t -= delta
	if _tp_t > 0.0:
		return
	if _tp_phase == 1:
		# Ilmesty pelaajan taakse
		var behind: Vector3 = -target.global_transform.basis.z
		behind.y = 0.0
		global_position = target.global_position \
			- behind.normalized() * 2.2 + Vector3.UP * 0.0
		global_position.y = 0.9
		_vis.visible = true
		_warp_burst()
		Audio.sfx("warp")
		_tp_phase = 2
		_tp_t = 0.35   # lyhyt ennakointi ennen iskua
	elif _tp_phase == 2:
		_tp_phase = 0
		var dist := global_position.distance_to(target.global_position)
		if dist < 3.2 and target.has_method("take_damage"):
			target.take_damage(22.0 if enraged else 16.0)
			Audio.sfx("roar")
			Input.start_joy_vibration(0, 0.7, 1.0, 0.3)


## Kyky 3: VORTEX PULL - imee pelaajaa kohti (vain raivotilassa)
func _run_pull(delta: float, target: Node3D) -> void:
	_pull_t -= delta
	var pull_dir := global_position - target.global_position
	pull_dir.y = 0.0
	if pull_dir.length() > 2.0:
		target.global_position += pull_dir.normalized() * 9.0 * delta
	if _pull_t <= 0.0 and target.has_method("take_damage"):
		target.take_damage(10.0)


func _shoot_bolt(dir: Vector3, dmg: int) -> void:
	var bolt := Area3D.new()
	bolt.set_script(load("res://scripts/bolt.gd"))
	bolt.set("damage", dmg)
	bolt.set("direction", dir)
	bolt.set("tint", Color(0.6, 0.25, 0.95))
	bolt.set("hits_group", "player")
	bolt.position = global_position + dir * 1.4 + Vector3.UP * 2.6
	get_parent().add_child(bolt)


func _warp_burst() -> void:
	var p := CPUParticles3D.new()
	p.position = global_position + Vector3.UP * 1.5
	p.emitting = true
	p.one_shot = true
	p.amount = 40
	p.lifetime = 0.5
	p.explosiveness = 1.0
	p.initial_velocity_min = 3.0
	p.initial_velocity_max = 9.0
	p.spread = 180.0
	p.color = Color(0.6, 0.3, 0.95)
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.06
	(p.mesh as SphereMesh).height = 0.12
	get_parent().add_child(p)
	get_tree().create_timer(0.7).timeout.connect(p.queue_free)


func take_damage(amount: float) -> void:
	if not active:
		return   # ennen taistelua haavoittumaton
	hp = max(hp_floor, hp - amount)
	_mat.emission_energy_multiplier = 1.4
	var tw := create_tween()
	tw.tween_property(_mat, "emission_energy_multiplier",
		0.9 if enraged else 0.35, 0.3)
	hp_changed.emit()
