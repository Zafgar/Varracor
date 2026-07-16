extends Node3D
## Muckford v2 - Tier 0 -suokaupunki, layout suunniteltu py-version pohjalta
## (citys/mucford) mutta hienompana. Commander saapuu metsätieltä lännestä.
##
##   LAYOUT (x itään, z etelään, tori origossa):
##     luoteessa maatila peltoineen · pohjoisessa Town Hall · koillisessa
##     barracks · torin pohjoislaidalla 5 kojua (market_data.py:n liikkeet)
##     · torin itälaidalla Griznakin vankkurit · kaakossa paja ahjoineen ·
##     lounaassa The Sunk Cask + laituri suolammelle · kaakon portti
##     Shanty Yard -areenalle · idän portti kaivostielle (lukossa) ·
##     etelässä ja lännessä suolampia kaisloineen ja tulikärpäsineen
##
## Grafiikka koodilla: aamu-usva, lämpimät hehkuvat ikkunat, lyhdyt,
## savupiiput savuineen, laudoitetut kulkutiet, kuljeskelevat kyläläiset.

const STALLS := [
	{"name": "Fenna's Greenmarket", "canopy": Color(0.30, 0.50, 0.25)},
	{"name": "Grett's Scrap Arms", "canopy": Color(0.45, 0.30, 0.20)},
	{"name": "The Mudguard", "canopy": Color(0.35, 0.35, 0.45)},
	{"name": "The Bittersip", "canopy": Color(0.50, 0.35, 0.15)},
	{"name": "Krad's Oddments", "canopy": Color(0.40, 0.25, 0.40)},
]

var player: CharacterBody3D


func _ready() -> void:
	_build_environment()
	_build_ground()
	_build_buildings()
	_build_market()
	_build_swamp()
	_build_details()
	_spawn_villagers()
	_spawn_player()
	_build_camera()
	_build_hud()
	add_child(load("res://scripts/pause_menu.gd").new())
	_build_commander_menu()
	Audio.play_music("town")
	_show_title()


## Commander-menu (M / touchpad): hahmopaneeli + alueen kartta
func _build_commander_menu() -> void:
	var menu := CanvasLayer.new()
	menu.set_script(load("res://scripts/commander_menu.gd"))
	menu.set("player", player)
	menu.set("area_title", "MUCKFORD — Tier 0")
	menu.set("world_rect", Rect2(-45, -30, 85, 60))
	menu.set("map_features", [
		{"pos": Vector2(-32, 4), "size": Vector2(30, 6),
		 "color": Color(0.25, 0.20, 0.14), "label": "Forest Road"},
		{"pos": Vector2(0, 0), "size": Vector2(36, 26),
		 "color": Color(0.24, 0.23, 0.20), "label": ""},
		{"pos": Vector2(-16, 22), "size": Vector2(22, 12),
		 "color": Color(0.12, 0.22, 0.18), "label": ""},
		{"pos": Vector2(20, 24), "size": Vector2(14, 9),
		 "color": Color(0.12, 0.22, 0.18), "label": ""},
		{"pos": Vector2(-34, -18), "size": Vector2(12, 10),
		 "color": Color(0.12, 0.22, 0.18), "label": ""},
		{"pos": Vector2(-14, 11), "size": Vector2(10, 7),
		 "color": Color(0.38, 0.27, 0.16), "label": "The Sunk Cask"},
		{"pos": Vector2(16, 6), "size": Vector2(6, 5),
		 "color": Color(0.36, 0.26, 0.16), "label": "Smithy"},
		{"pos": Vector2(15, -13), "size": Vector2(8, 6),
		 "color": Color(0.33, 0.28, 0.22), "label": "Barracks"},
		{"pos": Vector2(0, -16), "size": Vector2(9, 6),
		 "color": Color(0.40, 0.34, 0.26), "label": "Town Hall"},
		{"pos": Vector2(-18, -12), "size": Vector2(6, 5),
		 "color": Color(0.34, 0.26, 0.17), "label": "Hobb's Farm"},
		{"pos": Vector2(-24, -4), "size": Vector2(9, 7),
		 "color": Color(0.22, 0.34, 0.14), "label": ""},
		{"pos": Vector2(13, 1), "size": Vector2(4, 2),
		 "color": Color(0.55, 0.44, 0.28), "label": "Griznak"},
		{"pos": Vector2(10, 17), "size": Vector2(5, 2),
		 "color": Color(0.72, 0.58, 0.28), "label": "Arena"},
		{"pos": Vector2(27, 0), "size": Vector2(2, 6),
		 "color": Color(0.45, 0.40, 0.34), "label": "Mine Road"},
	])
	add_child(menu)


