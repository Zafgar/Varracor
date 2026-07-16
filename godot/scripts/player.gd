class_name Commander
extends CharacterBody3D
## Commander: pelaajan koko toimintapaketti top-down 3D:ssä.
## MOLEMMAT ohjaustavat toimivat rinnakkain:
##   PS5: vasen tatti liike, oikea tatti tähtäys, R2 lyönti, Cross dash,
##        Square/Triangle/L1 loitsut 1-3 (+ DualSense-tärinä)
##   KB+hiiri: WASD liike, hiiri tähtäys (raycast lattiatasoon), LMB lyönti,
##        Space dash, 1/2/3 loitsut
## Statit tulevat samasta käyrästä kuin py-versiossa (Catalogs.stat_target),
## loitsuvahingot samasta skaalauksesta (Catalogs.scaled_damage).

signal stats_changed
signal spell_cast(slot: int)
signal dashed
signal downed

const SPEED := 8.0
const DASH_SPEED := 22.0
const DASH_TIME := 0.15
const DASH_STAMINA := 25.0
const ATTACK_RANGE := 2.2
const ATTACK_CD := 0.45
const AOE_RADIUS := 6.0

# Arkkityyppikohtaiset cooldownit (nopea nuke, hitaampi aoe)
const ARCH_CD := {"nuke": 1.5, "aoe": 2.5, "dot": 2.2}

# Intron Vortex-kyvyt (py: SeamCut/VortexWarp/RiftPulse) - miekan lainaamat
# voimat, eivät katalogiloitsuja. Devourer vie ne intron lopussa;
# Commander oppii ne uudelleen Path of the Vortexin kautta.
const VORTEX_SPELLS := {
	"vortex_slash": {"name": "Vortex Slash", "mana": 10.0, "cd": 1.1},
	"vortex_warp": {"name": "Vortex Warp", "mana": 14.0, "cd": 4.0},
	"rift_pulse": {"name": "Rift Pulse", "mana": 20.0, "cd": 6.0},
}
const VORTEX_TEAL := Color(0.2, 0.95, 0.78)

var level := 5
var max_hp := 100.0
var hp := 100.0
var max_mana := 60.0
var mana := 60.0
var max_stamina := 100.0
var stamina := 100.0
var strength := 10
var intelligence := 10

# Kolme loitsupaikkaa (Square/1, Triangle/2, L1/3) - katalogista
var spells: Array[String] = ["arcane_dart", "frost_shard", "flame_wave"]
var cooldowns: Array[float] = [0.0, 0.0, 0.0]

# Vortex-miekka: Devourer vie sen intron lopussa (tarina) - ilman
# miekkaa lyönti on nyrkki-isku ja terän hehku puuttuu
var has_sword := true

var _dash_left := 0.0
var _dash_dir := Vector3.ZERO
var _attack_cd := 0.0
var _swing := 0.0
var _aim := Vector3.FORWARD
var _sword: Node3D


func _ready() -> void:
	add_to_group("player")
	_init_stats()
	_build_body()


func _init_stats() -> void:
	# Sama kasvukäyrä kuin py-versiossa: stat_target(level) jaetaan
	# attribuutteihin, HP/mana skaalautuvat siitä
	var target := Catalogs.stat_target(level)
	strength = max(5, int(target * 0.5))
	intelligence = max(5, int(target * 0.5))
	max_hp = 100.0 + target * 2.0
	max_mana = 40.0 + target * 1.5
	hp = max_hp
	mana = max_mana
	stamina = max_stamina
	stats_changed.emit()


