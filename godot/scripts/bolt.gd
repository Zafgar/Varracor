extends Area3D
## Hehkuva loitsuprojektiiili: pallo + valo, lentää suoraan, osuu
## "enemies"-ryhmään ja purskahtaa partikkeleiksi. Väri = vahinkotyyppi.

var damage := 10
var direction := Vector3.FORWARD
var tint := Color(0.55, 0.5, 1.0)
# Mihin ryhmään projektiiili osuu: pelaajan boltit "enemies",
# vihollisten (esim. Devourer) boltit "player"
var hits_group := "enemies"

const SPEED := 26.0
const LIFETIME := 1.6

# Lyhytikäiset boltit (esim. Vortex Slashin viuhka) asettavat tämän
var lifetime_override := 0.0

var _age := 0.0


func _ready() -> void:
	var mesh := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.22
	sm.height = 0.44
	mesh.mesh = sm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = tint
	mat.emission_enabled = true
	mat.emission = tint
	mat.emission_energy_multiplier = 3.0
	mesh.material_override = mat
	add_child(mesh)

	var light := OmniLight3D.new()
	light.light_color = tint
	light.omni_range = 4.0
	light.light_energy = 1.4
	add_child(light)

	var col := CollisionShape3D.new()
	var shape := SphereShape3D.new()
	shape.radius = 0.3
	col.shape = shape
	add_child(col)

	body_entered.connect(_on_hit)


func _physics_process(delta: float) -> void:
	position += direction * SPEED * delta
	_age += delta
	var life := lifetime_override if lifetime_override > 0.0 else LIFETIME
	if _age >= life:
		queue_free()


func _on_hit(body: Node3D) -> void:
	if body.is_in_group(hits_group) and body.has_method("take_damage"):
		body.take_damage(float(damage))
		_burst()
		return
	if body is StaticBody3D:
		_burst()   # seinä/este pysäyttää; muut hahmot läpäistään


func _burst() -> void:
	# Osumapurske: partikkelit jäävät maailmaan kun bolt vapautuu
	var p := CPUParticles3D.new()
	p.position = global_position
	p.emitting = true
	p.one_shot = true
	p.amount = 24
	p.lifetime = 0.4
	p.explosiveness = 1.0
	p.initial_velocity_min = 4.0
	p.initial_velocity_max = 9.0
	p.spread = 180.0
	p.color = tint
	p.mesh = SphereMesh.new()
	(p.mesh as SphereMesh).radius = 0.05
	(p.mesh as SphereMesh).height = 0.1
	get_parent().add_child(p)
	var timer := get_tree().create_timer(0.6)
	timer.timeout.connect(p.queue_free)
	Audio.sfx("hit")
	queue_free()
