extends Node3D
## Forest Road - pelin avaus (peilaa systems/muckford_forest_tutorial.py +
## npc/commander_npc.py + npc/mnemonic_devourer_npc.py):
## sateinen yömyrsky metsätiellä, 5 opetusvaihetta (liike, lyönti, dash,
## loitsut, tie eteenpäin), Vortex-repeämä, Mnemonic Devourer -dialogi
## valintoineen, skriptattu taistelu (vahva/heikko-haarat) ja lopuksi
## muistinpyyhintä + miekan vienti -> herääminen Muckfordissa.
## KAIKKI grafiikka koodilla: sumu, volyymisumu, sade, salamat, hehkut.

const ROAD_LEN := 150.0
const ROAD_HALF_W := 8.0
const VORTEX_X := 140.0

const STAGES := [
	{"title": "MOVE THROUGH THE STORM",
	 "instr": "Left stick / WASD — move down the road.",
	 "gate": 26.0, "spawn_x": -1.0, "rats": [], "need": ""},
	{"title": "BASIC ATTACK",
	 "instr": "Aim with right stick / mouse, strike with R2 / LMB.",
	 "gate": 52.0, "spawn_x": 38.0,
	 "rats": [{"oz": 0.0, "hp": 24}], "need": ""},
	{"title": "DASH",
	 "instr": "Cross / Space dashes (costs stamina). Finish the pack.",
	 "gate": 78.0, "spawn_x": 64.0,
	 "rats": [{"oz": -2.5, "hp": 26}, {"oz": 2.5, "hp": 26}],
	 "need": "dash"},
	{"title": "VORTEX SKILLS",
	 "instr": "Square/1 Arcane Dart · Triangle/2 Frost Shard · L1/3 Flame Wave.",
	 "gate": 104.0, "spawn_x": 90.0,
	 "rats": [{"oz": -3.0, "hp": 22}, {"oz": 0.0, "hp": 22}, {"oz": 3.0, "hp": 22}],
	 "need": "spell"},
	{"title": "THE ROAD AHEAD",
	 "instr": "Keep moving toward Muckford. Something waits in the rain.",
	 "gate": 128.0, "spawn_x": -1.0, "rats": [], "need": ""},
]

enum Seq { TUTORIAL, VORTEX, FIGHT, DONE }

var player: CharacterBody3D
var dlg: CanvasLayer
var devourer: CharacterBody3D
var seq: Seq = Seq.TUTORIAL

var _stage := 0
var _rats: Array = []
var _spawned := false
var _dash_seen := false
var _spell_seen := false
var _strong_done := false
var _weak_done := false
var _finishing := false

var _moon: DirectionalLight3D
var _flash: ColorRect
var _lightning_t := 4.0
var _vortex: Node3D

var _title_lbl: Label
var _instr_lbl: Label
var _lesson_lbl: Label
var _feedback_lbl: Label
var _feedback_t := 0.0
var _boss_panel: Control
var _boss_fill: ColorRect


func _ready() -> void:
	_build_environment()
	_build_ground()
	_build_forest()
	_spawn_player()
	_build_camera()
	_build_hud()
	_build_tutorial_panel()
	_build_boss_bar()
	dlg = load("res://scripts/dialogue_box.gd").new()
	add_child(dlg)
	add_child(load("res://scripts/pause_menu.gd").new())
	Audio.play_music("storm")
	Audio.play_rain()


func _exit_tree() -> void:
	Audio.stop_rain()


# ---------- Maailma ----------
func _build_environment() -> void:
	_moon = DirectionalLight3D.new()
	_moon.rotation_degrees = Vector3(-50.0, 20.0, 0.0)
	_moon.light_color = Color(0.55, 0.65, 0.95)
	_moon.light_energy = 0.28
	_moon.shadow_enabled = true
	add_child(_moon)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.015, 0.02, 0.035)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.16, 0.18, 0.26)
	e.glow_enabled = true
	e.glow_bloom = 0.15
	e.fog_enabled = true
	e.fog_light_color = Color(0.05, 0.06, 0.10)
	e.fog_density = 0.012
	e.volumetric_fog_enabled = true
	e.volumetric_fog_density = 0.035
	e.volumetric_fog_albedo = Color(0.35, 0.4, 0.55)
	env.environment = e
	add_child(env)