func _build_body() -> void:
	# Vartalo: teräksensininen haarniska
	var torso := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.42
	cm.height = 1.5
	torso.mesh = cm
	var tmat := StandardMaterial3D.new()
	tmat.albedo_color = Color(0.22, 0.32, 0.52)
	tmat.metallic = 0.35
	tmat.roughness = 0.55
	torso.material_override = tmat
	torso.position.y = -0.1
	add_child(torso)

	# Rintapanssari: vaaleampi metallilevy kultaviivalla
	var chest := MeshInstance3D.new()
	var chb := BoxMesh.new()
	chb.size = Vector3(0.62, 0.55, 0.28)
	chest.mesh = chb
	var chmat := StandardMaterial3D.new()
	chmat.albedo_color = Color(0.42, 0.50, 0.62)
	chmat.metallic = 0.7
	chmat.roughness = 0.35
	chest.material_override = chmat
	chest.position = Vector3(0, 0.15, -0.28)
	add_child(chest)
	var trim := MeshInstance3D.new()
	var trb := BoxMesh.new()
	trb.size = Vector3(0.64, 0.06, 0.30)
	trim.mesh = trb
	var trmat := StandardMaterial3D.new()
	trmat.albedo_color = Color(0.86, 0.72, 0.35)
	trmat.metallic = 0.85
	trmat.roughness = 0.25
	trim.material_override = trmat
	trim.position = Vector3(0, 0.42, -0.28)
	add_child(trim)

	# Olkapanssarit
	var smat := StandardMaterial3D.new()
	smat.albedo_color = Color(0.30, 0.36, 0.46)
	smat.metallic = 0.6
	smat.roughness = 0.4
	for dx in [-0.5, 0.5]:
		var pad := MeshInstance3D.new()
		var pm := SphereMesh.new()
		pm.radius = 0.20
		pm.height = 0.30
		pad.mesh = pm
		pad.material_override = smat
		pad.position = Vector3(dx, 0.52, 0)
		add_child(pad)

	# Pää + tumma visiiri
	var head := MeshInstance3D.new()
	var hm := SphereMesh.new()
	hm.radius = 0.26
	hm.height = 0.52
	head.mesh = hm
	var hmat := StandardMaterial3D.new()
	hmat.albedo_color = Color(0.35, 0.40, 0.50)
	hmat.metallic = 0.5
	head.material_override = hmat
	head.position.y = 0.95
	add_child(head)
	var visor := MeshInstance3D.new()
	var vb := BoxMesh.new()
	vb.size = Vector3(0.34, 0.09, 0.12)
	visor.mesh = vb
	var vmat := StandardMaterial3D.new()
	vmat.albedo_color = Color(0.05, 0.08, 0.10)
	vmat.emission_enabled = true
	vmat.emission = VORTEX_TEAL
	vmat.emission_energy_multiplier = 0.5
	visor.material_override = vmat
	visor.position = Vector3(0, 0.97, -0.22)
	add_child(visor)

	# Viitta: tummanpunainen levy selässä
	var cape := MeshInstance3D.new()
	var cb := BoxMesh.new()
	cb.size = Vector3(0.66, 1.25, 0.05)
	cape.mesh = cb
	var cmat := StandardMaterial3D.new()
	cmat.albedo_color = Color(0.38, 0.10, 0.10)
	cmat.roughness = 0.9
	cape.material_override = cmat
	cape.position = Vector3(0, -0.05, 0.30)
	cape.rotation_degrees.x = -6.0
	add_child(cape)

	_sword = _build_sword()
	_sword.position = Vector3(0.55, 0.15, -0.35)
	_sword.visible = has_sword
	add_child(_sword)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.45
	shape.height = 1.8
	col.shape = shape
	add_child(col)


## Vortex Blade: kahva + kultainen väistin ja ponsi, teräslapa jonka
## molemmissa syrjissä hehkuva vortex-särmä, kärki kapenee - oma valo
func _build_sword() -> Node3D:
	var sword := Node3D.new()

	var grip := MeshInstance3D.new()
	var gc := CylinderMesh.new()
	gc.top_radius = 0.045
	gc.bottom_radius = 0.05
	gc.height = 0.28
	grip.mesh = gc
	var gmat := StandardMaterial3D.new()
	gmat.albedo_color = Color(0.16, 0.10, 0.07)
	gmat.roughness = 0.85
	grip.material_override = gmat
	grip.rotation_degrees.x = 90.0
	grip.position.z = 0.30
	sword.add_child(grip)

	var gold := StandardMaterial3D.new()
	gold.albedo_color = Color(0.86, 0.70, 0.30)
	gold.metallic = 0.9
	gold.roughness = 0.25
	var pommel := MeshInstance3D.new()
	var pms := SphereMesh.new()
	pms.radius = 0.06
	pms.height = 0.12
	pommel.mesh = pms
	pommel.material_override = gold
	pommel.position.z = 0.46
	sword.add_child(pommel)
	var guard := MeshInstance3D.new()
	var gb := BoxMesh.new()
	gb.size = Vector3(0.30, 0.06, 0.07)
	guard.mesh = gb
	guard.material_override = gold
	guard.position.z = 0.14
	sword.add_child(guard)

	var blade := MeshInstance3D.new()
	var bb := BoxMesh.new()
	bb.size = Vector3(0.14, 0.035, 0.95)
	blade.mesh = bb
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(0.75, 0.80, 0.88)
	bmat.metallic = 0.9
	bmat.roughness = 0.2
	blade.material_override = bmat
	blade.position.z = -0.38
	sword.add_child(blade)

	# Hehkuvat vortex-särmät terän molemmin puolin
	var emat := StandardMaterial3D.new()
	emat.albedo_color = VORTEX_TEAL
	emat.emission_enabled = true
	emat.emission = VORTEX_TEAL
	emat.emission_energy_multiplier = 2.4
	for dx in [-0.075, 0.075]:
		var edge := MeshInstance3D.new()
		var eb := BoxMesh.new()
		eb.size = Vector3(0.015, 0.04, 0.95)
		edge.mesh = eb
		edge.material_override = emat
		edge.position = Vector3(dx, 0, -0.38)
		sword.add_child(edge)

	# Kärki
	var tip := MeshInstance3D.new()
	var tp := PrismMesh.new()
	tp.size = Vector3(0.14, 0.22, 0.035)
	tip.mesh = tp
	tip.material_override = emat
	tip.rotation_degrees.x = -90.0
	tip.position.z = -0.965
	sword.add_child(tip)

	var light := OmniLight3D.new()
	light.light_color = VORTEX_TEAL
	light.omni_range = 2.6
	light.light_energy = 0.7
	light.position.z = -0.5
	sword.add_child(light)
	return sword