# ---------- Valo ja ilma ----------
func _build_environment() -> void:
	# Matala aamuaurinko idästä - pitkät varjot torin yli
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-28.0, -65.0, 0.0)
	sun.light_color = Color(1.0, 0.86, 0.65)
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	add_child(sun)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.62, 0.68, 0.72)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.52, 0.54, 0.50)
	e.glow_enabled = true
	e.fog_enabled = true
	e.fog_light_color = Color(0.72, 0.74, 0.70)
	e.fog_density = 0.006
	# Kevyt aamu-usva makaa suon päällä
	e.volumetric_fog_enabled = true
	e.volumetric_fog_density = 0.012
	e.volumetric_fog_albedo = Color(0.75, 0.78, 0.72)
	env.environment = e
	add_child(env)


# ---------- Maasto ----------
func _build_ground() -> void:
	var ground := StaticBody3D.new()
	var gm := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(140, 120)
	gm.mesh = plane
	var gmat := StandardMaterial3D.new()
	gmat.albedo_color = Color(0.17, 0.22, 0.13)
	gmat.roughness = 0.95
	gm.material_override = gmat
	ground.add_child(gm)
	var col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(140, 0.1, 120)
	col.shape = box
	col.position.y = -0.05
	ground.add_child(col)
	add_child(ground)

	# Torin mukulakivipohja + saapumistie lännestä
	_flat(Vector3(0, 0.02, 0), Vector2(36, 26), Color(0.30, 0.28, 0.24))
	_flat(Vector3(-32, 0.02, 4), Vector2(30, 6), Color(0.22, 0.18, 0.13))
	# Kivilaattoja torille (yksityiskohta)
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in range(24):
		_flat(Vector3(rng.randf_range(-16.0, 16.0), 0.03,
			rng.randf_range(-11.0, 11.0)),
			Vector2(rng.randf_range(0.8, 1.8), rng.randf_range(0.8, 1.8)),
			Color(0.34, 0.32, 0.28))


func _flat(pos: Vector3, size: Vector2, color: Color) -> void:
	var m := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = size
	m.mesh = pm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.9
	m.material_override = mat
	m.position = pos
	add_child(m)


# ---------- Rakennukset ----------
func _build_buildings() -> void:
	# The Sunk Cask: iso taverna lounaassa, ovi torille päin
	_add_house(Vector3(-14, 0, 11), Vector3(10, 4.5, 7),
		Color(0.30, 0.22, 0.14), "The Sunk Cask", 180.0)
	# Paja kaakossa + ahjo
	_add_house(Vector3(16, 0, 6), Vector3(6, 3.5, 5),
		Color(0.28, 0.21, 0.13), "Smithy", -90.0)
	_add_forge(Vector3(12.2, 0, 8.5))
	# Barracks koillisessa
	_add_house(Vector3(15, 0, -13), Vector3(8, 4, 6),
		Color(0.25, 0.22, 0.18), "Barracks", 135.0)
	# Town Hall pohjoisessa banderolleineen
	_add_house(Vector3(0, 0, -16), Vector3(9, 5, 6),
		Color(0.32, 0.28, 0.22), "Town Hall", 0.0)
	_add_banner(Vector3(-3.2, 0, -12.4))
	_add_banner(Vector3(3.2, 0, -12.4))
	# Maatila luoteessa + aidattu pelto
	_add_house(Vector3(-18, 0, -12), Vector3(6, 3, 5),
		Color(0.26, 0.20, 0.14), "Hobb's Farm", 90.0)
	_add_field(Vector3(-24, 0, -4), Vector2(9, 7))

	# Portti Shanty Yard -areenalle (kaakko)
	_add_gate(Vector3(10, 0, 17), "SHANTY YARD ARENA",
		"res://scenes/main.tscn")
	# Kaivostien portti idässä - vielä lukossa (avain Mardalta py-tarinassa)
	_add_locked_gate(Vector3(27, 0, 0), "MINE ROAD — LOCKED")