func _build_ground() -> void:
	# Maasto: tumma märkä niitty + mutainen tie + kiiltävät lätäköt
	var ground := StaticBody3D.new()
	var gm := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(ROAD_LEN + 80.0, 90.0)
	gm.mesh = plane
	var gmat := StandardMaterial3D.new()
	gmat.albedo_color = Color(0.07, 0.10, 0.07)
	gmat.roughness = 0.9
	gm.material_override = gmat
	ground.add_child(gm)
	ground.position = Vector3(ROAD_LEN / 2.0, 0, 0)
	var col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(ROAD_LEN + 80.0, 0.1, 90.0)
	col.shape = box
	col.position.y = -0.05
	ground.add_child(col)
	add_child(ground)

	var road := MeshInstance3D.new()
	var rp := PlaneMesh.new()
	rp.size = Vector2(ROAD_LEN + 40.0, ROAD_HALF_W * 2.0)
	road.mesh = rp
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.13, 0.11, 0.085)
	rmat.roughness = 0.75
	road.material_override = rmat
	road.position = Vector3(ROAD_LEN / 2.0, 0.02, 0)
	add_child(road)

	# Lätäköt: matalat kiiltävät kiekot jotka poimivat hehkut
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in range(26):
		var puddle := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.height = 0.015
		cyl.top_radius = rng.randf_range(0.5, 1.6)
		cyl.bottom_radius = cyl.top_radius
		puddle.mesh = cyl
		var pmat := StandardMaterial3D.new()
		pmat.albedo_color = Color(0.04, 0.06, 0.10)
		pmat.roughness = 0.05
		pmat.metallic = 0.7
		puddle.material_override = pmat
		puddle.position = Vector3(rng.randf_range(4.0, ROAD_LEN),
			0.03, rng.randf_range(-ROAD_HALF_W + 1.0, ROAD_HALF_W - 1.0))
		add_child(puddle)


func _build_forest() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	# Tiheät puurivit tien molemmin puolin (2 riviä/puoli)
	for side: float in [-1.0, 1.0]:
		for row in range(2):
			var z_base: float = side * (ROAD_HALF_W + 3.0 + row * 5.0)
			var x := -10.0
			while x < ROAD_LEN + 20.0:
				_add_tree(Vector3(x + rng.randf_range(-2.0, 2.0), 0,
					z_base + rng.randf_range(-1.5, 1.5)),
					rng.randf_range(0.8, 1.6), rng)
				x += rng.randf_range(4.5, 7.5)
	# Tien varren yksityiskohdat: hylätyt kärryt ja lohkareet
	_add_cart(Vector3(30.0, 0, -6.0))
	_add_cart(Vector3(84.0, 0, 5.5))
	_add_rock(Vector3(56.0, 0, 6.5), 1.3)
	_add_rock(Vector3(110.0, 0, -6.0), 1.7)
	_add_rock(Vector3(122.0, 0, 5.0), 1.0)


func _add_tree(pos: Vector3, s: float, rng: RandomNumberGenerator) -> void:
	var tree := Node3D.new()
	tree.position = pos
	tree.rotation.y = rng.randf_range(0.0, TAU)
	tree.scale = Vector3.ONE * s
	var trunk := MeshInstance3D.new()
	var tc := CylinderMesh.new()
	tc.top_radius = 0.18
	tc.bottom_radius = 0.3
	tc.height = 2.4
	trunk.mesh = tc
	var tmat := StandardMaterial3D.new()
	tmat.albedo_color = Color(0.09, 0.07, 0.05)
	trunk.material_override = tmat
	trunk.position.y = 1.2
	tree.add_child(trunk)
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.045, 0.085, 0.055)
	fmat.roughness = 1.0
	for layer in [[2.6, 1.7, 2.0], [4.0, 1.2, 1.6]]:
		var cone := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.0
		cm.bottom_radius = layer[1]
		cm.height = layer[2]
		cone.mesh = cm
		cone.material_override = fmat
		cone.position.y = layer[0]
		tree.add_child(cone)
	add_child(tree)


