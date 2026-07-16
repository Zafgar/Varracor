extends Node
## SaveGame (autoload): versioitu slottitallennus (3 slottia,
## user://save_slot_N.json) - sama idea kuin py-versiossa: päävalikon
## LOAD GAME avaa slottipaneelin (lataus + poisto kahdella klikillä),
## pause-valikon SAVE GAME valitsee slotin samasta paneelista.

const SLOTS := 3
const VERSION := 1

## Slottipaneeli asettaa nämä; kohdeskene kuluttaa spawnissa
var pending_load := false
var pending_slot := 1

## Skenenvaihdon kevyt tilansiirto (esim. intro -> Muckford: ei miekkaa,
## ei loitsuja). Vastaanottava skene kuluttaa ja tyhjentää.
var transfer_state: Dictionary = {}


func _ready() -> void:
	# Migraatio: vanha yksipaikkainen save.json -> slotti 1
	if FileAccess.file_exists("user://save.json") \
			and not slot_exists(1):
		DirAccess.rename_absolute("user://save.json", _slot_path(1))


func _slot_path(slot: int) -> String:
	return "user://save_slot_%d.json" % slot


func slot_exists(slot: int) -> bool:
	return FileAccess.file_exists(_slot_path(slot))


func has_any_save() -> bool:
	for i in range(1, SLOTS + 1):
		if slot_exists(i):
			return true
	return false


## Slottipaneelin riviteksti: milloin, missä ja millä tasolla
func slot_info(slot: int) -> Dictionary:
	if not slot_exists(slot):
		return {}
	var payload := _read(slot)
	var player: Dictionary = payload.get("player", {})
	var scene := str(player.get("scene", ""))
	return {
		"saved_at": str(payload.get("saved_at", "?")),
		"scene": scene.get_file().get_basename().capitalize(),
		"level": int(player.get("level", 1)),
	}


func save_slot(slot: int, state: Dictionary) -> bool:
	var payload := {
		"version": VERSION,
		"saved_at": Time.get_datetime_string_from_system(),
		"player": state,
	}
	var f := FileAccess.open(_slot_path(slot), FileAccess.WRITE)
	if f == null:
		push_warning("SaveGame: ei voitu avata " + _slot_path(slot))
		return false
	f.store_string(JSON.stringify(payload, "  "))
	return true


func load_slot(slot: int) -> Dictionary:
	var payload := _read(slot)
	if int(payload.get("version", 0)) != VERSION and not payload.is_empty():
		# Tulevaisuudessa: migraatio versiosta toiseen
		push_warning("SaveGame: tuntematon versio, yritetään silti")
	return payload.get("player", {})


func delete_slot(slot: int) -> void:
	if slot_exists(slot):
		DirAccess.remove_absolute(_slot_path(slot))


## Kohdeskenet kutsuvat tätä spawnissa: palauttaa ladattavan tilan
## (pending-slotti) ja kuittaa latauksen tehdyksi
func consume_pending() -> Dictionary:
	if not pending_load:
		return {}
	pending_load = false
	return load_slot(pending_slot)


func _read(slot: int) -> Dictionary:
	if not slot_exists(slot):
		return {}
	var f := FileAccess.open(_slot_path(slot), FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	if not (parsed is Dictionary):
		push_warning("SaveGame: rikkinäinen tallennus slotissa %d" % slot)
		return {}
	return parsed