func _add_house(pos: Vector3, size: Vector3, color: Color,
		sign_text: String, face_deg: float) -> void:
	var house := StaticBody3D.new()
	house.position = pos
	house.rotation_degrees.y = face_deg
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = color
	wmat.roughness = 0.9

	var walls := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	walls.mesh = bm
	walls.material_override = wmat
	walls.position.y = size.y / 2.0
	house.add_child(walls)
	# Hirsiraidat seiniin (kapeat tummemmat listat)
	var smat := StandardMaterial3D.new()
	smat.albedo_color = color.darkened(0.35)
	for i in range(1, int(size.y)):
		var strip := MeshInstance3D.new()
		var sb := BoxMesh.new()
		sb.size = Vector3(size.x + 0.04, 0.08, size.z + 0.04)
		strip.mesh = sb
		strip.material_override = smat
		strip.position.y = float(i)
		house.add_child(strip)

	var roof := MeshInstance3D.new()
	var pm := PrismMesh.new()
	pm.size = Vector3(size.x + 1.0, size.y * 0.55, size.z + 1.0)
	roof.mesh = pm
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.18, 0.09, 0.07)
	roof.material_override = rmat
	roof.position.y = size.y + size.y * 0.275
	house.add_child(roof)

	# Savupiippu + savu
	var chimney := MeshInstance3D.new()
	var cb := BoxMesh.new()
	cb.size = Vector3(0.7, 1.6, 0.7)
	chimney.mesh = cb
	var cmat := StandardMaterial3D.new()
	cmat.albedo_color = Color(0.30, 0.30, 0.32)
	chimney.material_override = cmat
	chimney.position = Vector3(size.x * 0.3, size.y + size.y * 0.5, 0)
	house.add_child(chimney)
	var smoke := CPUParticles3D.new()
	smoke.amount = 14
	smoke.lifetime = 4.0
	smoke.preprocess = 4.0
	smoke.initial_velocity_min = 0.4
	smoke.initial_velocity_max = 0.8
	smoke.direction = Vector3(0.3, 1, 0)
	smoke.spread = 12.0
	smoke.gravity = Vector3.ZERO
	smoke.scale_amount_min = 1.0
	smoke.scale_amount_max = 2.4
	smoke.color = Color(0.7, 0.7, 0.72, 0.25)
	smoke.mesh = SphereMesh.new()
	(smoke.mesh as SphereMesh).radius = 0.25
	(smoke.mesh as SphereMesh).height = 0.5
	smoke.position = chimney.position + Vector3(0, 1.0, 0)
	house.add_child(smoke)

	# Ovi + lämpimät ikkunat etuseinään
	var dmat := StandardMaterial3D.new()
	dmat.albedo_color = Color(0.12, 0.08, 0.05)
	var door := MeshInstance3D.new()
	var dm := BoxMesh.new()
	dm.size = Vector3(1.1, 2.0, 0.15)
	door.mesh = dm
	door.material_override = dmat
	door.position = Vector3(0, 1.0, -size.z / 2.0 - 0.06)
	house.add_child(door)
	var wgmat := StandardMaterial3D.new()
	wgmat.albedo_color = Color(1.0, 0.75, 0.35)
	wgmat.emission_enabled = true
	wgmat.emission = Color(1.0, 0.65, 0.25)
	wgmat.emission_energy_multiplier = 1.4
	for dx in [-size.x * 0.3, size.x * 0.3]:
		var win := MeshInstance3D.new()
		var wb := BoxMesh.new()
		wb.size = Vector3(0.9, 0.9, 0.1)
		win.mesh = wb
		win.material_override = wgmat
		win.position = Vector3(dx, size.y * 0.55, -size.z / 2.0 - 0.06)
		house.add_child(win)

	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	col.shape = shape
	col.position.y = size.y / 2.0
	house.add_child(col)

	if sign_text != "":
		var lbl := Label3D.new()
		lbl.text = sign_text
		lbl.font_size = 110
		lbl.pixel_size = 0.008
		lbl.modulate = UITheme.GOLD
		lbl.outline_size = 24
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.position.y = size.y + size.y * 0.7
		house.add_child(lbl)
	add_child(house)


