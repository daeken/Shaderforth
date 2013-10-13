import re

def regex(pattern, flags=0):
	def sub(text):
		match = pattern.match(text)
		if match == None:
			return False
		return match.groups()
	pattern = re.compile(pattern, flags)
	return sub

ffloat = regex(r'(-?[0-9]+\.[0-9]*)')
efloat = regex(r'(-?\.[0-9]+)')
bint = regex(r'(-?[0-9]+)')

satis = lambda inp, *funcs: any(func(inp) for func in funcs)

def parse(code):
	def sub(elem):
		if satis(elem, ffloat, efloat):
			return float(elem)
		elif bint(elem):
			return int(elem)
		else:
			return unicode(elem)

	code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
	code = map(sub, (elem for elem in code.replace('\n', ' ').replace('\t', ' ').split(' ') if elem != ''))

	return code

class Type(object):
	def __init__(self, name):
		self.name = name
		self.attributes = []

	def attribute(self, name):
		self.attributes.append(name)

	def __repr__(self):
		return ' '.join(self.attributes) + (' ' if self.attributes else '') + self.name

class Stack(object):
	def __init__(self):
		self.list = []

	def push(self, elem):
		self.list.append(elem)
		return self

	def pop(self):
		if len(self.list) == 0:
			self.list.append(Compiler.instance.argument())
		return self.list.pop()

	def top(self):
		if len(self.list) == 0:
			self.list.append(Compiler.instance.argument())
		return self.list[-1]

	def __len__(self):
		return len(self.list)

	def __repr__(self):
		return 'Stack(%r)' % self.list

class Code(object):
	def __init__(self, elems):
		self.elems = elems
		self.i = 0

	def peek(self):
		if self.i >= len(self.elems):
			return None
		return self.elems[self.i]

	def consume(self):
		if self.i >= len(self.elems):
			raise Exception('Out of range')
		self.i += 1
		return self.elems[self.i - 1]

	def insert(self, atoms):
		self.elems = self.elems[:self.i] + list(atoms) + self.elems[self.i:]
		return self

	def __repr__(self):
		return 'Code(parsed=%r, rest=%r)' % (self.elems[:self.i], self.elems[self.i:])

def word(symbol, consumes=0):
	def dec(fn):
		bwords[symbol] = consumes, fn
		return fn
	return dec

bwords = {
	'+' : (2, None), 
	'-' : (2, None), 
	'*' : (2, None), 
	'/' : (2, None), 
	'<' : (2, None), 
	'>' : (2, None), 
	'<=' : (2, None), 
	'>=' : (2, None), 
	'==' : (2, None), 
}
glfuncs = dict(
	dot=2, 
	vec4=4, 
	sin=1, 
	abs=1, 
	atan=1, 
	cos=1, 
	pow=2, 
	sqrt=1, 
	mod=2, 
	tan=1, 
	min=2, 
	length=1, 
)
gltypes = dict(
	dot='float', 
	vec4='vec4',
	length='float'
)
for name, consumes in glfuncs.items():
	bwords[name] = (consumes, None)