func _add_cart(pos: Vector3) -> void:
	var cart := Node3D.new()
	cart.position = pos
	var body := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(2.2, 0.8, 1.2)
	body.mesh = bm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.16, 0.11, 0.07)
	body.material_override = mat
	body.position.y = 0.7
	cart.add_child(body)
	for dx in [-0.8, 0.8]:
		var wheel := MeshInstance3D.new()
		var wm := CylinderMesh.new()
		wm.top_radius = 0.45
		wm.bottom_radius = 0.45
		wm.height = 0.12
		wheel.mesh = wm
		wheel.material_override = mat
		wheel.rotation_degrees.x = 90.0
		wheel.position = Vector3(dx, 0.45, 0.65)
		cart.add_child(wheel)
	add_child(cart)


func _add_rock(pos: Vector3, s: float) -> void:
	var rock := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = s
	sm.height = s * 1.2
	rock.mesh = sm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.16, 0.16, 0.18)
	mat.roughness = 0.95
	rock.material_override = mat
	rock.position = pos + Vector3(0, s * 0.25, 0)
	add_child(rock)


func _spawn_player() -> void:
	player = CharacterBody3D.new()
	player.set_script(load("res://scripts/player.gd"))
	player.position = Vector3(3, 1, 0)
	add_child(player)
	player.dashed.connect(func(): _dash_seen = true)
	player.spell_cast.connect(func(_s): _spell_seen = true)
	player.downed.connect(_on_player_downed)
	_attach_rain(player)
	# LOAD GAME tähän skeneen: palauta statit mutta pidä opetus alusta
	var state := SaveGame.consume_pending()
	state.erase("pos")
	if not state.is_empty():
		player.apply_state(state)


## Sade seuraa pelaajaa: GPU-partikkelit laatikosta pelaajan yllä,
## kapeat hehkuvat viirut jotka putoavat nopeasti
func _attach_rain(target: Node3D) -> void:
	var rain := GPUParticles3D.new()
	rain.amount = 1100
	rain.lifetime = 0.7
	rain.visibility_aabb = AABB(Vector3(-30, -14, -30), Vector3(60, 30, 60))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(22, 0.5, 22)
	pm.direction = Vector3(0.15, -1, 0)
	pm.spread = 0.0
	pm.initial_velocity_min = 34.0
	pm.initial_velocity_max = 44.0
	pm.gravity = Vector3(0, -20, 0)
	rain.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(0.025, 0.55)
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.55, 0.65, 0.9, 0.32)
	rmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rmat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	quad.material = rmat
	rain.draw_pass_1 = quad
	rain.position.y = 12.0
	target.add_child(rain)


func _build_camera() -> void:
	var rig := Node3D.new()
	rig.set_script(load("res://scripts/camera_rig.gd"))
	rig.set("target_path", player.get_path())
	add_child(rig)


func _build_hud() -> void:
	var hud := CanvasLayer.new()
	hud.set_script(load("res://scripts/hud.gd"))
	hud.set("player", player)
	add_child(hud)


func _build_tutorial_panel() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.theme = UITheme.build()
	panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.position.y = 28
	panel.custom_minimum_size = Vector2(780, 0)
	layer.add_child(panel)
	var v := VBoxContainer.new()
	panel.add_child(v)
	var top := HBoxContainer.new()
	v.add_child(top)
	_title_lbl = Label.new()
	_title_lbl.add_theme_color_override("font_color", UITheme.GOLD)
	_title_lbl.add_theme_font_size_override("font_size", 26)
	_title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_title_lbl)
	_lesson_lbl = UITheme.hint("")
	top.add_child(_lesson_lbl)
	_instr_lbl = Label.new()
	_instr_lbl.add_theme_font_size_override("font_size", 19)
	v.add_child(_instr_lbl)
	_feedback_lbl = Label.new()
	_feedback_lbl.add_theme_font_size_override("font_size", 18)
	_feedback_lbl.add_theme_color_override("font_color", Color(0.6, 1.0, 0.7))
	v.add_child(_feedback_lbl)

	# Salamavälähdys koko ruudulle
	_flash = ColorRect.new()
	_flash.color = Color(0.85, 0.88, 1.0, 0.0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_flash)
	_refresh_panel()


