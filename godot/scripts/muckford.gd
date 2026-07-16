extends Node3D
## Muckford - Tier 0 -suokaupungin aamu. Commander herää The Sunk Caskin
## edustalla ilman muistia, miekkaa ja loitsuja (intro vei ne).
## Koodirakennettu kylä: lämmin aamuvalo, kevyt usva, talot harjakattoineen,
## hehkuvat ikkunat, taverna kylttineen ja portti harjoitusareenalle.

const SQUARE_R := 26.0

var player: CharacterBody3D
var _title: Label


func _ready() -> void:
	_build_environment()
	_build_ground()
	_build_town()
	_spawn_player()
	_build_camera()
	_build_hud()
	add_child(load("res://scripts/pause_menu.gd").new())
	Audio.play_music("town")
	_show_title()


func _build_environment() -> void:
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38.0, 55.0, 0.0)
	sun.light_color = Color(1.0, 0.9, 0.72)
	sun.light_energy = 1.15
	sun.shadow_enabled = true
	add_child(sun)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.55, 0.66, 0.80)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.55, 0.55, 0.52)
	e.glow_enabled = true
	e.fog_enabled = true
	e.fog_light_color = Color(0.7, 0.75, 0.8)
	e.fog_density = 0.004
	env.environment = e
	add_child(env)


func _build_ground() -> void:
	var ground := StaticBody3D.new()
	var gm := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(120, 120)
	gm.mesh = plane
	var gmat := StandardMaterial3D.new()
	gmat.albedo_color = Color(0.20, 0.26, 0.15)
	gmat.roughness = 0.95
	gm.material_override = gmat
	ground.add_child(gm)
	var col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(120, 0.1, 120)
	col.shape = box
	col.position.y = -0.05
	ground.add_child(col)
	add_child(ground)

	# Torin savipohja
	var square := MeshInstance3D.new()
	var sp := PlaneMesh.new()
	sp.size = Vector2(SQUARE_R * 1.6, SQUARE_R * 1.4)
	square.mesh = sp
	var smat := StandardMaterial3D.new()
	smat.albedo_color = Color(0.32, 0.27, 0.20)
	square.material_override = smat
	square.position.y = 0.02
	add_child(square)


func _build_town() -> void:
	# Taverna (The Sunk Cask): iso talo etelälaidalla
	_add_house(Vector3(0, 0, 14), Vector3(9, 4, 7),
		Color(0.30, 0.22, 0.14), true, "The Sunk Cask")
	# Kylän talot torin ympärille
	_add_house(Vector3(-16, 0, 4), Vector3(6, 3, 5), Color(0.26, 0.20, 0.14), false, "")
	_add_house(Vector3(-15, 0, -8), Vector3(5, 3, 5), Color(0.24, 0.19, 0.15), false, "")
	_add_house(Vector3(15, 0, -6), Vector3(6, 3.5, 5), Color(0.28, 0.21, 0.13), false, "Smithy")
	_add_house(Vector3(16, 0, 6), Vector3(5, 3, 4), Color(0.25, 0.20, 0.16), false, "")
	_add_house(Vector3(-3, 0, -16), Vector3(7, 3.5, 5), Color(0.27, 0.22, 0.15), false, "Barracks")

	# Kaivo torin keskellä
	var well := MeshInstance3D.new()
	var wm := CylinderMesh.new()
	wm.top_radius = 1.1
	wm.bottom_radius = 1.2
	wm.height = 1.0
	well.mesh = wm
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = Color(0.35, 0.35, 0.38)
	well.material_override = wmat
	well.position = Vector3(0, 0.5, -2)
	add_child(well)

	# Portti harjoitusareenalle (prototyyppi): itälaidalla
	var gate_lbl := Label3D.new()
	gate_lbl.text = "TRAINING ARENA >"
	gate_lbl.font_size = 120
	gate_lbl.modulate = UITheme.GOLD
	gate_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	gate_lbl.position = Vector3(26, 3.0, 0)
	add_child(gate_lbl)
	var gate := Area3D.new()
	gate.position = Vector3(28, 1, 0)
	var gcol := CollisionShape3D.new()
	var gbox := BoxShape3D.new()
	gbox.size = Vector3(3, 4, 10)
	gcol.shape = gbox
	gate.add_child(gcol)
	gate.body_entered.connect(func(body: Node3D):
		if body.is_in_group("player"):
			Router.goto("res://scenes/main.tscn"))
	add_child(gate)