func _add_forge(pos: Vector3) -> void:
	# Ulkoahjo: kivipesä jossa hehkuva hiillos, alasin ja kipinät
	var forge := Node3D.new()
	forge.position = pos
	var hearth := MeshInstance3D.new()
	var hb := BoxMesh.new()
	hb.size = Vector3(1.6, 1.0, 1.6)
	hearth.mesh = hb
	var hmat := StandardMaterial3D.new()
	hmat.albedo_color = Color(0.25, 0.25, 0.27)
	hearth.material_override = hmat
	hearth.position.y = 0.5
	forge.add_child(hearth)
	var coals := MeshInstance3D.new()
	var cb := BoxMesh.new()
	cb.size = Vector3(1.2, 0.15, 1.2)
	coals.mesh = cb
	var comat := StandardMaterial3D.new()
	comat.albedo_color = Color(1.0, 0.4, 0.1)
	comat.emission_enabled = true
	comat.emission = Color(1.0, 0.35, 0.05)
	comat.emission_energy_multiplier = 2.6
	coals.material_override = comat
	coals.position.y = 1.05
	forge.add_child(coals)
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.5, 0.15)
	light.omni_range = 7.0
	light.light_energy = 1.8
	light.position.y = 1.6
	forge.add_child(light)
	# Alasin
	var anvil := MeshInstance3D.new()
	var ab := BoxMesh.new()
	ab.size = Vector3(0.9, 0.35, 0.35)
	anvil.mesh = ab
	var amat := StandardMaterial3D.new()
	amat.albedo_color = Color(0.15, 0.15, 0.17)
	amat.metallic = 0.6
	anvil.material_override = amat
	anvil.position = Vector3(1.6, 0.75, 0)
	forge.add_child(anvil)
	var base := MeshInstance3D.new()
	var bb := CylinderMesh.new()
	bb.top_radius = 0.25
	bb.bottom_radius = 0.3
	bb.height = 0.6
	base.mesh = bb
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(0.2, 0.14, 0.09)
	base.material_override = bmat
	base.position = Vector3(1.6, 0.3, 0)
	forge.add_child(base)
	add_child(forge)


func _add_banner(pos: Vector3) -> void:
	var pole := MeshInstance3D.new()
	var pc := CylinderMesh.new()
	pc.top_radius = 0.06
	pc.bottom_radius = 0.08
	pc.height = 4.5
	pole.mesh = pc
	var pmat := StandardMaterial3D.new()
	pmat.albedo_color = Color(0.2, 0.15, 0.1)
	pole.material_override = pmat
	pole.position = pos + Vector3(0, 2.25, 0)
	add_child(pole)
	var flag := MeshInstance3D.new()
	var fb := BoxMesh.new()
	fb.size = Vector3(0.06, 1.6, 1.0)
	flag.mesh = fb
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.55, 0.42, 0.15)
	flag.material_override = fmat
	flag.position = pos + Vector3(0, 3.6, 0.55)
	add_child(flag)


func _add_field(pos: Vector3, size: Vector2) -> void:
	# Tumma multa + satorivit + riukuaita
	_flat(pos + Vector3(0, 0.02, 0), size, Color(0.16, 0.11, 0.07))
	var cmat := StandardMaterial3D.new()
	cmat.albedo_color = Color(0.25, 0.45, 0.18)
	for row in range(3):
		for i in range(6):
			var crop := MeshInstance3D.new()
			var cc := CylinderMesh.new()
			cc.top_radius = 0.0
			cc.bottom_radius = 0.22
			cc.height = 0.5
			crop.mesh = cc
			crop.material_override = cmat
			crop.position = pos + Vector3(
				-size.x / 2.0 + 1.0 + i * (size.x - 2.0) / 5.0,
				0.25,
				-size.y / 2.0 + 1.2 + row * (size.y - 2.4) / 2.0)
			add_child(crop)
	# Aita: tolpat + vaakariu'ut
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.22, 0.16, 0.10)
	var half_x := size.x / 2.0
	var half_z := size.y / 2.0
	for t in range(5):
		for sz in [-half_z, half_z]:
			_fence_post(pos + Vector3(-half_x + t * half_x / 2.0, 0, sz), fmat)
	for sx in [-half_x, half_x]:
		for t in range(3):
			_fence_post(pos + Vector3(sx, 0, -half_z + t * half_z), fmat)


func _fence_post(pos: Vector3, mat: StandardMaterial3D) -> void:
	var post := MeshInstance3D.new()
	var pc := CylinderMesh.new()
	pc.top_radius = 0.06
	pc.bottom_radius = 0.07
	pc.height = 1.0
	post.mesh = pc
	post.material_override = mat
	post.position = pos + Vector3(0, 0.5, 0)
	add_child(post)


