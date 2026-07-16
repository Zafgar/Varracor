extends Node
## Catalogs (autoload): lataa pelidatan res://data/*.json -tiedostoista.
## Data exportataan PY-versiosta (python tools/export_gamedata.py) -
## PY on totuuslähde, tämä on peili. ÄLÄ käsin muokkaa data/-JSONeja.

var stat_curve: Dictionary = {}
var spells: Dictionary = {}
var gear: Dictionary = {}
var skill_tree: Dictionary = {}
var shapeshift: Dictionary = {}
var training: Dictionary = {}


func _ready() -> void:
	stat_curve = _load_json("res://data/stat_curve.json")
	spells = _load_json("res://data/spells.json")
	gear = _load_json("res://data/gear.json")
	skill_tree = _load_json("res://data/skill_tree.json")
	shapeshift = _load_json("res://data/shapeshift.json")
	training = _load_json("res://data/training.json")
	print("[Catalogs] spells=%d gear=%d skill_nodes=%d forms=%d" % [
		(spells.get("catalog", []) as Array).size(),
		(gear.get("items", []) as Array).size(),
		(skill_tree.get("nodes", {}) as Dictionary).size(),
		(shapeshift.get("forms", {}) as Dictionary).size(),
	])


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_warning("Catalogs: missing " + path)
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if parsed is Dictionary else {}


## Statikäyrä: sama kaava kuin progression/stat_curve.py (parametrit JSONista)
func stat_target(level: int) -> int:
	var base: float = stat_curve.get("base", 8.0)
	var coef: float = stat_curve.get("coef", 0.15)
	var power: float = stat_curve.get("power", 2.7)
	var lvl: int = max(1, level)
	return max(5, int(base + coef * pow(float(lvl), power)))


## Loitsun teho: base(tier) + INT * coef(tier), arkkityyppikertoimella
## (sama kuin spells/spell_scaling.py)
func scaled_damage(tier: int, intelligence: int, archetype: String = "nuke") -> int:
	var tb: Dictionary = spells.get("tier_base", {})
	var tc: Dictionary = spells.get("tier_int_coef", {})
	var am: Dictionary = spells.get("archetype_mult", {})
	var mult: float = am.get(archetype, 1.0)
	var base: float = float(tb.get(str(tier), 0)) * mult
	var coef: float = float(tc.get(str(tier), 0)) * mult
	return max(0, int(base + float(intelligence) * coef))


func spell_spec(spell_id: String) -> Dictionary:
	for s in spells.get("catalog", []):
		if s.get("id", "") == spell_id:
			return s
	return {}


func gear_item(gear_id: String) -> Dictionary:
	for g in gear.get("items", []):
		if g.get("id", "") == gear_id:
			return g
	return {}
