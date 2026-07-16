extends PanelContainer
## Jaettu slottipaneeli: LOAD-tila (päävalikko) ja SAVE-tila (pause).
## Rivit: SLOT N + aikaleima/skene/taso, X-poisto kahdella klikillä
## (ensimmäinen varmistaa, toinen poistaa) kuten py-versiossa.
## Signaalit: slot_picked(slot) valinnasta, closed paluusta.

signal slot_picked(slot: int)
signal closed

var mode := "load"   # "load" | "save"

var _rows: VBoxContainer
var _armed_delete := 0   # slotti jonka X on viritetty (0 = ei mikään)


func _ready() -> void:
	theme = UITheme.build()
	custom_minimum_size = Vector2(640, 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	add_child(v)
	v.add_child(UITheme.title("LOAD GAME" if mode == "load" else "SAVE GAME", 36))
	_rows = VBoxContainer.new()
	_rows.add_theme_constant_override("separation", 8)
	v.add_child(_rows)
	var back := Button.new()
	back.text = "BACK"
	back.pressed.connect(func():
		Audio.sfx("back")
		closed.emit())
	v.add_child(back)
	v.add_child(UITheme.hint("X poistaa: paina kahdesti varmistukseksi"))
	refresh()


func refresh() -> void:
	_armed_delete = 0
	for c in _rows.get_children():
		c.queue_free()
	for i in range(1, SaveGame.SLOTS + 1):
		_rows.add_child(_make_row(i))
	# Fokus ensimmäiseen käytettävään nappiin
	await get_tree().process_frame
	for c in _rows.get_children():
		var b := c.get_child(0) as Button
		if not b.disabled:
			b.grab_focus()
			return


func _make_row(slot: int) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var info := SaveGame.slot_info(slot)
	var main := Button.new()
	main.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if info.is_empty():
		main.text = "SLOT %d — empty" % slot
		main.disabled = mode == "load"
	else:
		main.text = "SLOT %d — %s · Lv %d · %s" % [
			slot, info["scene"], info["level"], info["saved_at"]]
	main.pressed.connect(func():
		Audio.sfx("confirm")
		slot_picked.emit(slot))
	row.add_child(main)

	var del := Button.new()
	del.text = "X"
	del.disabled = info.is_empty()
	del.pressed.connect(func(): _on_delete(slot, del))
	row.add_child(del)
	return row


func _on_delete(slot: int, btn: Button) -> void:
	if _armed_delete == slot:
		SaveGame.delete_slot(slot)
		Audio.sfx("back")
		refresh()
	else:
		_armed_delete = slot
		btn.text = "X?"
		Audio.sfx("click")
