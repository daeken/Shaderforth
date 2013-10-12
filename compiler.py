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

def word(symbol, consumes=0):
	def dec(fn):
		bwords[symbol] = consumes, fn
		return fn
	return dec

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

bwords = {}
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
class Compiler(object):
	def __init__(self, code):
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
			if name.startswith('gl_'):
				continue

			print type, rename(name) + ';'

		defd = []

		def structure(atom):
			if not isinstance(atom, tuple):
				return unicode(atom)

			if atom[0] in '+-/*':
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
			else:
				return '%s(%s)' % (rename(atom[0]), ', '.join(map(structure, atom[1:])))

		for name, (locals, effects) in self.words.items():
			print '%s %s(%s) {' % (self.wordtypes[name][1], rename(name), ', '.join('%s arg_%i' % (type, i) for i, type in enumerate(self.wordtypes[name][0])))
			for effect in effects:
				print '\t' + structure(effect) + ';'
			print '}'

	def parsewords(self, code):
		parsed = Code(parse(code))
		parseloc = 0
		words, macros = {'main': []}, {}
		wordtypes = {'main' : ((), 'void')}
		globals = []

		modstack = []
		cur = words['main']

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
					ret = 'void'
					while parsed.peek() != ')':
						token = parsed.consume()
						if token == '->':
							ret = parsed.consume()
						else:
							args.append(token)
					parsed.consume()
					wordtypes[name] = tuple(args), ret
			elif token == ':m':
				modstack.append(cur)
				cur = macros[parsed.consume()] = []
			elif token == ':globals':
				modstack.append(cur)
				cur = globals
			elif token == ';':
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
		self.argcount = 0

		while self.atoms.peek() != None:
			token = self.atoms.consume()

			if not isinstance(token, unicode):
				self.rstack.push(token)
			elif token in bwords:
				bwords[token][1](self, *(self.atoms.consume() for i in xrange(bwords[token][0])))
			elif len(token) > 1 and token[0] == '@':
				self.rstack.push(Type(token[1:]))
			elif len(token) > 2 and token[:2] == '=>':
				self.macroassign(token[2:])
			elif len(token) > 1 and token[0] == '=':
				self.assign(token[1:])
			elif len(token) > 1 and token[0] == '.':
				elem = self.rstack.pop()
				for swizzle in token[1:].split('.'):
					self.rstack.push(('.' + swizzle, elem))
			elif len(token) > 1 and token[0] == '/':
				self.map(token[1:])
			elif len(token) > 1 and token[0] == '\\':
				self.reduce(token[1:])
			elif token in glfuncs:
				self.rstack.push(tuple([token] + [self.rstack.pop() for i in xrange(glfuncs[token])][::-1]))
			elif token in '-+/*':
				b, a = self.rstack.pop(), self.rstack.pop()
				self.rstack.push((token, a, b))
			elif token in self.globals or token in self.locals:
				self.rstack.push(('var', token))
			elif token in self.words:
				self.rstack.push(tuple([token] + [self.rstack.pop() for i in xrange(len(self.wordtypes[token][0]))][::-1]))
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
			else:
				print 'unknown token', token

		assert len(self.rstack) <= 1
		if len(self.rstack) == 1:
			self.effects.append(('return', self.rstack.pop()))

		return self.locals, self.effects

	def argument(self):
		self.argcount += 1
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
		if name not in self.macros:
			self.rstack.push([(name, elem) for elem in tlist])
			return

		atoms = self.macros[name]
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
		if name not in self.macros:
			expr, elems = elems[0], elems[1:]
			for elem in elems:
				expr = (name, expr, elem)
			self.rstack.push(expr)
			return

		atoms = self.macros[name]
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
		return 'inferred'

	@word('dup')
	def dup(self):
		top = self.rstack.pop()

		if not isinstance(top, tuple):
			inline = True
		elif top[0] == 'var':
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
		b, a = self.rstack.pop(), self.rstack.pop()
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
		depth = 1
		while self.atoms.peek() != None:
			token = self.atoms.consume()
			if token == ')':
				depth -= 1
				if depth == 0:
					return
			elif token == '(':
				depth += 1

	@word('flatten')
	def flatten(self):
		for elem in self.rstack.pop():
			self.rstack.push(elem)

	@word('avec')
	def avec(self):
		tlist = self.rstack.pop()
		self.rstack.push(tuple(['vec%i' % len(tlist)] + tlist))

def main(fn):
	Compiler(file(fn, 'r').read().decode('utf-8'))

if __name__=='__main__':
	import sys
	main(*sys.argv[1:])
