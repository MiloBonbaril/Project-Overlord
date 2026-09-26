extends Control

const TURN_COUNT := 8
const DEFAULT_SEED := 20260926
const ENGINE_PATH := "res://outils/joue-partie.py"

var seed_input: LineEdit
var status_label: Label
var heading: Label
var advice: RichTextLabel
var clause_input: LineEdit
var options_box: VBoxContainer
var resolve_button: Button
var report: RichTextLabel
var next_button: Button
var restart_button: Button
var game: Dictionary = {}
var catalogue: Dictionary = {}
var choices: Array[String] = []
var clauses_by_turn: Array[String] = []
var current_turn := 0
var selected_option_id := ""
var resolution_pending := false


func _ready() -> void:
	build_ui()
	load_catalogue()
	start_game()


func build_ui() -> void:
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 32)
	margin.add_theme_constant_override("margin_right", 32)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 24)
	add_child(margin)

	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 12)
	margin.add_child(page)

	var title := Label.new()
	title.text = "PROJECT OVERLORD — conseil du domaine"
	title.add_theme_font_size_override("font_size", 24)
	page.add_child(title)

	var launch := HBoxContainer.new()
	launch.add_theme_constant_override("separation", 8)
	page.add_child(launch)
	var seed_label := Label.new()
	seed_label.text = "Seed"
	launch.add_child(seed_label)
	seed_input = LineEdit.new()
	seed_input.text = str(DEFAULT_SEED)
	seed_input.custom_minimum_size.x = 180
	launch.add_child(seed_input)
	var launch_button := Button.new()
	launch_button.text = "Lancer"
	launch_button.pressed.connect(start_game)
	launch.add_child(launch_button)
	restart_button = Button.new()
	restart_button.text = "Rejouer la même seed"
	restart_button.pressed.connect(start_game)
	launch.add_child(restart_button)

	status_label = Label.new()
	status_label.modulate = Color("b7becb")
	page.add_child(status_label)
	heading = Label.new()
	heading.add_theme_font_size_override("font_size", 20)
	page.add_child(heading)
	advice = RichTextLabel.new()
	advice.bbcode_enabled = true
	advice.fit_content = true
	advice.custom_minimum_size.y = 110
	page.add_child(advice)

	var clause_row := HBoxContainer.new()
	page.add_child(clause_row)
	var clause_label := Label.new()
	clause_label.text = "Clauses (séparées par des virgules)  "
	clause_row.add_child(clause_label)
	clause_input = LineEdit.new()
	clause_input.placeholder_text = "aucune"
	clause_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	clause_input.text_changed.connect(_on_clauses_changed)
	clause_row.add_child(clause_input)

	options_box = VBoxContainer.new()
	options_box.add_theme_constant_override("separation", 6)
	page.add_child(options_box)
	resolve_button = Button.new()
	resolve_button.text = "Résoudre"
	resolve_button.disabled = true
	resolve_button.pressed.connect(resolve_selected_order)
	page.add_child(resolve_button)
	report = RichTextLabel.new()
	report.bbcode_enabled = true
	report.size_flags_vertical = Control.SIZE_EXPAND_FILL
	report.custom_minimum_size.y = 180
	page.add_child(report)
	next_button = Button.new()
	next_button.text = "Conseil suivant"
	next_button.pressed.connect(show_next_turn)
	next_button.visible = false
	page.add_child(next_button)


func load_catalogue() -> void:
	var directory := DirAccess.open("res://contenu/catalogue")
	if directory == null:
		return
	for filename in directory.get_files():
		if not filename.ends_with(".json") or filename == "exemple-canonique.json":
			continue
		var file := FileAccess.open("res://contenu/catalogue/" + filename, FileAccess.READ)
		var parsed = JSON.parse_string(file.get_as_text())
		if parsed is Dictionary:
			catalogue[parsed.get("id", filename)] = parsed


func start_game() -> void:
	var parsed_seed := seed_input.text.strip_edges().to_int()
	seed_input.text = str(parsed_seed)
	choices.clear()
	clauses_by_turn.clear()
	current_turn = 0
	selected_option_id = ""
	resolution_pending = false
	report.text = ""
	var result := run_engine(parsed_seed)
	if result.is_empty():
		return
	game = result
	status_label.text = "Seed %d · %d tours · vivier : %s" % [parsed_seed, game.get("tours", 0), joined(game.get("figures_du_vivier", []))]
	show_turn()


func run_engine(seed_value: int) -> Dictionary:
	var args := PackedStringArray([ProjectSettings.globalize_path(ENGINE_PATH), "--seed", str(seed_value), "--tours", str(TURN_COUNT), "--json"])
	for choice in choices:
		args.append_array(["--choix", choice])
	for turn_clauses in clauses_by_turn:
		args.append_array(["--clause-tour", turn_clauses])
	var output: Array = []
	var exit_code := OS.execute("python3", args, output, true)
	if exit_code != 0 or output.is_empty():
		show_error("Le moteur Python n’a pas pu démarrer (code %d). Python 3.10+ est requis." % exit_code)
		return {}
	var parsed = JSON.parse_string(str(output[0]))
	if not parsed is Dictionary:
		show_error("Le moteur a produit un journal illisible.")
		return {}
	return parsed


