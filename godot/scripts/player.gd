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
var _sword: MeshInstance3D


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
	var mesh := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.45
	cm.height = 1.8
	mesh.mesh = cm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.25, 0.45, 0.85)
	mesh.material_override = mat
	add_child(mesh)

	_sword = MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.12, 0.12, 1.2)
	_sword.mesh = bm
	var smat := StandardMaterial3D.new()
	smat.albedo_color = Color(0.8, 0.8, 0.85)
	smat.emission_enabled = true
	smat.emission = Color(0.2, 0.9, 0.75)  # vortex-hehku
	smat.emission_energy_multiplier = 0.6
	_sword.material_override = smat
	_sword.position = Vector3(0.55, 0.2, -0.5)
	_sword.visible = has_sword
	add_child(_sword)

	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.45
	shape.height = 1.8
	col.shape = shape
	add_child(col)


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


func _cast(slot: int) -> void:
	if slot >= spells.size() or cooldowns[slot] > 0.0:
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
	# Rengas-VFX: laajeneva torus joka haalistuu
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.8
	tm.outer_radius = 1.0
	ring.mesh = tm
	var mat := StandardMaterial3D.new()
	var c := _damage_color(str(spec.get("damage_type", "Fire")))
	mat.albedo_color = c
	mat.emission_enabled = true
	mat.emission = c
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