func _add_gate(pos: Vector3, label: String, target_scene: String) -> void:
	# Kaksi kivipylvästä + poikkipuu + kyltti; Area3D vie kohteeseen
	var gate := Node3D.new()
	gate.position = pos
	var pmat := StandardMaterial3D.new()
	pmat.albedo_color = Color(0.32, 0.32, 0.34)
	for dx in [-2.2, 2.2]:
		var pillar := MeshInstance3D.new()
		var pb := BoxMesh.new()
		pb.size = Vector3(0.9, 3.6, 0.9)
		pillar.mesh = pb
		pillar.material_override = pmat
		pillar.position = Vector3(dx, 1.8, 0)
		gate.add_child(pillar)
	var beam := MeshInstance3D.new()
	var bb := BoxMesh.new()
	bb.size = Vector3(5.6, 0.5, 0.7)
	beam.mesh = bb
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(0.22, 0.16, 0.10)
	beam.material_override = bmat
	beam.position.y = 3.8
	gate.add_child(beam)
	var lbl := Label3D.new()
	lbl.text = label
	lbl.font_size = 100
	lbl.pixel_size = 0.008
	lbl.modulate = UITheme.GOLD
	lbl.outline_size = 24
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.position.y = 4.6
	gate.add_child(lbl)
	var area := Area3D.new()
	var acol := CollisionShape3D.new()
	var abox := BoxShape3D.new()
	abox.size = Vector3(4.0, 4.0, 2.0)
	acol.shape = abox
	acol.position.y = 1.5
	area.add_child(acol)
	area.body_entered.connect(func(body: Node3D):
		if body.is_in_group("player"):
			# Deferred: skeneä ei saa vaihtaa kesken physics-callbackin
			Router.goto.call_deferred(target_scene))
	gate.add_child(area)
	add_child(gate)


func _add_locked_gate(pos: Vector3, label: String) -> void:
	var gate := StaticBody3D.new()
	gate.position = pos
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.20, 0.14, 0.09)
	var doors := MeshInstance3D.new()
	var db := BoxMesh.new()
	db.size = Vector3(0.5, 3.2, 6.0)
	doors.mesh = db
	doors.material_override = wood
	doors.position.y = 1.6
	gate.add_child(doors)
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(0.5, 3.2, 6.0)
	col.shape = shape
	col.position.y = 1.6
	gate.add_child(col)
	var lbl := Label3D.new()
	lbl.text = label
	lbl.font_size = 80
	lbl.pixel_size = 0.008
	lbl.modulate = UITheme.MUTED
	lbl.outline_size = 24
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.position.y = 4.2
	gate.add_child(lbl)
	add_child(gate)


# ---------- Tori ----------
func _build_market() -> void:
	# 5 kojua torin pohjoislaidalla (liikkeet citys/mucford/market_data.py)
	for i in range(STALLS.size()):
		var x := -12.0 + i * 6.0
		_add_stall(Vector3(x, 0, -9.5), STALLS[i])
	# Kaivo torin keskellä
	var well := StaticBody3D.new()
	well.position = Vector3(0, 0, 1)
	var wm := MeshInstance3D.new()
	var wc := CylinderMesh.new()
	wc.top_radius = 1.1
	wc.bottom_radius = 1.25
	wc.height = 1.0
	wm.mesh = wc
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = Color(0.36, 0.36, 0.38)
	wm.material_override = wmat
	wm.position.y = 0.5
	well.add_child(wm)
	var roof := MeshInstance3D.new()
	var rp := PrismMesh.new()
	rp.size = Vector3(2.4, 0.9, 2.4)
	roof.mesh = rp
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.18, 0.09, 0.07)
	roof.material_override = rmat
	roof.position.y = 2.6
	well.add_child(roof)
	var wcol := CollisionShape3D.new()
	var wsh := CylinderShape3D.new()
	wsh.radius = 1.25
	wsh.height = 1.0
	wcol.shape = wsh
	wcol.position.y = 0.5
	well.add_child(wcol)
	add_child(well)
	# Griznakin vankkurit torin itälaidalla (AINA kaupungissa, kuten py:ssä)
	_add_caravan(Vector3(13, 0, 1))