func show_turn() -> void:
	clear_options()
	selected_option_id = ""
	resolution_pending = false
	clause_input.editable = true
	clause_input.text = ""
	resolve_button.visible = true
	resolve_button.disabled = true
	next_button.visible = false
	var journal: Array = game.get("journal", [])
	if current_turn >= journal.size():
		show_end()
		return
	var entry: Dictionary = journal[current_turn]
	var situation: Dictionary = catalogue.get(entry.get("situation", ""), {})
	heading.text = "Tour %d/%d · %s" % [current_turn + 1, journal.size(), situation.get("nom", entry.get("situation", "Situation"))]
	advice.text = "[b]Conseil de %s[/b]\n%s\n\nChoisissez un ordre :" % [entry.get("serviteur", "?"), situation.get("description", "")]
	build_options(situation, entry)


func build_options(situation: Dictionary, entry: Dictionary) -> void:
	clear_options()
	var active_clauses := parse_clauses()
	for scored in entry.get("conseil", []):
		var option := find_option(situation, scored.get("id", ""))
		var option_id: String = scored.get("id", "")
		var forbidden_by := PackedStringArray()
		for clause in option.get("interdit_par", []):
			if active_clauses.has(str(clause)):
				forbidden_by.append(str(clause))
		var button := Button.new()
		var state_text := ""
		if not forbidden_by.is_empty():
			state_text = "\nINTERDITE PAR LA CLAUSE : %s" % joined(forbidden_by)
		elif option_id == selected_option_id:
			state_text = "\n✓ ORDRE SÉLECTIONNÉ"
		button.text = "%s — conseil %.2f\n%s%s" % [option.get("nom", option_id), scored.get("score", 0.0), option.get("prose", ""), state_text]
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.disabled = not forbidden_by.is_empty()
		button.pressed.connect(select_order.bind(option_id))
		options_box.add_child(button)


func select_order(option_id: String) -> void:
	if resolution_pending:
		return
	selected_option_id = option_id
	resolve_button.disabled = false
	var entry: Dictionary = game["journal"][current_turn]
	build_options(catalogue.get(entry.get("situation", ""), {}), entry)


func resolve_selected_order() -> void:
	if resolution_pending or selected_option_id.is_empty():
		return
	resolution_pending = true
	resolve_button.disabled = true
	choices.append(selected_option_id)
	clauses_by_turn.append(clause_input.text.strip_edges())
	var result := run_engine(seed_input.text.to_int())
	if result.is_empty():
		choices.pop_back()
		clauses_by_turn.pop_back()
		resolution_pending = false
		resolve_button.disabled = false
		return
	game = result
	var entry: Dictionary = game["journal"][current_turn]
	clear_options()
	clause_input.editable = false
	resolve_button.visible = false
	var facts: Array = entry.get("faits", [])
	var facts_text := "Faits non établis dans le rapport." if facts.is_empty() else joined(facts, "\n")
	report.text = "[b]Résolution : %s[/b]\n%s\n\n[b]Faits[/b]\n%s" % [entry.get("resolution_probable", ""), entry.get("rapport", ""), facts_text]
	next_button.text = "Terminer la partie" if current_turn + 1 >= game["journal"].size() else "Conseil suivant"
	next_button.visible = true


func show_next_turn() -> void:
	current_turn += 1
	report.text = ""
	show_turn()


func show_end() -> void:
	heading.text = "Partie terminée"
	advice.text = "Le domaine a traversé %d conseils. Vous pouvez rejouer exactement cette partie ou saisir une autre seed." % game.get("tours", 0)
	report.text = "[b]Journal final[/b]\nSeed %s · ordres : %s" % [seed_input.text, joined(choices)]
	clause_input.editable = false
	resolve_button.visible = false
	next_button.visible = false


func find_option(situation: Dictionary, option_id: String) -> Dictionary:
	for option in situation.get("options", []):
		if option.get("id", "") == option_id:
			return option
	return {}


func clear_options() -> void:
	for child in options_box.get_children():
		child.queue_free()


func parse_clauses() -> PackedStringArray:
	var clauses := PackedStringArray()
	for value in clause_input.text.split(","):
		var clause := value.strip_edges()
		if not clause.is_empty():
			clauses.append(clause)
	return clauses


func _on_clauses_changed(_text: String) -> void:
	if game.is_empty() or resolution_pending or current_turn >= game.get("journal", []).size():
		return
	selected_option_id = ""
	resolve_button.disabled = true
	var entry: Dictionary = game["journal"][current_turn]
	build_options(catalogue.get(entry.get("situation", ""), {}), entry)


func joined(values, separator := ", ") -> String:
	var strings := PackedStringArray()
	for value in values:
		strings.append(str(value))
	return separator.join(strings)


func show_error(message: String) -> void:
	status_label.text = message
	heading.text = "Impossible de lancer la partie"
	advice.text = "Vérifiez la commande indiquée dans le README."
