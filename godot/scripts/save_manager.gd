extends Node
## SaveGame (autoload): yksinkertainen versioitu tallennus user://save.json.
## Sama idea kuin optioissa (ConfigFile) mutta pelitila JSONina - korjaa
## py-version ad-hoc-tallennuksen (lapsentauti #9: versioitu formaatti).
##
## Käyttö: pause-valikon SAVE GAME kutsuu save_state(commander.state_dict()),
## päävalikon CONTINUE asettaa pending_load=true -> areena lukee sen.

const PATH := "user://save.json"
const VERSION := 1

## Päävalikko asettaa tämän; areena kuluttaa sen spawnissa
var pending_load := false

## Skenenvaihdon kevyt tilansiirto (esim. intro -> Muckford: ei miekkaa,
## ei loitsuja). Vastaanottava skene kuluttaa ja tyhjentää.
var transfer_state: Dictionary = {}


func has_save() -> bool:
	return FileAccess.file_exists(PATH)


func save_state(state: Dictionary) -> bool:
	var payload := {
		"version": VERSION,
		"saved_at": Time.get_datetime_string_from_system(),
		"player": state,
	}
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f == null:
		push_warning("SaveGame: ei voitu avata " + PATH)
		return false
	f.store_string(JSON.stringify(payload, "  "))
	return true


func load_state() -> Dictionary:
	if not has_save():
		return {}
	var f := FileAccess.open(PATH, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	if not (parsed is Dictionary):
		push_warning("SaveGame: rikkinäinen tallennus")
		return {}
	if int(parsed.get("version", 0)) != VERSION:
		# Tulevaisuudessa: migraatio versiosta toiseen
		push_warning("SaveGame: tuntematon versio, yritetään silti")
	return parsed.get("player", {})