class Compiler(object):
	def __init__(self, code, shadertoy=False):
		self.tempi = 0
		self.shadertoy = shadertoy
		Compiler.instance = self
		self.globals = dict(
			gl_FragCoord=Type('vec4'), 
			gl_FragColor=Type('vec4'), 
		)
		self.words, self.wordtypes, self.macros = self.parsewords(code)

		for name, atoms in self.words.items():
			self.words[name] = self.compile(name, atoms)

		self.output()

	def output(self):
		def rename(name):
			return name.replace('-', '_')

		for name, type in self.globals.items():
			if name.startswith('gl_') or (self.shadertoy and 'uniform' in type.attributes):
				continue

			print type, rename(name) + ';'

		defd = []

		def structure(atom):
			if not isinstance(atom, tuple):
				return unicode(atom)

			if atom[0] in '+ - / * < > <= >= =='.split(' '):
				if len(atom) == 2:
					return '%s (%s)' % (atom[0], structure(atom[1]))
				else:
					return '(%s) %s (%s)' % (structure(atom[1]), atom[0], structure(atom[2]))
			elif atom[0] == '=':
				return '%s = %s' % (structure(atom[1]), structure(atom[2]))
			elif atom[0][0] == '.':
				return '(%s)%s' % (structure(atom[1]), atom[0])
			elif atom[0] == 'var':
				if atom[1].startswith('gl_') or atom[1] in self.globals or atom[1] in defd:
					return rename(atom[1])
				else:
					defd.append(atom[1])
					return '%r %s' % (locals[atom[1]], rename(atom[1]))
			elif atom[0] == 'arg':
				return atom[1]
			elif atom[0] == 'return':
				return 'return %s' % structure(atom[1])
			elif atom[0] == 'for':
				_, name, start, top = atom
				defd.append(name)
				return 'for(int %s = %s; %s < %s; ++%s) {' % (name, structure(start), name, structure(top), name), True
			elif atom[0] == 'if':
				return 'if(%s) {' % structure(atom[1]), True
			elif atom[0] == 'else':
				return '} else {', True
			elif atom[0] == 'endblock':
				return '}', True
			elif atom[0] == 'break':
				return 'break'
			elif atom[0] == 'continue':
				return 'continue'
			else:
				return '%s(%s)' % (rename(atom[0]), ', '.join(map(structure, atom[1:])))

		for name in self.words:
			if name != 'main':
				print '%s %s(%s);' % (self.wordtypes[name][1], rename(name), ', '.join('%s arg_%i' % (type, i) for i, type in enumerate(self.wordtypes[name][0])))
		for name, (locals, effects) in self.words.items():
			print '%s %s(%s) {' % (self.wordtypes[name][1], rename(name), ', '.join('%s arg_%i' % (type, i) for i, type in enumerate(self.wordtypes[name][0])))
			for effect in effects:
				line = structure(effect)
				sup = False
				if isinstance(line, tuple):
					line, sup = line
				if sup:
					print '\t' + line
				else:
					print '\t' + line + ';'
			print '}'

	def parsewords(self, code):
		def sanitize(name, macro):
			spec = macrospec[name]
			preamble = []
			for elem in spec[::-1]:
				preamble.append('=>__macro_' + name + '_' + elem)
			for i, elem in enumerate(macro):
				if elem in spec:
					macro[i] = '__macro_' + name + '_' + elem
				elif isinstance(elem, unicode) and len(elem) > 1 and elem[0] == '*':
					macro[i] = '*__macro_' + name + '_' + elem[1:]
			macros[name] = preamble + macro

		parsed = Code(parse(code))
		parseloc = 0
		words, macros = {'main': []}, {}
		macrospec = {}
		wordtypes = {'main' : ((), 'void')}
		globals = []

		modstack = []
		cur = words['main']
		in_macro = None
		preamble = []

		while parsed.peek() is not None:
			token = parsed.consume()
			if token == ':':
				modstack.append(cur)
				name = parsed.consume()
				cur = words[name] = []

				argstart = parsed.consume()
				if argstart == '()':
					wordtypes[name] = (), 'void'
				else:
					assert argstart == '('
					args = []
					argnames = []
					ret = 'void'
					while parsed.peek() != ')':
						token = parsed.consume()
						if token == '->':
							ret = parsed.consume()
						else:
							token = token.split(':', 1)
							if len(token) == 1:
								args.append(token[0])
								argnames.append(None)
							else:
								args.append(token[1])
								argnames.append(token[0])
					parsed.consume()
					wordtypes[name] = tuple(args), ret
					assert len([_ for _ in argnames if _ != None]) == 0 or None not in argnames
					if None not in argnames:
						for name in argnames[::-1]:
							cur.append('=>' + name)
			elif token == ':m':
				modstack.append(cur)
				name = parsed.consume()
				cur = macros[name] = []
				macrospec[name] = []
				in_macro = name
				if parsed.peek() == '(':
					parsed.consume()
					while parsed.peek() != ')':
						macrospec[name].append(parsed.consume().split(':')[0])
					parsed.consume()
			elif token == ':globals':
				modstack.append(cur)
				cur = globals
			elif token == ';':
				if in_macro:
					sanitize(in_macro, cur)
					in_macro = None
				cur = modstack.pop()
			elif token == '(':
				depth = 1
				while parsed.peek() != None:
					token = parsed.consume()
					if token == '(':
						depth += 1
					elif token == ')':
						depth -= 1
						if depth == 0:
							break
			else:
				cur.append(token)

		for name, tokens in words.items():
			while True:
				rewrite = False
				for i, token in enumerate(tokens):
					if token in macros:
						tokens = tokens[:i] + macros[token] + tokens[i+1:]
						rewrite = True
						break
				if not rewrite:
					break
			words[name] = tokens

		locals, effects = self.compile('__globals', globals)
		self.globals.update(locals)
		assert len(effects) == 0

		return words, wordtypes, macros

	def compile(self, name, atoms):
		self.atoms = Code(atoms)
		self.rstack = Stack()
		self.sstack = Stack()
		self.locals = {}
		self.macrolocals = {}
		self.effects = []
		if name != '__globals':
			self.argcount = len(self.wordtypes[name][0])+1

		while self.atoms.peek() != None:
			token = self.atoms.consume()

			if not isinstance(token, unicode) and not isinstance(token, str):
				self.rstack.push(token)
			elif token in bwords:
				consumes, fn = bwords[token]
				if fn != None:
					fn(self, *[self.atoms.consume() for i in xrange(consumes)][::-1])
				else:
					self.rstack.push(tuple([token] + [self.rstack.pop() for i in xrange(consumes)][::-1]))
			elif len(token) > 1 and token[0] == '@':
				self.rstack.push(Type(token[1:]))
			elif len(token) > 1 and token[0] == '&':
				self.rstack.push(token[1:])
			elif len(token) > 1 and token[0] == '*':
				self.rstack.push(self.macrolocals[token[1:]])
				self.call()
			elif len(token) > 2 and token[:2] == '=>':
				self.macroassign(token[2:])
			elif len(token) > 1 and token[0] == '=':
				self.assign(token[1:])
			elif len(token) > 1 and token[0] == '.':
				elem = self.rstack.pop()
				for swizzle in token[1:].split('.'):
					self.rstack.push(('.' + swizzle, elem))
			elif len(token) > 1 and token[0] == '/':
				if token == '/{':
					self.map(self.block())
				else:
					self.map(token[1:])
			elif len(token) > 1 and token[0] == '\\':
				if token == '\\{':
					self.reduce(self.block())
				else:
					self.reduce(token[1:])
			elif token in self.globals or token in self.locals:
				self.rstack.push(('var', token))
			elif token in self.words:
				elem = tuple([token] + [self.rstack.pop() for i in xrange(len(self.wordtypes[token][0]))][::-1])
				if self.wordtypes[token][1] == 'void':
					self.effects.append(elem)
				else:
					self.rstack.push(elem)
			elif token in self.macrolocals:
				self.rstack.push(self.macrolocals[token])
			elif token == '[':
				self.sstack.push(self.rstack)
				self.rstack = Stack()
			elif token == ']':
				temp = self.rstack.list
				self.rstack = self.sstack.pop()
				self.rstack.push(temp)
			elif token == ']v':
				temp = self.rstack.list
				self.rstack = self.sstack.pop()
				self.rstack.push(temp)
				self.avec()
			elif token == '{':
				self.rstack.push(self.block())
			else:
				print 'unknown token', token

		assert len(self.rstack) <= 1
		if len(self.rstack) == 1:
			self.effects.append(('return', self.rstack.pop()))

		return self.locals, self.effects

	def block(self):
		depth = 1
		cdepth = 0
		atoms = []
		while True:
			token = self.atoms.consume()
			atoms.append(token)
			if token == '(':
				cdepth += 1
			elif token == ')':
				cdepth -= 1
			elif cdepth == 0 and token in ('{', '\\{', '/{'):
				depth += 1
			elif cdepth == 0 and token == '}':
				depth -= 1
				if depth == 0:
					break
		return atoms[:-1]

	def tempname(self):
		self.tempi += 1
		return '_temp_%i_' % self.tempi

	def eatcomment(self):
		depth = 1
		while self.atoms.peek() != None:
			token = self.atoms.consume()
			if token == ')':
				depth -= 1
				if depth == 0:
					return
			elif token == '(':
				depth += 1

	def argument(self):
		assert self.argcount > 0
		self.argcount -= 1
		return ('arg', 'arg_%i' % (self.argcount-1))

	def assign(self, name):
		if isinstance(self.rstack.top(), Type):
			type = self.rstack.pop()
			self.locals[name] = type
		else:
			elem = self.rstack.pop()
			if name not in self.locals and name not in self.globals:
				self.locals[name] = Type(self.infertype(elem))
			self.effects.append(('=', ('var', name), elem))

	def map(self, name):
		tlist = self.rstack.pop()

		atoms = self.blockify(name)
		tatoms = []
		tatoms.append(u'[')
		for i, val in enumerate(tlist):
			tname = u'__temp_%i' % i
			self.macrolocals[tname] = val
			tatoms.append(tname)
			tatoms += atoms
		tatoms.append(u']')
		self.atoms.insert(tatoms)

	def reduce(self, name):
		elems = self.rstack.pop()
		
		atoms = self.blockify(name)
		tatoms = []
		for i, val in enumerate(elems):
			tname = u'__temp_%i' % i
			self.macrolocals[tname] = val
			tatoms.append(tname)
			if i != 0:
				tatoms += atoms
		self.atoms.insert(tatoms)

	def macroassign(self, name):
		self.macrolocals[name] = self.rstack.pop()

	def infertype(self, expr):
		if isinstance(expr, tuple):
			if expr[0] == 'var':
				name = expr[1]
				if name in self.globals:
					return self.globals[name].name
				elif name in self.locals:
					return self.locals[name].name
				else:
					assert False
			elif expr[0][0] == '.':
				if len(expr[0]) == 2:
					return 'float'
				else:
					return 'vec%i' % (len(expr[0])-1)
			elif expr[0] in gltypes:
				return gltypes[expr[0]]
			elif expr[0] in self.words:
				return self.wordtypes[expr[0]][1]
			else:
				types = map(self.infertype, expr[1:])
				mat = vec = other = None
				for type in types:
					if 'mat' in type:
						mat = type
					elif 'vec' in type:
						vec = type
					else:
						other = type
				return mat or vec or other
		else:
			return 'float'
		assert False

	@word('dup')
	def dup(self):
		top = self.rstack.pop()

		if not isinstance(top, tuple):
			inline = True
		elif top[0] == 'var' or top[0] == 'arg':
			inline = True
		elif top[0][0] == '.' and top[1][0] == 'var':
			inline = True
		else:
			inline = False

		if inline:
			self.rstack.push(top)
			self.rstack.push(top)
		else:
			temp = 'var_%i' % len(self.locals)
			self.locals[temp] = Type(self.infertype(top))
			temp = ('var', temp)
			self.effects.append(('=', temp, top))
			self.rstack.push(temp)
			self.rstack.push(temp)

	@word('swap')
	def swap(self):
		a, b = self.rstack.pop(), self.rstack.pop()
		self.rstack.push(a)
		self.rstack.push(b)

	@word('uniform')
	def uniform(self):
		self.rstack.top().attribute('uniform')

	@word('negate')
	def negate(self):
		self.rstack.push(('-', self.rstack.pop()))

	@word('(')
	def nullparen_open(self):
		self.eatcomment()

	@word('flatten')
	def flatten(self):
		for elem in self.rstack.pop():
			self.rstack.push(elem)

	@word('avec')
	def avec(self):
		tlist = self.rstack.pop()
		self.rstack.push(tuple(['vec%i' % len(tlist)] + tlist))

	@word('call')
	def call(self):
		name = self.rstack.pop()

		atoms = self.blockify(name)
		self.atoms.insert(atoms)

	def blockify(self, atom):
		if isinstance(atom, list):
			return atom

		if atom in self.macros:
			return self.macros[atom]
		elif atom in self.words or atom in bwords:
			return [atom]
		else:
			print atom
			assert False

	@word('times')
	def times(self):
		count = self.rstack.pop()
		block = self.blockify(self.rstack.pop())
		var = self.tempname()

		self.effects.append(('for', var, 0, count))
		self.rstack.push('__term__')
		self.rstack.push(('var', var))
		self.atoms.insert(list(block) + ['__endblock'])
		self.locals[var] = Type('int')

	@word('when')
	def when(self):
		cond = self.rstack.pop()
		block = self.blockify(self.rstack.pop())

		self.effects.append(('if', cond))
		self.rstack.push('__term__')
		self.atoms.insert(list(block) + ['__endblock'])

	@word('if')
	def if_(self):
		cond = self.rstack.pop()
		else_ = self.blockify(self.rstack.pop())
		if_ = self.blockify(self.rstack.pop())

		self.effects.append(('if', cond))
		self.rstack.push(else_)
		self.rstack.push('__if_term__')
		self.atoms.insert(list(if_) + ['__else'])

	@word('__else')
	def else_(self):
		self.effects.append(('else', ))
		while self.rstack.pop() != '__if_term__':
			pass
		else_ = self.rstack.pop()
		self.rstack.push('__term__')
		self.atoms.insert(list(else_) + ['__endblock'])

	@word('__endblock')
	def endblock(self):
		self.effects.append(('endblock', ))
		while self.rstack.pop() != '__term__':
			pass

	@word('break')
	def break_(self):
		self.effects.append(('break', ))

	@word('continue')
	def continue_(self):
		self.effects.append(('continue', ))

def main(fn, shadertoy=None):
	Compiler(file(fn, 'r').read().decode('utf-8'), shadertoy == '--shadertoy')

if __name__=='__main__':
	import sys
	main(*sys.argv[1:])