func _add_house(pos: Vector3, size: Vector3, color: Color,
		tavern: bool, sign_text: String) -> void:
	var house := StaticBody3D.new()
	house.position = pos
	# Seinät
	var walls := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	walls.mesh = bm
	var wmat := StandardMaterial3D.new()
	wmat.albedo_color = color
	wmat.roughness = 0.9
	walls.material_override = wmat
	walls.position.y = size.y / 2.0
	house.add_child(walls)
	# Harjakatto
	var roof := MeshInstance3D.new()
	var pm := PrismMesh.new()
	pm.size = Vector3(size.x + 0.8, size.y * 0.6, size.z + 0.8)
	roof.mesh = pm
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.20, 0.10, 0.08)
	roof.material_override = rmat
	roof.position.y = size.y + size.y * 0.3
	house.add_child(roof)
	# Ovi
	var door := MeshInstance3D.new()
	var dm := BoxMesh.new()
	dm.size = Vector3(1.0, 1.9, 0.15)
	door.mesh = dm
	var dmat := StandardMaterial3D.new()
	dmat.albedo_color = Color(0.12, 0.08, 0.05)
	door.material_override = dmat
	door.position = Vector3(0, 0.95, -size.z / 2.0 - 0.05)
	house.add_child(door)
	# Lämpimästi hehkuvat ikkunat
	var wgmat := StandardMaterial3D.new()
	wgmat.albedo_color = Color(1.0, 0.75, 0.35)
	wgmat.emission_enabled = true
	wgmat.emission = Color(1.0, 0.7, 0.3)
	wgmat.emission_energy_multiplier = 1.6
	for dx in [-size.x * 0.28, size.x * 0.28]:
		var win := MeshInstance3D.new()
		var wb := BoxMesh.new()
		wb.size = Vector3(0.8, 0.8, 0.1)
		win.mesh = wb
		win.material_override = wgmat
		win.position = Vector3(dx, size.y * 0.55, -size.z / 2.0 - 0.05)
		house.add_child(win)
	# Törmäys
	var col := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	col.shape = shape
	col.position.y = size.y / 2.0
	house.add_child(col)
	# Kyltti
	if sign_text != "":
		var lbl := Label3D.new()
		lbl.text = sign_text
		lbl.font_size = 96
		lbl.modulate = UITheme.GOLD if tavern else UITheme.TEXT
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.position = Vector3(0, size.y + size.y * 0.75, 0)
		house.add_child(lbl)
	add_child(house)


func _spawn_player() -> void:
	player = CharacterBody3D.new()
	player.set_script(load("res://scripts/player.gd"))
	player.position = Vector3(0, 1, 9)   # tavernan edusta
	add_child(player)
	# Introsta saapuminen: ei miekkaa eikä loitsuja
	if not SaveGame.transfer_state.is_empty():
		player.apply_state(SaveGame.transfer_state)
		SaveGame.transfer_state = {}
	elif SaveGame.pending_load:
		SaveGame.pending_load = false
		var state := SaveGame.load_state()
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
		"You wake outside the Sunk Cask. Your memory — and your blade — are gone."))
	layer.add_child(panel)


func _show_title() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_title = UITheme.title("MUCKFORD", 90)
	_title.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_title.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_title.position.y = 140
	_title.modulate.a = 0.0
	layer.add_child(_title)
	var sub := UITheme.hint("Tier 0 — the swamp gate of Varracor")
	sub.set_anchors_preset(Control.PRESET_CENTER_TOP)
	sub.grow_horizontal = Control.GROW_DIRECTION_BOTH
	sub.position.y = 240
	sub.modulate.a = 0.0
	layer.add_child(sub)
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(_title, "modulate:a", 1.0, 1.5)
	tw.tween_property(sub, "modulate:a", 1.0, 1.5)
	tw.chain().tween_interval(3.0)
	tw.chain().tween_property(_title, "modulate:a", 0.0, 1.5)
	tw.parallel().tween_property(sub, "modulate:a", 0.0, 1.5)
