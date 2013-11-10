tokenize = (code) ->
	tokens = []
	for token in code.split(/\s+/)
		if token.match /(^-?[0-9]+\.[0-9]*)$/ or token.match /^(-?\.[0-9]+)$/
			tokens.push parseFloat(token)
		else if token.match /(-?[0-9]+)/
			tokens.push parseInt(token)
		else
			tokens.push token
	tokens

strip_comments = (tokens) ->
	ret = []
	depth = 0
	for token in tokens
		if token == '('
			depth += 1
		else if token == ')' and depth > 0
			depth -= 1
		else if depth == 0
			ret.push token
	ret

parse_words = (tokens) ->
	words = {main: []}
	macros = {}

	current = () ->
		[name, macro] = stack[stack.length - 1]
		if macro
			macros[name] = [] if macros[name] == undefined
			macros[name]
		else
			words[name] = [] if words[name] == undefined
			words[name]

	stack = [['main', false]]
	start = undefined

	for token in tokens
		if token == ':'
			start = false
		else if token == ':m'
			start = true
		else if token == ';'
			stack.pop()
		else if start != undefined
			stack.push [token, start]
			start = undefined
		else
			current().push token

	[words, macros]

compile = (code) ->
	tokens = tokenize code
	tokens = strip_comments tokens

	[words, macros] = parse_words tokens
	console.log words
	console.log macros