func _add_stall(pos: Vector3, spec: Dictionary) -> void:
	var stall := StaticBody3D.new()
	stall.position = pos
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.24, 0.17, 0.11)
	# Myyntipöytä
	var table := MeshInstance3D.new()
	var tb := BoxMesh.new()
	tb.size = Vector3(3.4, 0.9, 1.2)
	table.mesh = tb
	table.material_override = wood
	table.position.y = 0.45
	stall.add_child(table)
	# Tolpat + katos
	for dx in [-1.5, 1.5]:
		for dz in [-0.5, 0.5]:
			var pole := MeshInstance3D.new()
			var pc := CylinderMesh.new()
			pc.top_radius = 0.05
			pc.bottom_radius = 0.05
			pc.height = 2.4
			pole.mesh = pc
			pole.material_override = wood
			pole.position = Vector3(dx, 1.2, dz)
			stall.add_child(pole)
	var canopy := MeshInstance3D.new()
	var cb := BoxMesh.new()
	cb.size = Vector3(3.8, 0.12, 1.8)
	canopy.mesh = cb
	var cmat := StandardMaterial3D.new()
	cmat.albedo_color = spec["canopy"]
	canopy.mesh = cb
	canopy.material_override = cmat
	canopy.position.y = 2.5
	canopy.rotation_degrees.z = 4.0
	stall.add_child(canopy)
	# Laatikot pöydän vieressä
	var crate := MeshInstance3D.new()
	var crb := BoxMesh.new()
	crb.size = Vector3(0.7, 0.7, 0.7)
	crate.mesh = crb
	crate.material_override = wood
	crate.position = Vector3(2.2, 0.35, 0.2)
	stall.add_child(crate)
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(3.4, 1.0, 1.2)
	col.shape = shape
	col.position.y = 0.5
	stall.add_child(col)
	var lbl := Label3D.new()
	lbl.text = str(spec["name"])
	lbl.font_size = 72
	lbl.pixel_size = 0.008
	lbl.modulate = UITheme.TEXT
	lbl.outline_size = 20
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.position.y = 3.1
	stall.add_child(lbl)
	add_child(stall)


func _add_caravan(pos: Vector3) -> void:
	var wagon := StaticBody3D.new()
	wagon.position = pos
	wagon.rotation_degrees.y = 25.0
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.30, 0.20, 0.12)
	var body := MeshInstance3D.new()
	var bb := BoxMesh.new()
	bb.size = Vector3(3.6, 1.1, 1.8)
	body.mesh = bb
	body.material_override = wood
	body.position.y = 1.0
	wagon.add_child(body)
	# Kaareva kuomu (kapseli kyljellään)
	var canopy := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 1.0
	cm.height = 3.8
	canopy.mesh = cm
	var cmat := StandardMaterial3D.new()
	cmat.albedo_color = Color(0.55, 0.48, 0.36)
	canopy.material_override = cmat
	canopy.rotation_degrees.z = 90.0
	canopy.position.y = 2.0
	wagon.add_child(canopy)
	var wheel_mat := StandardMaterial3D.new()
	wheel_mat.albedo_color = Color(0.14, 0.10, 0.06)
	for dx in [-1.3, 1.3]:
		for dz in [-1.0, 1.0]:
			var wheel := MeshInstance3D.new()
			var wc := CylinderMesh.new()
			wc.top_radius = 0.55
			wc.bottom_radius = 0.55
			wc.height = 0.14
			wheel.mesh = wc
			wheel.material_override = wheel_mat
			wheel.rotation_degrees.x = 90.0
			wheel.position = Vector3(dx, 0.55, dz)
			wagon.add_child(wheel)
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(3.6, 2.4, 1.8)
	col.shape = shape
	col.position.y = 1.2
	wagon.add_child(col)
	var lbl := Label3D.new()
	lbl.text = "Griznak's Caravan"
	lbl.font_size = 84
	lbl.pixel_size = 0.008
	lbl.modulate = UITheme.GOLD
	lbl.outline_size = 20
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.position.y = 3.6
	wagon.add_child(lbl)
	add_child(wagon)