func _build_boss_bar() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_boss_panel = PanelContainer.new()
	_boss_panel.theme = UITheme.build()
	_boss_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_boss_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_boss_panel.position.y = 150
	_boss_panel.visible = false
	layer.add_child(_boss_panel)
	var v := VBoxContainer.new()
	_boss_panel.add_child(v)
	var name_lbl := Label.new()
	name_lbl.text = "MNEMONIC DEVOURER"
	name_lbl.add_theme_color_override("font_color", Color(0.8, 0.45, 1.0))
	name_lbl.add_theme_font_size_override("font_size", 22)
	name_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(name_lbl)
	var back := ColorRect.new()
	back.color = Color(0.08, 0.05, 0.10, 0.9)
	back.custom_minimum_size = Vector2(560, 16)
	v.add_child(back)
	_boss_fill = ColorRect.new()
	_boss_fill.color = Color(0.62, 0.25, 0.9)
	_boss_fill.position = Vector2(2, 2)
	_boss_fill.size = Vector2(556, 12)
	back.add_child(_boss_fill)


func _refresh_panel() -> void:
	if _stage >= STAGES.size():
		return
	var s: Dictionary = STAGES[_stage]
	_title_lbl.text = str(s["title"])
	_instr_lbl.text = str(s["instr"])
	_lesson_lbl.text = "Lesson %d/%d" % [_stage + 1, STAGES.size()]


func _feedback(msg: String) -> void:
	_feedback_lbl.text = msg
	_feedback_t = 3.0


# ---------- Vaihelogiikka ----------
func _physics_process(delta: float) -> void:
	_tick_lightning(delta)
	if _feedback_t > 0.0:
		_feedback_t -= delta
		if _feedback_t <= 0.0:
			_feedback_lbl.text = ""

	# Pidä pelaaja tiellä
	player.global_position.z = clamp(player.global_position.z,
		-ROAD_HALF_W + 0.6, ROAD_HALF_W - 0.6)
	player.global_position.x = max(player.global_position.x, 1.0)

	match seq:
		Seq.TUTORIAL:
			_update_tutorial()
		Seq.FIGHT:
			_update_fight()
		_:
			pass

	if _boss_panel.visible and devourer:
		_boss_fill.size.x = 556.0 * clamp(devourer.hp / devourer.max_hp, 0.0, 1.0)


func _update_tutorial() -> void:
	var s: Dictionary = STAGES[_stage]
	var gate := float(s["gate"])
	if player.global_position.x > gate:
		player.global_position.x = gate

	var rats_def: Array = s["rats"]
	if rats_def.is_empty():
		# Liikevaiheet: portti avaa seuraavan
		if player.global_position.x >= gate - 1.5:
			if _stage == STAGES.size() - 1:
				seq = Seq.VORTEX
				_opening_sequence()
			else:
				_advance_stage()
		return

	# Spawnaa rotat kun pelaaja lähestyy
	if not _spawned and player.global_position.x >= float(s["spawn_x"]) - 12.0:
		_spawned = true
		for r in rats_def:
			_spawn_rat(Vector3(float(s["spawn_x"]), 0.6, float(r["oz"])),
				float(r["hp"]))
		Audio.sfx("roar")

	if _spawned:
		_rats = _rats.filter(func(r): return is_instance_valid(r))
		if _rats.is_empty():
			# Vaatimustarkistus (py-versio: toista vaihe jos oppi puuttui)
			if s["need"] == "dash" and not _dash_seen:
				_feedback("Use Cross / Space to dash before finishing the pack.")
				_spawned = false
			elif s["need"] == "spell" and not _spell_seen:
				_feedback("Cast a spell: Square / 1 for Arcane Dart.")
				_spawned = false
			else:
				_advance_stage()


func _advance_stage() -> void:
	_stage += 1
	_spawned = false
	_rats = []
	_feedback("Lesson complete")
	player.hp = player.max_hp
	player.mana = player.max_mana
	player.stamina = player.max_stamina
	if _stage == 2:
		_dash_seen = false
	elif _stage == 3:
		_spell_seen = false
	Audio.sfx("confirm")
	_refresh_panel()