func _physics_process(delta: float) -> void:
	_tick_timers(delta)
	_update_aim()
	_move(delta)
	_face_aim()
	_handle_actions()
	_regen(delta)


func _tick_timers(delta: float) -> void:
	_attack_cd = max(0.0, _attack_cd - delta)
	for i in range(cooldowns.size()):
		cooldowns[i] = max(0.0, cooldowns[i] - delta)
	if _swing > 0.0:
		_swing = max(0.0, _swing - delta * 6.0)
		_sword.rotation.y = -_swing * 2.4


## Tähtäys: oikea tatti voittaa jos sitä käytetään, muuten hiiren
## sijainti raycastattuna lattiatasoon (y=0) - molemmat toimivat aina.
func _update_aim() -> void:
	var stick := Input.get_vector("aim_left", "aim_right", "aim_up", "aim_down")
	if stick.length() > 0.35:
		_aim = Vector3(stick.x, 0, stick.y).normalized()
		return
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var mp := get_viewport().get_mouse_position()
	var from := cam.project_ray_origin(mp)
	var dir := cam.project_ray_normal(mp)
	if abs(dir.y) < 0.001:
		return
	var t := -from.y / dir.y
	if t <= 0.0:
		return
	var hit := from + dir * t
	var flat := Vector3(hit.x - global_position.x, 0, hit.z - global_position.z)
	if flat.length() > 0.4:
		_aim = flat.normalized()


func _move(delta: float) -> void:
	var stick := Input.get_vector("move_left", "move_right",
								  "move_up", "move_down")
	var input := Vector3(stick.x, 0, stick.y)

	if _dash_left > 0.0:
		_dash_left -= delta
		velocity.x = _dash_dir.x * DASH_SPEED
		velocity.z = _dash_dir.z * DASH_SPEED
	else:
		if Input.is_action_just_pressed("dash") and input != Vector3.ZERO \
				and stamina >= DASH_STAMINA:
			stamina -= DASH_STAMINA
			_dash_left = DASH_TIME
			_dash_dir = input.normalized()
			Audio.sfx("whoosh")
			Input.start_joy_vibration(0, 0.35, 0.6, 0.15)
			dashed.emit()
		velocity.x = input.x * SPEED
		velocity.z = input.z * SPEED

	if not is_on_floor():
		velocity.y -= 20.0 * delta
	else:
		velocity.y = 0.0
	move_and_slide()


## Twin-stick-tyyli: hahmo katsoo AINA tähtäyssuuntaan, ei liikesuuntaan
func _face_aim() -> void:
	if _aim.length() > 0.1:
		look_at(global_position + _aim, Vector3.UP)


func _handle_actions() -> void:
	if Input.is_action_just_pressed("attack"):
		_melee()
	for i in range(spells.size()):
		if Input.is_action_just_pressed("cast_%d" % (i + 1)):
			_cast(i)


func _melee() -> void:
	if _attack_cd > 0.0:
		return
	_attack_cd = ATTACK_CD
	_swing = 1.0
	Audio.sfx("hit")
	Input.start_joy_vibration(0, 0.2, 0.4, 0.1)
	var dmg := (8.0 + strength * 0.6) if has_sword else (3.0 + strength * 0.3)
	var origin := global_position + _aim * (ATTACK_RANGE * 0.5)
	for e in get_tree().get_nodes_in_group("enemies"):
		if e is Node3D and origin.distance_to(e.global_position) <= ATTACK_RANGE:
			if e.has_method("take_damage"):
				e.take_damage(dmg)