# ---------- Suo ----------
func _build_swamp() -> void:
	_add_pond(Vector3(-16, 0, 22), Vector2(22, 12))
	_add_pond(Vector3(20, 0, 24), Vector2(14, 9))
	_add_pond(Vector3(-34, 0, -18), Vector2(12, 10))
	# Laudoitettu kulkutie torilta tavernan laiturille
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.28, 0.20, 0.13)
	for i in range(7):
		var plank := MeshInstance3D.new()
		var pb := BoxMesh.new()
		pb.size = Vector3(1.6, 0.1, 0.9)
		plank.mesh = pb
		plank.material_override = wood
		plank.position = Vector3(-13.0, 0.08, 14.0 + i * 1.0)
		add_child(plank)


func _add_pond(pos: Vector3, size: Vector2) -> void:
	var water := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = size
	water.mesh = pm
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = Color(0.10, 0.17, 0.13, 0.88)
	wmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	wmat.roughness = 0.08
	wmat.metallic = 0.35
	water.material_override = wmat
	water.position = pos + Vector3(0, 0.04, 0)
	add_child(water)

	var rng := RandomNumberGenerator.new()
	rng.seed = int(pos.x * 13.0 + pos.z * 7.0)
	# Kaislat rannoille
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.30, 0.38, 0.18)
	for i in range(18):
		var a := rng.randf_range(0.0, TAU)
		var reed := MeshInstance3D.new()
		var rc := CylinderMesh.new()
		rc.top_radius = 0.02
		rc.bottom_radius = 0.04
		rc.height = rng.randf_range(0.9, 1.5)
		reed.mesh = rc
		reed.material_override = rmat
		reed.position = pos + Vector3(cos(a) * size.x * 0.48,
			rc.height / 2.0, sin(a) * size.y * 0.48)
		add_child(reed)
	# Lumpeenlehdet
	var lmat := StandardMaterial3D.new()
	lmat.albedo_color = Color(0.20, 0.40, 0.20)
	for i in range(6):
		var pad := MeshInstance3D.new()
		var pc := CylinderMesh.new()
		pc.top_radius = rng.randf_range(0.25, 0.5)
		pc.bottom_radius = pc.top_radius
		pc.height = 0.02
		pad.mesh = pc
		pad.material_override = lmat
		pad.position = pos + Vector3(rng.randf_range(-size.x * 0.35, size.x * 0.35),
			0.06, rng.randf_range(-size.y * 0.35, size.y * 0.35))
		add_child(pad)
	# Tulikärpäset veden yllä
	var flies := CPUParticles3D.new()
	flies.amount = 16
	flies.lifetime = 5.0
	flies.preprocess = 5.0
	flies.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	flies.emission_box_extents = Vector3(size.x * 0.4, 0.6, size.y * 0.4)
	flies.gravity = Vector3.ZERO
	flies.initial_velocity_min = 0.2
	flies.initial_velocity_max = 0.6
	var fly_mesh := SphereMesh.new()
	fly_mesh.radius = 0.035
	fly_mesh.height = 0.07
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.8, 1.0, 0.4)
	fmat.emission_enabled = true
	fmat.emission = Color(0.7, 1.0, 0.3)
	fmat.emission_energy_multiplier = 2.2
	fly_mesh.material = fmat
	flies.mesh = fly_mesh
	flies.position = pos + Vector3(0, 1.0, 0)
	add_child(flies)


# ---------- Yksityiskohdat ----------
func _build_details() -> void:
	# Lyhdyt torin kulmiin ja tien varteen
	for lpos in [Vector3(-16, 0, -6), Vector3(16, 0, -6),
			Vector3(-16, 0, 8), Vector3(16, 0, 10),
			Vector3(-26, 0, 3), Vector3(6, 0, 14)]:
		_add_lantern(lpos)
	# Tavernan laituri lammelle
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.26, 0.19, 0.12)
	var dock := MeshInstance3D.new()
	var db := BoxMesh.new()
	db.size = Vector3(2.0, 0.25, 6.0)
	dock.mesh = db
	dock.material_override = wood
	dock.position = Vector3(-13, 0.15, 19.5)
	add_child(dock)
	# Tynnyreitä ja laatikoita tavernan edustalle
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for i in range(4):
		var barrel := MeshInstance3D.new()
		var bc := CylinderMesh.new()
		bc.top_radius = 0.4
		bc.bottom_radius = 0.45
		bc.height = 0.9
		barrel.mesh = bc
		barrel.material_override = wood
		barrel.position = Vector3(-9.5 + rng.randf_range(-0.6, 0.6),
			0.45, 9.0 + i * 1.1)
		add_child(barrel)
	# Reunametsä
	for i in range(26):
		var a := TAU * i / 26.0
		var r := 46.0 + rng.randf_range(-4.0, 6.0)
		_add_tree(Vector3(cos(a) * r, 0, sin(a) * r * 0.8),
			rng.randf_range(0.9, 1.5), rng)