func _spawn_rat(pos: Vector3, hp: float) -> void:
	var rat := CharacterBody3D.new()
	rat.set_script(load("res://scripts/enemy.gd"))
	rat.set("max_hp", hp)
	rat.set("speed", 4.2)
	rat.set("contact_dmg", 4.0)
	rat.set("aggro_range", 18.0)
	rat.set("body_color", Color(0.28, 0.20, 0.15))
	rat.set("body_radius", 0.32)
	rat.set("body_height", 0.9)
	rat.set("lying", true)
	rat.position = pos
	add_child(rat)
	_rats.append(rat)


# ---------- Avauskohtaus: Vortex + Devourer ----------
func _opening_sequence() -> void:
	_title_lbl.text = "???"
	_instr_lbl.text = ""
	_lesson_lbl.text = ""
	# Commanderin monologi (npc/commander_npc.py forest_intro)
	await dlg.say("Commander",
		"This weather... it's unnatural. The rain feels heavy, like oil.")
	await dlg.say("Commander",
		"I can feel it in my bones. Something is wrong here. The air tastes of... ash.")
	await dlg.say("Commander",
		"What is that?! A tear in the fabric of the world!")
	dlg.close()

	_spawn_vortex()
	Audio.sfx("thunder")
	await get_tree().create_timer(2.2).timeout

	# Vortex katoaa - sen tilalla seisoo jotain
	_despawn_vortex()
	_spawn_devourer()
	await get_tree().create_timer(0.8).timeout

	await dlg.say("Commander",
		"It vanished... wait. Something stands in its place. The air ripples around it.")
	# Devourer-dialogi (npc/mnemonic_devourer_npc.py)
	await dlg.say("Mnemonic Devourer",
		"There you are. You followed the seam... and you brought it with you.")
	await dlg.say("Mnemonic Devourer",
		"That blade does not belong on this side. Place it on the ground.")
	var pick: int = await dlg.ask("Mnemonic Devourer",
		"Kneel. Do not make me take it the hard way.",
		["No.", "What are you?",
		 "Come closer and I'll cut you down.",
		 "I'm not giving you anything. Tell me why you want it."])
	var responses := [
		"...Expected.",
		"A correction. A hand that erases mistakes.",
		"Do it again.",
		"Because it is yours. And because it is not.",
	]
	await dlg.say("Mnemonic Devourer", responses[pick])
	await dlg.say("Mnemonic Devourer", "Show me what you remember.")
	dlg.close()

	# Taistelu alkaa
	seq = Seq.FIGHT
	devourer.active = true
	_boss_panel.visible = true
	Audio.sfx("roar")
	Input.start_joy_vibration(0, 0.6, 0.9, 0.4)


func _spawn_vortex() -> void:
	_vortex = Node3D.new()
	_vortex.position = Vector3(VORTEX_X, 1.6, 0)
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 1.0
	tm.outer_radius = 1.5
	ring.mesh = tm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.2, 0.9, 0.75)
	mat.emission_enabled = true
	mat.emission = Color(0.2, 0.9, 0.75)
	mat.emission_energy_multiplier = 3.5
	ring.material_override = mat
	ring.rotation_degrees.x = 90.0
	_vortex.add_child(ring)

	var p := CPUParticles3D.new()
	p.amount = 90
	p.lifetime = 1.4
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 1.4
	p.initial_velocity_min = 0.5
	p.initial_velocity_max = 2.0
	p.gravity = Vector3.ZERO
	p.color = Color(0.3, 1.0, 0.85, 0.7)
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.06
	(p.mesh as SphereMesh).height = 0.12
	_vortex.add_child(p)

	var light := OmniLight3D.new()
	light.light_color = Color(0.2, 0.95, 0.8)
	light.omni_range = 14.0
	light.light_energy = 3.5
	_vortex.add_child(light)
	add_child(_vortex)

	# Pyörintä + sykkivä skaala
	var tw := _vortex.create_tween()
	tw.set_loops()
	tw.tween_property(_vortex, "rotation:y", TAU, 2.0).as_relative()