## HUD:n käyttämät apurit: nimi ja cooldownin maksimi slotille
func spell_display_name(slot: int) -> String:
	if slot >= spells.size():
		return "-"
	var id: String = spells[slot]
	if VORTEX_SPELLS.has(id):
		return str(VORTEX_SPELLS[id]["name"])
	return str(Catalogs.spell_spec(id).get("name", id))


func cooldown_max(slot: int) -> float:
	if slot >= spells.size():
		return 1.0
	var id: String = spells[slot]
	if VORTEX_SPELLS.has(id):
		return float(VORTEX_SPELLS[id]["cd"])
	var spec := Catalogs.spell_spec(id)
	return float(ARCH_CD.get(str(spec.get("archetype", "nuke")), 1.8))


func _cast(slot: int) -> void:
	if slot >= spells.size() or cooldowns[slot] > 0.0:
		return
	if VORTEX_SPELLS.has(spells[slot]):
		_cast_vortex(slot)
		return
	var spec := Catalogs.spell_spec(spells[slot])
	if spec.is_empty():
		return
	var tier := int(spec.get("tier", 1))
	var archetype := str(spec.get("archetype", "nuke"))
	var cost := float(Catalogs.spells.get("tier_mana", {}).get(str(tier), 12))
	if mana < cost:
		Audio.sfx("back")
		return
	mana -= cost
	cooldowns[slot] = ARCH_CD.get(archetype, 1.8)
	var dmg := Catalogs.scaled_damage(tier, intelligence, archetype)
	Audio.sfx("whoosh")
	Input.start_joy_vibration(0, 0.3, 0.5, 0.12)
	spell_cast.emit(slot)
	if archetype == "aoe":
		_cast_nova(dmg, spec)
	else:
		_cast_bolt(dmg, spec)
	stats_changed.emit()


# ---- Vortex-kyvyt (intro; py: SeamCut / VortexWarp / RiftPulse) ----
func _cast_vortex(slot: int) -> void:
	var id: String = spells[slot]
	var spec: Dictionary = VORTEX_SPELLS[id]
	var cost := float(spec["mana"])
	if mana < cost:
		Audio.sfx("back")
		return
	mana -= cost
	cooldowns[slot] = float(spec["cd"])
	spell_cast.emit(slot)
	match id:
		"vortex_slash":
			_vortex_slash()
		"vortex_warp":
			_vortex_warp()
		"rift_pulse":
			_rift_pulse()
	stats_changed.emit()


## Leveä viilto: kolmen teal-säteen viuhka lyhyellä kantamalla
func _vortex_slash() -> void:
	_swing = 1.0
	Audio.sfx("whoosh")
	Input.start_joy_vibration(0, 0.3, 0.5, 0.1)
	var dmg := Catalogs.scaled_damage(2, intelligence, "nuke")
	for angle in [-0.35, 0.0, 0.35]:
		var dir := _aim.rotated(Vector3.UP, angle)
		var bolt := Area3D.new()
		bolt.set_script(load("res://scripts/bolt.gd"))
		bolt.set("damage", dmg)
		bolt.set("direction", dir)
		bolt.set("tint", VORTEX_TEAL)
		bolt.set("lifetime_override", 0.28)
		bolt.position = global_position + dir * 0.9 + Vector3.UP * 0.4
		get_parent().add_child(bolt)


## Teleporttihyppy tähtäyssuuntaan: lähtö- ja saapumispurske
func _vortex_warp() -> void:
	Audio.sfx("warp")
	Input.start_joy_vibration(0, 0.4, 0.7, 0.15)
	_warp_burst(global_position)
	global_position += _aim * 7.0
	_warp_burst(global_position)


func _warp_burst(pos: Vector3) -> void:
	var p := CPUParticles3D.new()
	p.position = pos + Vector3.UP * 0.5
	p.emitting = true
	p.one_shot = true
	p.amount = 36
	p.lifetime = 0.5
	p.explosiveness = 1.0
	p.initial_velocity_min = 3.0
	p.initial_velocity_max = 8.0
	p.spread = 180.0
	p.color = VORTEX_TEAL
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.05
	(p.mesh as SphereMesh).height = 0.1
	get_parent().add_child(p)
	get_tree().create_timer(0.7).timeout.connect(p.queue_free)


