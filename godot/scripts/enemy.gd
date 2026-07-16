extends CharacterBody3D
## Vihollisrunko: jahtaa pelaajaa, tekee kontaktivahinkoa, kuuluu
## "enemies"-ryhmään. Kaksi ulkoasua: "grunt" (kapseli) ja "ratman"
## (pystyssä kulkeva rottahumanoidi: kuono, korvat, häntä, punaiset
## silmät). Rotille vikinä-äänet ja aggrohuuto kuplineen.

const CONTACT_CD := 1.0

# Parametrisoitu: metsätien rottamiehet ja areenan harjoitusviholliset
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
var species := "grunt"        # "grunt" | "ratman"
var sfx_hurt := ""
var sfx_die := ""
var sfx_aggro := ""
var bark_text := ""           # aggrohuuto kuplana (esim. "Skreee!")

# Rift Pulse ym. asettavat tämän: työntö joka vaimenee itsestään
var knockback := Vector3.ZERO

var _hit_cd := 0.0
var _mesh: MeshInstance3D
var _mat: StandardMaterial3D
var _aggroed := false


func _ready() -> void:
	add_to_group("enemies")
	if hp < 0.0:
		hp = max_hp
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = body_color
	_mat.roughness = 0.85
	if species == "ratman":
		_build_ratman()
	else:
		_mesh = MeshInstance3D.new()
		var cm := CapsuleMesh.new()
		cm.radius = body_radius
		cm.height = body_height
		_mesh.mesh = cm
		_mesh.material_override = _mat
		add_child(_mesh)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = body_radius
	shape.height = body_height
	col.shape = shape
	add_child(col)


## Rottahumanoidi: kyyry vartalo, kuono, korvat, häntä, hehkuvat silmät
func _build_ratman() -> void:
	_mesh = MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = body_radius
	cm.height = body_height
	_mesh.mesh = cm
	_mesh.material_override = _mat
	_mesh.rotation_degrees.x = 12.0   # kyyry ryhti
	add_child(_mesh)

	var head := MeshInstance3D.new()
	var hs := SphereMesh.new()
	hs.radius = body_radius * 0.55
	hs.height = body_radius * 1.1
	head.mesh = hs
	head.material_override = _mat
	head.position = Vector3(0, body_height * 0.55, -0.12)
	add_child(head)

	# Kuono
	var snout := MeshInstance3D.new()
	var sc := CylinderMesh.new()
	sc.top_radius = 0.02
	sc.bottom_radius = body_radius * 0.3
	sc.height = 0.34
	snout.mesh = sc
	var smat := StandardMaterial3D.new()
	smat.albedo_color = body_color.lightened(0.25)
	snout.material_override = smat
	snout.rotation_degrees.x = -90.0
	snout.position = Vector3(0, body_height * 0.52, -0.38)
	add_child(snout)

	# Korvat
	for dx in [-0.14, 0.14]:
		var ear := MeshInstance3D.new()
		var ec := CylinderMesh.new()
		ec.top_radius = 0.0
		ec.bottom_radius = 0.09
		ec.height = 0.2
		ear.mesh = ec
		ear.material_override = _mat
		ear.position = Vector3(dx, body_height * 0.55 + 0.22, -0.08)
		add_child(ear)

	# Punaiset silmät
	var emat := StandardMaterial3D.new()
	emat.albedo_color = Color(1.0, 0.25, 0.15)
	emat.emission_enabled = true
	emat.emission = Color(1.0, 0.2, 0.1)
	emat.emission_energy_multiplier = 2.0
	for dx in [-0.1, 0.1]:
		var eye := MeshInstance3D.new()
		var es := SphereMesh.new()
		es.radius = 0.035
		es.height = 0.07
		eye.mesh = es
		eye.material_override = emat
		eye.position = Vector3(dx, body_height * 0.58, -0.3)
		add_child(eye)

	# Häntä taakse
	var tail := MeshInstance3D.new()
	var tc := CylinderMesh.new()
	tc.top_radius = 0.015
	tc.bottom_radius = 0.05
	tc.height = 0.9
	tail.mesh = tc
	var tmat := StandardMaterial3D.new()
	tmat.albedo_color = body_color.lightened(0.15)
	tail.mesh = tc
	tail.material_override = tmat
	tail.rotation_degrees.x = 65.0
	tail.position = Vector3(0, 0.05, 0.5)
	add_child(tail)


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
		if not _aggroed:
			_aggroed = true
			if sfx_aggro != "":
				Audio.sfx(sfx_aggro)
			if bark_text != "":
				_bark(bark_text)
		var dir := to_target.normalized()
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed
		look_at(global_position + dir, Vector3.UP)
	else:
		velocity.x = 0.0
		velocity.z = 0.0

	# Työntövoima (Rift Pulse ym.) vaimenee nopeasti
	if knockback.length() > 0.1:
		velocity.x += knockback.x
		velocity.z += knockback.z
		knockback = knockback.lerp(Vector3.ZERO, 10.0 * delta)

	if not is_on_floor():
		velocity.y -= 20.0 * delta
	else:
		velocity.y = 0.0
	move_and_slide()


## Aggrohuuto puhekuplana: nousee ja haalistuu
func _bark(text: String) -> void:
	var lbl := Label3D.new()
	lbl.text = text
	lbl.font_size = 64
	lbl.pixel_size = 0.008
	lbl.modulate = Color(1.0, 0.85, 0.7)
	lbl.outline_size = 18
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.position.y = body_height + 0.6
	add_child(lbl)
	var tw := lbl.create_tween()
	tw.set_parallel(true)
	tw.tween_property(lbl, "position:y", body_height + 1.4, 1.2)
	tw.tween_property(lbl, "modulate:a", 0.0, 1.2)
	tw.chain().tween_callback(lbl.queue_free)


func take_damage(amount: float) -> void:
	hp -= amount
	if sfx_hurt != "" and hp > 0.0:
		Audio.sfx(sfx_hurt)
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
	Audio.sfx(sfx_die if sfx_die != "" else "hit")
	queue_free()
