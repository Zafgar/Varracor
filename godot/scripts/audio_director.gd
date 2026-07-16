extends Node
## Audio (autoload): KAIKKI äänet ja musiikki syntetisoidaan koodilla -
## ei audiotiedostoja (sama placeholder-filosofia kuin grafiikoissa;
## oikeat äänet voidaan vaihtaa tilalle myöhemmin).
##
## - Väylät: Master / Music / SFX (optiot säätävät näitä)
## - SFX: valmiiksi syntetisoidut AudioStreamWAV:t (click/confirm/back/
##   whoosh/hit) - siniverhokäyrät ja kohinapurskeet
## - Musiikki: reaaliaikainen pad-syntetisaattori (AudioStreamGenerator):
##   sointukierto + hidas huojunta, eri tunnelma per näkymä

const SR := 22050.0

var _sfx: Dictionary = {}
var _music_player: AudioStreamPlayer
var _playback: AudioStreamGeneratorPlayback
var _phase := [0.0, 0.0, 0.0]
var _chord_t := 0.0
var _chord_i := 0
var _chords: Array = []
var _gain := 0.07

# Sointukierrot per tunnelma (MIDI-nuotit, moll-sävyt)
const MOODS := {
	"menu":  [[57, 60, 64], [55, 59, 62], [53, 57, 60], [55, 59, 62]],
	"intro": [[45, 48, 52], [43, 47, 50], [41, 45, 48], [40, 43, 47]],
	"arena": [[50, 53, 57], [48, 52, 55], [46, 50, 53], [48, 52, 55]],
}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS   # musiikki soi pausenkin läpi
	_make_buses()
	_sfx["click"] = _tone(880.0, 0.06, 26.0, 0.35)
	_sfx["confirm"] = _two_tone(660.0, 990.0, 0.12, 0.4)
	_sfx["back"] = _two_tone(660.0, 440.0, 0.12, 0.35)
	_sfx["whoosh"] = _noise_burst(0.18, 14.0, 0.5)
	_sfx["hit"] = _noise_burst(0.08, 30.0, 0.6)


func _make_buses() -> void:
	for bus_name in ["Music", "SFX"]:
		if AudioServer.get_bus_index(bus_name) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus_name)
			AudioServer.set_bus_send(i, "Master")


func sfx(name: String) -> void:
	var stream: AudioStreamWAV = _sfx.get(name)
	if stream == null:
		return
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.bus = "SFX"
	add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


func play_music(mood: String) -> void:
	_chords = MOODS.get(mood, MOODS["menu"])
	_chord_i = 0
	_chord_t = 0.0
	if _music_player == null:
		_music_player = AudioStreamPlayer.new()
		var gen := AudioStreamGenerator.new()
		gen.mix_rate = SR
		gen.buffer_length = 0.25
		_music_player.stream = gen
		_music_player.bus = "Music"
		add_child(_music_player)
		_music_player.play()
		_playback = _music_player.get_stream_playback()


func stop_music() -> void:
	if _music_player:
		_music_player.stop()
		_music_player.queue_free()
		_music_player = null
		_playback = null


func _process(delta: float) -> void:
	if _playback == null or _chords.is_empty():
		return
	_chord_t += delta
	if _chord_t >= 4.0:
		_chord_t = 0.0
		_chord_i = (_chord_i + 1) % _chords.size()
	var chord: Array = _chords[_chord_i]
	var frames: int = _playback.get_frames_available()
	for f in range(frames):
		var v := 0.0
		for i in range(3):
			var hz: float = 440.0 * pow(2.0, (float(chord[i]) - 69.0) / 12.0)
			_phase[i] += hz / SR
			# Pehmeä pad: perussini + hiljainen oktaavi
			v += sin(TAU * _phase[i]) * 0.5 \
				+ sin(TAU * _phase[i] * 2.0) * 0.12
		v *= _gain * (0.8 + 0.2 * sin(_chord_t * 1.7))   # hidas huojunta
		_playback.push_frame(Vector2(v, v))


# ---- SFX-syntetisointi (16-bit mono WAV) ----
func _wav(samples: PackedFloat32Array) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in range(samples.size()):
		var s := int(clamp(samples[i], -1.0, 1.0) * 32767.0)
		data.encode_s16(i * 2, s)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = int(SR)
	wav.stereo = false
	wav.data = data
	return wav


func _tone(freq: float, dur: float, decay: float, vol: float) -> AudioStreamWAV:
	var n := int(SR * dur)
	var out := PackedFloat32Array()
	out.resize(n)
	for i in range(n):
		var t := float(i) / SR
		out[i] = sin(TAU * freq * t) * exp(-decay * t) * vol
	return _wav(out)


func _two_tone(f1: float, f2: float, dur: float, vol: float) -> AudioStreamWAV:
	var n := int(SR * dur)
	var out := PackedFloat32Array()
	out.resize(n)
	for i in range(n):
		var t := float(i) / SR
		var f := f1 if t < dur * 0.5 else f2
		out[i] = sin(TAU * f * t) * exp(-10.0 * t) * vol
	return _wav(out)


func _noise_burst(dur: float, decay: float, vol: float) -> AudioStreamWAV:
	var n := int(SR * dur)
	var out := PackedFloat32Array()
	out.resize(n)
	var prev := 0.0
	for i in range(n):
		var t := float(i) / SR
		# Kevyt alipäästö kohinaan -> "whoosh" eikä sirinä
		prev = prev * 0.7 + (randf() * 2.0 - 1.0) * 0.3
		out[i] = prev * exp(-decay * t) * vol
	return _wav(out)