func _add_lantern(pos: Vector3) -> void:
	var pole := MeshInstance3D.new()
	var pc := CylinderMesh.new()
	pc.top_radius = 0.05
	pc.bottom_radius = 0.07
	pc.height = 2.6
	pole.mesh = pc
	var pmat := StandardMaterial3D.new()
	pmat.albedo_color = Color(0.15, 0.12, 0.09)
	pole.material_override = pmat
	pole.position = pos + Vector3(0, 1.3, 0)
	add_child(pole)
	var lamp := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.16
	sm.height = 0.32
	lamp.mesh = sm
	var lmat := StandardMaterial3D.new()
	lmat.albedo_color = Color(1.0, 0.8, 0.4)
	lmat.emission_enabled = true
	lmat.emission = Color(1.0, 0.7, 0.3)
	lmat.emission_energy_multiplier = 2.0
	lamp.material_override = lmat
	lamp.position = pos + Vector3(0, 2.5, 0)
	add_child(lamp)
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.75, 0.4)
	light.omni_range = 6.0
	light.light_energy = 0.9
	light.position = pos + Vector3(0, 2.5, 0)
	add_child(light)


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
	tmat.albedo_color = Color(0.13, 0.10, 0.07)
	trunk.material_override = tmat
	trunk.position.y = 1.2
	tree.add_child(trunk)
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.10, 0.16, 0.09)
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


# ---------- Väki ----------
func _spawn_villagers() -> void:
	var tints := [Color(0.45, 0.38, 0.28), Color(0.38, 0.42, 0.30),
		Color(0.50, 0.32, 0.28), Color(0.35, 0.35, 0.42),
		Color(0.42, 0.30, 0.36)]
	var spots := [Vector3(-4, 1, -4), Vector3(6, 1, 3), Vector3(-8, 1, 6),
		Vector3(2, 1, -7), Vector3(-20, 1, -8)]
	for i in range(spots.size()):
		var v := CharacterBody3D.new()
		v.set_script(load("res://scripts/villager.gd"))
		v.set("tint", tints[i])
		v.position = spots[i]
		add_child(v)


func _spawn_player() -> void:
	player = CharacterBody3D.new()
	player.set_script(load("res://scripts/player.gd"))
	# Saapuminen: herää tavernan edustalta (intro) - muuten läntinen tie
	player.position = Vector3(-11, 1, 8)
	add_child(player)
	# Introsta saapuminen: ei miekkaa eikä loitsuja
	if not SaveGame.transfer_state.is_empty():
		player.apply_state(SaveGame.transfer_state)
		SaveGame.transfer_state = {}
	else:
		var state := SaveGame.consume_pending()
		if not state.is_empty():
			player.apply_state(state)


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

	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.theme = UITheme.build()
	panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	panel.position = Vector2(24, -70)
	panel.add_child(UITheme.hint(
		"You wake outside the Sunk Cask. Your memory — and your blade — are gone.      M / Touchpad — Commander & Map"))
	layer.add_child(panel)


func _show_title() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var title := UITheme.title("MUCKFORD", 90)
	title.set_anchors_preset(Control.PRESET_CENTER_TOP)
	title.grow_horizontal = Control.GROW_DIRECTION_BOTH
	title.position.y = 140
	title.modulate.a = 0.0
	layer.add_child(title)
	var sub := UITheme.hint("Tier 0 — the swamp gate of Varracor")
	sub.set_anchors_preset(Control.PRESET_CENTER_TOP)
	sub.grow_horizontal = Control.GROW_DIRECTION_BOTH
	sub.position.y = 240
	sub.modulate.a = 0.0
	layer.add_child(sub)
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(title, "modulate:a", 1.0, 1.5)
	tw.tween_property(sub, "modulate:a", 1.0, 1.5)
	tw.chain().tween_interval(3.0)
	tw.chain().tween_property(title, "modulate:a", 0.0, 1.5)
	tw.parallel().tween_property(sub, "modulate:a", 0.0, 1.5)