## Hätäpulssi: laajeneva rengas joka vahingoittaa JA työntää viholliset
func _rift_pulse() -> void:
	Audio.sfx("shriek")
	Input.start_joy_vibration(0, 0.6, 0.9, 0.25)
	var dmg := Catalogs.scaled_damage(2, intelligence, "aoe")
	for e in get_tree().get_nodes_in_group("enemies"):
		if e is Node3D and global_position.distance_to(e.global_position) <= AOE_RADIUS:
			if e.has_method("take_damage"):
				e.take_damage(float(dmg))
			var push: Vector3 = e.global_position - global_position
			push.y = 0.0
			if e.get("knockback") != null:
				e.set("knockback", push.normalized() * 14.0)
	_nova_ring(VORTEX_TEAL)


func _nova_ring(color: Color) -> void:
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.8
	tm.outer_radius = 1.0
	ring.mesh = tm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 2.5
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring.material_override = mat
	ring.position = global_position + Vector3.UP * 0.2
	get_parent().add_child(ring)
	var tw := ring.create_tween()
	tw.set_parallel(true)
	tw.tween_property(ring, "scale", Vector3.ONE * AOE_RADIUS, 0.4)
	tw.tween_property(mat, "albedo_color:a", 0.0, 0.4)
	tw.chain().tween_callback(ring.queue_free)


func _cast_bolt(dmg: int, spec: Dictionary) -> void:
	var bolt := Area3D.new()
	bolt.set_script(load("res://scripts/bolt.gd"))
	bolt.set("damage", dmg)
	bolt.set("direction", _aim)
	bolt.set("tint", _damage_color(str(spec.get("damage_type", "Arcane"))))
	bolt.position = global_position + _aim * 0.9 + Vector3.UP * 0.4
	get_parent().add_child(bolt)


## AOE-loitsu: laajeneva rengas pelaajan ympärille, osuu kaikkiin lähellä
func _cast_nova(dmg: int, spec: Dictionary) -> void:
	for e in get_tree().get_nodes_in_group("enemies"):
		if e is Node3D and global_position.distance_to(e.global_position) <= AOE_RADIUS:
			if e.has_method("take_damage"):
				e.take_damage(float(dmg))
	_nova_ring(_damage_color(str(spec.get("damage_type", "Fire"))))


static func _damage_color(damage_type: String) -> Color:
	match damage_type:
		"Fire": return Color(1.0, 0.45, 0.15)
		"Frost": return Color(0.4, 0.75, 1.0)
		"Poison": return Color(0.45, 0.9, 0.3)
		"Holy": return Color(1.0, 0.95, 0.6)
		"Shadow": return Color(0.6, 0.3, 0.9)
		_: return Color(0.55, 0.5, 1.0)   # Arcane


func _regen(delta: float) -> void:
	stamina = min(max_stamina, stamina + 18.0 * delta)
	mana = min(max_mana, mana + 3.0 * delta)


func take_damage(amount: float) -> void:
	hp = max(0.0, hp - amount)
	Audio.sfx("hit")
	Input.start_joy_vibration(0, 0.5, 0.8, 0.2)
	stats_changed.emit()
	if hp <= 0.0:
		# Prototyyppi: kuolema palauttaa täysiin voimiin paikallaan.
		# downed-signaali antaa skenen reagoida (esim. Devourer-taistelun
		# heikko-haara intron aikana).
		downed.emit()
		hp = max_hp
		mana = max_mana


# ---- Tallennus (SaveGame käyttää näitä) ----
func set_has_sword(v: bool) -> void:
	has_sword = v
	if _sword:
		_sword.visible = v


func state_dict() -> Dictionary:
	return {
		"pos": [global_position.x, global_position.y, global_position.z],
		"hp": hp, "mana": mana, "stamina": stamina,
		"level": level, "spells": spells,
		"has_sword": has_sword,
		"scene": get_tree().current_scene.scene_file_path,
	}


func apply_state(d: Dictionary) -> void:
	level = int(d.get("level", level))
	_init_stats()
	var p: Array = d.get("pos", [])
	if p.size() == 3:
		global_position = Vector3(p[0], p[1], p[2])
	hp = clamp(float(d.get("hp", max_hp)), 1.0, max_hp)
	mana = clamp(float(d.get("mana", max_mana)), 0.0, max_mana)
	stamina = clamp(float(d.get("stamina", max_stamina)), 0.0, max_stamina)
	if d.has("spells"):
		spells.clear()
		for s in d["spells"]:
			spells.append(str(s))
	set_has_sword(bool(d.get("has_sword", true)))
	stats_changed.emit()