func _despawn_vortex() -> void:
	if _vortex == null:
		return
	var v := _vortex
	_vortex = null
	var tw := v.create_tween()
	tw.tween_property(v, "scale", Vector3.ONE * 0.01, 0.5)
	tw.tween_callback(v.queue_free)
	Audio.sfx("whoosh")


func _spawn_devourer() -> void:
	devourer = CharacterBody3D.new()
	devourer.set_script(load("res://scripts/devourer.gd"))
	devourer.position = Vector3(VORTEX_X, 0.9, 0)
	add_child(devourer)


func _update_fight() -> void:
	if devourer == null or _finishing:
		return
	# Vahva-haara: pelaaja painaa bossin alle 50 % -> keskeytys
	if not _strong_done and devourer.hp <= devourer.max_hp * 0.5:
		_strong_done = true
		_interrupt_strong()
	# Loppu: skripti voittaa aina - alle 15 % käynnistää muistinpyyhinnän
	elif _strong_done and devourer.hp <= devourer.max_hp * 0.15:
		_finishing = true
		_final_sequence()


func _interrupt_strong() -> void:
	devourer.active = false
	await dlg.say("Mnemonic Devourer",
		"...Interesting. You still have teeth. I gave you too much room.")
	await dlg.say("Mnemonic Devourer", "Stop it. STOP IT! No more games.")
	await dlg.say("Mnemonic Devourer",
		"I didn't come here to die. I came here to *take you apart*.")
	await dlg.say("Mnemonic Devourer", "This is not over. You will fall.")
	dlg.close()
	devourer.enraged = true
	devourer.hp_floor = devourer.max_hp * 0.15
	devourer.active = true
	Audio.sfx("roar")


func _on_player_downed() -> void:
	if seq != Seq.FIGHT or _finishing:
		return
	if _weak_done:
		return
	_weak_done = true
	_weak_branch()


func _weak_branch() -> void:
	devourer.active = false
	await dlg.say("Mnemonic Devourer",
		"Heh... heh... heh. That's all? You walked this far... for that?")
	await dlg.say("Mnemonic Devourer",
		"Pathetic. I expected more from the one who carries the seam.")
	await dlg.say("Mnemonic Devourer",
		"Your struggle is amusing. Let's continue.")
	dlg.close()
	if not _finishing:
		devourer.active = true


func _final_sequence() -> void:
	devourer.active = false
	_boss_panel.visible = false
	await dlg.say("Mnemonic Devourer", "You misunderstand. I'm not here to kill you.")
	await dlg.say("Mnemonic Devourer", "That would be wasteful. You have a place in this.")
	await dlg.say("Mnemonic Devourer", "Hold still. Let go.")
	await dlg.say("Mnemonic Devourer", "Forget.")
	# Muistinpyyhintä: valkoinen välähdys + terä viedään
	_flash.color.a = 1.0
	Audio.sfx("thunder")
	Input.start_joy_vibration(0, 1.0, 1.0, 0.6)
	var tw := create_tween()
	tw.tween_property(_flash, "color:a", 0.0, 1.2)
	player.set_has_sword(false)
	player.spells.clear()
	await dlg.say("Mnemonic Devourer", "Good. That belongs to the wound.")
	await dlg.say("Mnemonic Devourer", "I'll keep what you can't.")
	await dlg.say("Mnemonic Devourer",
		"When you wake... you won't even know what you lost.")
	dlg.close()
	# Blackout -> herääminen Muckfordissa
	SaveGame.transfer_state = {
		"hp": player.max_hp, "mana": player.max_mana,
		"stamina": player.max_stamina,
		"has_sword": false, "spells": [], "level": player.level,
	}
	Router.goto("res://scenes/muckford.tscn", false)


# ---------- Salamat ----------
func _tick_lightning(delta: float) -> void:
	_lightning_t -= delta
	if _lightning_t <= 0.0:
		_lightning_t = randf_range(5.0, 13.0)
		_flash.color.a = 0.55
		_moon.light_energy = 1.6
		var tw := create_tween()
		tw.set_parallel(true)
		tw.tween_property(_flash, "color:a", 0.0, 0.45)
		tw.tween_property(_moon, "light_energy", 0.28, 0.5)
		Audio.sfx("thunder")
