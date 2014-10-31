from decimal import *
import re

def format_float(tval):
	if tval == Decimal('-0'):
		return '0.'
	val = str(Decimal(tval))
	if '.' not in val:
		return val + '.'
	elif val.startswith('0.'):
		return val[1:]
	elif val.startswith('-0.'):
		return '-' + val[2:]
	else:
		return val

getcontext().prec = 5
old_float = float
float = Decimal

def depcopy(deps):
	return dict((k, list(v)) for k, v in deps.items())

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
sfloat = regex(r'(-?[0-9]+)')
bint = regex(r'#(-?[0-9]+)')

satis = lambda inp, *funcs: any(func(inp) for func in funcs)

def parse(code):
	def sub(elem):
		if satis(elem, ffloat, efloat, sfloat):
			return float(elem)
		elif bint(elem):
			return int(elem[1:])
		else:
			return unicode(elem)

	code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
	code = map(sub, (elem for elem in code.replace('\n', ' ').replace('\t', ' ').split(' ') if elem != ''))

	return code

class Type(object):
	def __init__(self, name):
		self.name = name
		self.attributes = []
		self.array_count = None

	def attribute(self, name):
		self.attributes.append(name)

	def array(self, count):
		self.array_count = count

	def __repr__(self):
		return ' '.join(self.attributes) + (' ' if self.attributes else '') + self.name + ('' if self.array_count is None else '[%i]' % self.array_count)

	def rename(self):
		return ' '.join(self.attributes) + (' ' if self.attributes else '') + Compiler.instance.rename(self.name) + ('' if self.array_count is None else '[%i]' % self.array_count)

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

	def retrieve(self, offset, remove=False):
		offset = len(self.list)-offset-1
		elem = self.list[offset]
		if remove:
			self.list = self.list[:offset] + self.list[offset+1:]
		return elem

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
	'**' : (2, None), 
	'<' : (2, None), 
	'>' : (2, None), 
	'<=' : (2, None), 
	'>=' : (2, None), 
	'==' : (2, None), 
	'!=' : (2, None), 
}
foldops = {
	'+' : lambda a, b: a + b, 
	'-' : lambda a, b: a - b, 
	'*' : lambda a, b: a * b, 
	'/' : lambda a, b: a / b, 
	'**' : lambda a, b: a ** b, 
}
glfuncs = dict(
	dot=2, 
	sin=1, 
	abs=1, 
	atan=1, 
	atan2=2, 
	cos=1, 
	exp=1, 
	sqrt=1, 
	mod=2, 
	tan=1, 
	min=2, 
	max=2, 
	length=1, 
	normalize=1, 
	cross=2, 
	mix=3, 
	mat2=4, 
	mat3=9, 
	mat4=16, 
	reflect=2, 
	refract=3, 
	int=1, 
	clamp=3,
	smoothstep=3, 
	ceil=1, 
	floor=1, 
	sign=1, 
	texture2D=2, 
	log=1, 
	log2=1, 
	vec2=1, 
)
gltypes = dict(
	dot='float', 
	vec2='vec2',
	vec3='vec3',
	vec4='vec4',
	length='float', 
	mat2='mat2', 
	mat3='mat3', 
	mat4='mat4', 
	float='float', 
	int='int',
	sampler2D='sampler2D'
)
btypes = 'void int float bool vec2 vec3 vec4 mat2 mat3 mat4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4'.split(' ')
for name, consumes in glfuncs.items():
	bwords[name] = (consumes, None)
class Compiler(object):
	def __init__(self, code, utility, shadertoy=False, minimize=False):
		self.barecode = code
		self.code = utility + code
		self.tempi = 0
		self.shadertoy = shadertoy
		self.minimize = minimize
		Compiler.instance = self
		self.globals = dict(
			gl_FragCoord=Type('vec4'), 
			gl_FragColor=Type('vec4'), 
		)
		self.options = []
		self.renamed = {}
		self.rename_i = 0
		self.words, self.wordtypes, self.macros, self.structs = self.parsewords(self.code)
		self.deps = {}
		self.mainWords = {}

		for name, atoms in self.words.items():
			self.words[name] = self.compile(name, atoms)
			self.deps[name] = deps = []
			for atom in atoms:
				if not isinstance(atom, unicode):
					continue
				if atom[0] in '&\\/':
					atom = atom[1:]
				if atom in self.words and atom not in deps:
					deps.append(atom)

		self.passes, eps = self.parsepasses()
		eps.append('main')
		for i, ep in enumerate(eps):
			if len(self.words[ep][1]) == 0:
				del eps[i]

		self.outcode = {}
		for ep in eps:
			code = self.output(ep)
			if minimize:
				self.outcode[ep] = self.minshader(code)
			else:
				self.outcode[ep] = code.rstrip('\n')

	def minshader(self, code):
		code = re.sub(r'//.*$', '', code)
		code = code.replace('\n', ' ').replace('\t', ' ')
		code = re.sub(r' +', ' ', code)
		code = re.sub(r'/\*.*?\*/', '', code)
		code = re.sub(r' +', ' ', code)
		code = re.sub(r'\.0+([^0-9])', r'.\1', code)
		code = re.sub(r'0+([1-9]+\.[^a-z_])', r'\1', code, re.I)
		code = re.sub(r'0+([1-9]*\.[0-9])', r'\1', code)
		code = re.sub(r'\s*(;|{|}|\(|\)|=|\+|-|\*|\/|\[|\]|,|\.|%|!|~|\?|:|<|>)\s*', r'\1', code)
		return code.strip()

	def emitnl(self, *args):
		self.emitted += ' '.join(args) + '\n'

	def output(self, main):
		self.emitted = ''
		indentlevel = [1]
		operators = 'neg + - / * ** < > <= >= == != && ||'.split(' ')
		precedence = {
			'?:' : 1, 
			'+'  : 2, 
			'-'  : 2, 
			'*'  : 3, 
			'/'  : 3, 
			'**' : 4, 
			'==' : 4, 
			'!=' : 4, 
			'<'  : 4, 
			'>'  : 4, 
			'<=' : 4, 
			'>=' : 4, 
			'||' : 4, 
			'&&' : 4, 
			'.'  : 10, 
			'[]' : 10,
			'neg' : 10, 
		}
		def minprec(atom, op=None):
			if not isinstance(atom, tuple) or len(atom) == 0 or atom[0] not in operators:
				return 1000
			tmin = min([precedence[atom[0]]] + map(lambda x: minprec(x, atom[0]), atom))
			if op is not None and tmin < precedence[op]:
				return 1000
			return tmin
		def paren(atom, op=None, left=None):
			need = True
			right_div_sub = left == False and op in '-/'
			if not isinstance(atom, tuple):
				if atom is True:
					return 'true'
				elif atom is False:
					return 'false'
				elif isinstance(atom, float):
					return format_float(atom)
				return unicode(atom)
			elif atom[0] not in operators or op is None:
				need = False
			elif (minprec(atom) >= precedence[op] and not right_div_sub) or (minprec(atom) > precedence[op] and right_div_sub):
				need = False
			return '(%s)' % structure(atom) if need else structure(atom)
		def structure(atom):
			if not isinstance(atom, tuple):
				if atom is True:
					return 'true'
				elif atom is False:
					return 'false'
				elif isinstance(atom, float):
					return format_float(atom)
				return unicode(atom)

			if atom[0] == '**':
				return 'pow(%s, %s)' % (structure(atom[1]), structure(atom[2]))
			if atom[0] in operators:
				if atom[0] == 'neg':
					return '-%s' % paren(atom[1], 'neg')
				else:
					return '%s %s %s' % (paren(atom[1], atom[0], True), atom[0], paren(atom[2], atom[0], False))
			elif atom[0] == '=':
				if atom[2] is None:
					return '%s' % structure(atom[1])
				else:
					return '%s = %s' % (structure(atom[1]), structure(atom[2]))
			elif atom[0][0] == '.':
				swizzle = atom[0]
				if atom[2]:
					swizzle = '.' + self.rename(atom[0][1:])
				return '%s%s' % (paren(atom[1], '.'), swizzle)
			elif atom[0] == 'var':
				if atom[1].startswith('gl_') or atom[1] in self.globals or atom[1] in defd:
					return self.rename(atom[1])
				else:
					defd.append(atom[1])
					return '%s %s' % (locals[atom[1]].rename(), self.rename(atom[1]))
			elif atom[0] == 'arg':
				return self.rename(atom[1])
			elif atom[0] == 'return':
				if len(atom) == 2:
					return 'return %s' % structure(atom[1])
				else:
					return 'return'
			elif atom[0] == 'for':
				_, name, start, top = atom
				defd.append(name)
				name = self.rename(name)
				indentlevel[0] += 1
				return 'for(int %s = %s; %s < %s; ++%s) {' % (name, structure(start), name, structure(top), name), True
			elif atom[0] == 'if':
				indentlevel[0] += 1
				return 'if(%s) {' % structure(atom[1]), True
			elif atom[0] == 'else':
				return '} else {', True
			elif atom[0] == 'elif':
				return '} else if(%s) {' % structure(atom[1]), True
			elif atom[0] == 'endblock':
				indentlevel[0] -= 1
				return '}', True
			elif atom[0] == 'break':
				return 'break'
			elif atom[0] == 'continue':
				return 'continue'
			elif atom[0] == '?:':
				c, a, b = atom[1:]
				return '%s ? %s : %s' % (paren(c, '?:'), paren(a, '?:'), paren(b, '?:'))
			elif atom[0] == '[]':
				return '%s[%s]' % (paren(atom[1], '[]'), structure(atom[2]))
			else:
				return '%s(%s)' % (self.rename(atom[0]), ', '.join(map(structure, atom[1:])))

		if self.shadertoy:
			self.emitnl('/* Compiled with Shaderforth: https://github.com/daeken/Shaderforth')
			self.emitnl(self.barecode.rstrip('\n'))
			self.emitnl('*/')
			self.emitnl()

		for name, elems in self.structs.items():
			self.emitnl('struct %s {' % self.rename(name))
			for name, type in elems:
				self.emitnl('\t%s %s;' % (type.rename(), self.rename(name)))
			self.emitnl('};')
		for name, type in self.globals.items():
			if name.startswith('gl_') or (self.shadertoy and 'uniform' in type.attributes):
				continue

			self.emitnl(type.rename(), self.rename(name) + ';')

		required = [main]
		checked = []
		while len(checked) < len(required):
			for dep in required:
				if dep in checked:
					continue
				for elem in self.deps[dep]:
					if elem not in required:
						required.append(elem)
				checked.append(dep)
		dead = [name for name in self.words if name not in required]

		deps = depcopy(self.deps)
		wordorder = []
		while len(deps):
			for name, wdeps in deps.items():
				made = True
				for dname in wdeps:
					if dname not in wordorder:
						made = False
						break
				if made:
					del deps[name]
					wordorder.append(name)
					break
		for name in wordorder:
			if name in dead:
				continue
			locals, effects, localorder = self.words[name]
			defd = self.wordtypes[name][2]
			effects = self.predeclare(effects)

			if name == main:
				if name in self.mainWords:
					pname = self.mainWords[name]
				else:
					pname = 'main'
			else:
				pname = name

			self.emitnl('%s %s(%s) {' % (self.rename(self.wordtypes[name][1]) if pname != 'main' else 'void', self.rename(name) if pname == name else pname, ', '.join('%s %s' % (self.rename(type), self.rename(self.wordtypes[name][2][i])) for i, type in enumerate(self.wordtypes[name][0]))))
			for effect in effects:
				prev = indentlevel[0]
				line = structure(effect)
				sup = False
				if isinstance(line, tuple):
					line, sup = line
				if sup:
					if prev <= indentlevel[0]:
						off = 1
					else:
						off = 0
					self.emitnl('\t' * (indentlevel[0] - off) + line)
				else:
					self.emitnl('\t' * indentlevel[0] + line + ';')
			self.emitnl('}')

		return self.emitted

	def predeclare(self, effects):
		def vars_referenced(effect):
			if not isinstance(effect, tuple) and not isinstance(effect, list):
				return []
			if effect[0] == 'var':
				return [effect[1]]
			return reduce(lambda a, b: a + b, map(vars_referenced, effect))

		declared = list(self.globals.keys())
		need = []
		decls = [[]]
		inside = []
		for effect in effects:
			if effect[0] in ('if', 'while', 'for'):
				decls.append([])
			elif effect[0] in ('else', 'elif'):
				inside += decls.pop()
				assert len(decls)
				decls.append([])
			elif effect[0] == 'endblock':
				inside += decls.pop()
				assert len(decls)
			elif effect[0] == '=' and effect[1][0] == 'var':
				decls[-1].append(effect[1][1])
			refs = vars_referenced(effect)
			for ref in refs:
				if ref in inside and ref not in need:
					need.append(ref)
		return [('=', ('var', var), None) for var in need] + effects

	def rename(self, name):
		if name in glfuncs or name in btypes or name.startswith('gl_'):
			if name == 'atan2':
				return 'atan'
			return name
		elif name in self.globals and ('uniform' in self.globals[name].attributes or 'varying' in self.globals[name].attributes):
			return name
		elif name in self.renamed:
			return self.renamed[name]
		elif not self.minimize:
			self.renamed[name] = name = name.replace('-', '_').replace('>', '_').replace('<', '_').replace('?', '_').replace('__', '_')
			return name
		else:
			first = '_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
			rest = first + '0123456789'
			ti = self.rename_i
			sname = first[ti % len(first)]
			ti /= len(first)
			while ti > 0:
				sname += rest[ti % len(rest)]
				ti /= len(rest)
			self.renamed[name] = sname
			self.rename_i += 1
			return sname

	def parsewords(self, code):
		def sanitize(name, macro):
			spec = macrospec[name]
			stored = [elem[1:] for elem in spec if elem.startswith('$')]
			spec = [elem[1:] if elem.startswith('$') else elem for elem in spec]
			preamble = []
			for i, elem in enumerate(spec):
				if i != len(spec) - 1:
					preamble.append(len(spec) - i - 1)
					preamble.append('take')
				if elem in stored:
					preamble.append('=macro_' + name + '_' + elem)
				else:
					preamble.append('=>macro_' + name + '_' + elem)
			for i, elem in enumerate(macro):
				if elem in spec:
					macro[i] = 'macro_' + name + '_' + elem
				elif isinstance(elem, unicode) and len(elem) > 1 and elem[0] in '*\\/' and elem[1:] in spec:
					macro[i] = elem[0] + 'macro_' + name + '_' + elem[1:]
			macros[name] = preamble + macro

		parsed = Code(parse(code))
		parseloc = 0
		words, macros = {'main': []}, {}
		macrospec = {}
		wordtypes = {'main' : ((), 'void', []), 'texture2D' : ((), 'vec4', [])}
		globals = []
		self.passes = []
		structs = {}

		modstack = []
		cur = words['main']
		in_macro = None
		preamble = []

		comment_depth = 0

		while parsed.peek() is not None:
			token = parsed.consume()

			if token == '(':
				comment_depth += 1
				cur.append(token)
				continue

			if comment_depth > 0:
				if token == ')':
					comment_depth -= 1
				cur.append(token)
				continue

			if token == ':':
				modstack.append(cur)
				name = parsed.consume()
				cur = words[name] = []

				argstart = parsed.consume()
				if argstart == '()':
					wordtypes[name] = (), 'void', []
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
					assert len([_ for _ in argnames if _ != None]) == 0 or None not in argnames
					if None in argnames:
						argnames = ['arg_%i' % i for i in xrange(len(argnames))]
					wordtypes[name] = tuple(args), ret, argnames
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
			elif token == ':passes':
				modstack.append(cur)
				cur = self.passes
			elif token == ':struct':
				modstack.append(cur)
				name = parsed.consume()
				cur = structs[name] = []
			elif token == ';':
				if in_macro:
					sanitize(in_macro, cur)
					in_macro = None
				cur = modstack.pop()
			else:
				cur.append(token)

		for name, tokens in words.items():
			words[name] = self.expandmacros(name, tokens, macros)

		self.words = {}
		locals, effects, localorder = self.compile('__globals', globals, pre=True)
		self.globals.update(locals)

		def subword(name):
			return lambda self: self.rstack.push(tuple([name] + self.rstack.pop()[1:]))
		sdefs = {}
		for name, atoms in structs.items():
			locals, effects, localorder = self.compile('__' + name, atoms, pre=True)
			sdefs[name] = [(ename, locals[ename]) for ename in localorder]
			word(name)(subword(name))
			gltypes[name] = name

		return words, wordtypes, macros, sdefs

	def expandmacros(self, wname, tokens, macros):
		def sub(atoms, deps):
			i = 0
			while i < len(atoms):
				token = atoms[i]
				if token in macros and token not in deps:
					rep = rex(macros[token], deps + [token])
					atoms = atoms[:i] + rep + atoms[i+1:]
					i += len(rep)
				else:
					i += 1
			return atoms
		def rex(atoms, deps):
			while True:
				natoms = sub(atoms, deps)
				if natoms == atoms:
					return natoms
				atoms = natoms

		tokens = sub(tokens, [wname])
		return tokens

	def parsepasses(self):
		self.dimensions = {}
		locals, effects, localorder = self.compile('__passes', self.passes, pre=True)
		passes = []
		eps = []
		for effect in effects:
			assert effect[0] == '='
			if effect[2][0] == 'var':
				passes.append((effect[1][1], effect[2][1]))
			else:
				if effect[1][1] == 'sound-pass':
					self.mainWords[effect[2][0]] = 'mainSound'
				eps.append(effect[2][0])
				passes.append((effect[1][1], effect[2][0]))
		return passes, eps

	def fold_constants(self, op, operands):
		def eligible(val):
			return isinstance(val, float) or isinstance(val, int) or isinstance(val, list)

		def fold(a, b):
			getcontext().prec = 5
			if isinstance(a, list):
				if isinstance(b, list):
					assert len(a) == len(b)
					return ['array'] + map(lambda i: self.fold_constants(op, [a[i], b[i]]), xrange(1, len(a)))
				elif False not in map(eligible, a):
					return ['array'] + map(lambda x: foldops[op](x, b), a[1:])
				else:
					return tuple([op, a, b])
			else:
				return foldops[op](a, b)

		if False not in map(eligible, operands):
			return reduce(fold, operands)
		else:
			return tuple([op] + operands)

	def fold_swizzles(self, elem, swizzles):
		def eligible(arr, top=False):
			if not isinstance(arr, list) and not isinstance(arr, tuple):
				return True
			elif arr[0] == 'array':
				return False not in map(eligible, arr[1:])
			elif arr[0] == 'var' and not top:
				return True
			return False

		letterElem = dict(x=0, y=1, z=2, w=3, r=0, g=1, b=2, a=3)

		if eligible(elem, top=True):
			for swizzle in swizzles:
				if len(swizzle) == 1:
					self.rstack.push(elem[letterElem[swizzle] + 1])
				else:
					self.rstack.push(['array'] + [elem[letterElem[char] + 1] for char in swizzle])
		else:
			for swizzle in swizzles:
				self.rstack.push(('.' + swizzle, elem, False))

	def compile(self, name, atoms, pre=False):
		Compiler.compiling = name
		self.atoms = Code(atoms)
		self.rstack = Stack()
		self.sstack = Stack()
		self.locals = {}
		self.localorder = []
		self.macrolocals = {}
		self.effects = []
		if not pre:
			self.argcount = len(self.wordtypes[name][0])+1
			argtypes = self.wordtypes[name][0]
			self.argnames = self.wordtypes[name][2]
			self.argtypes = dict((self.argnames[i], type) for i, type in enumerate(argtypes))
			for name, type in self.argtypes.items():
				self.locals[name] = Type(type)

		while self.atoms.peek() != None:
			token = self.atoms.consume()

			if not isinstance(token, unicode) and not isinstance(token, str):
				self.rstack.push(token)
			elif token in bwords:
				consumes, fn = bwords[token]
				if fn != None:
					fn(self, *[self.atoms.consume() for i in xrange(consumes)][::-1])
				elif token in foldops:
					operands = [self.rstack.pop() for i in xrange(consumes)][::-1]
					
					self.rstack.push(self.fold_constants(token, operands))
				else:
					self.rstack.push(tuple([token] + [self.rstack.pop() for i in xrange(consumes)][::-1]))
			elif len(token) > 1 and token[0] == '@':
				self.rstack.push(Type(token[1:]))
			elif len(token) > 1 and token[0] == '&':
				self.rstack.push(token[1:])
			elif len(token) > 1 and token[0] == '*' and token != '**':
				self.rstack.push(self.macrolocals[token[1:]])
				self.call()
			elif len(token) > 2 and token[:2] == '=>':
				self.macroassign(token[2:])
			elif len(token) > 1 and token[0] == '=':
				self.assign(token[1:])
			elif token == '=':
				var = self.rstack.pop()
				value = self.rstack.pop()
				self.effects.append(('=', var, value))
			elif len(token) > 1 and token[0] == '.':
				elem = self.rstack.pop()
				is_struct = self.infertype(elem) in self.structs
				swizzles = token[1:].split('.')
				if is_struct:
					for swizzle in swizzles:
						self.rstack.push(('.' + swizzle, elem, is_struct))
				else:
					self.fold_swizzles(elem, swizzles)
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
			elif len(token) > 3 and token.startswith('$['):
				self.range(token[2:-1].split(':'))
			elif len(token) > 1 and token[0] == '!' and token != '!=':
				self.dup()
				self.atoms.insert([token[1:]])
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
				self.rstack.push(['array'] + temp)
			elif token == ']m':
				temp = self.rstack.list
				self.rstack = self.sstack.pop()
				self.rstack.push(['array'] + temp)
				self.amat()
			elif token == '{':
				self.rstack.push(self.block())
			elif token == 'true':
				self.rstack.push(True)
			elif token == 'false':
				self.rstack.push(False)
			else:
				print 'unknown token', token, self.rstack
				raise Exception('Unknown token')

		assert len(self.rstack) <= 1
		if len(self.rstack) == 1:
			self.effects.append(('return', self.rstack.pop()))

		self.effects = self.vectorize(self.effects)
		
		return self.locals, self.effects, self.localorder

	def vectorize(self, obj):
		if isinstance(obj, list) and len(obj) > 0 and obj[0] == 'array':
			self.rstack.push(map(self.vectorize, obj))
			self.avec()
			return self.rstack.pop()
		elif isinstance(obj, tuple):
			return tuple(map(self.vectorize, obj))
		elif isinstance(obj, list):
			return list(map(self.vectorize, obj))
		else:
			return obj

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
		atoms = atoms[:-1]
		if len(atoms) and atoms[0] == '(':
			spec = []
			stored = []
			for atom in atoms[1:]:
				if atom == ')':
					break
				if atom.startswith('$'):
					stored.append(atom[1:])
					atom = atom[1:]
				spec.append(atom)
			atoms = atoms[2+len(spec):]
			name = self.tempname()
			preamble = []
			for i, elem in enumerate(spec):
				if i != len(spec) - 1:
					preamble.append(len(spec) - i - 1)
					preamble.append('take')
				if elem in stored:
					preamble.append('=macro_' + name + '_' + elem)
				else:
					preamble.append('=>macro_' + name + '_' + elem)
			for i, elem in enumerate(atoms):
				if elem in spec:
					atoms[i] = 'macro_' + name + '_' + elem
				elif isinstance(elem, unicode) and len(elem) > 1 and elem[0] in '*\\/' and elem[1:] in spec:
					atoms[i] = elem[0] + 'macro_' + name + '_' + elem[1:]
			atoms = preamble + atoms

		return atoms

	def tempname(self):
		self.tempi += 1
		return 'temp_%i' % self.tempi

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
		return ('arg', self.argnames[self.argcount-1])

	def assign(self, name):
		if isinstance(self.rstack.top(), Type):
			type = self.rstack.pop()
			self.locals[name] = type
			if name not in self.localorder:
				self.localorder.append(name)
			self.effects.append(('=', ('var', name), None))
		else:
			elem = self.rstack.pop()
			if name not in self.locals and name not in self.globals:
				self.locals[name] = Type(self.infertype(elem))
				self.localorder.append(name)
			self.effects.append(('=', ('var', name), elem))

	def map(self, name):
		tlist = self.rstack.pop()
		if tlist[0] != 'array':
			self.rstack.push(tlist)
			self.veca()
			tlist = self.rstack.pop()
		
		atoms = self.blockify(name)
		tatoms = []
		tatoms.append(u'[')
		for i, val in enumerate(tlist[1:]):
			tname = self.tempname()
			self.macrolocals[tname] = val
			tatoms.append(tname)
			tatoms += atoms
		tatoms.append(u']')
		self.atoms.insert(tatoms)

	def reduce(self, name):
		tlist = self.rstack.pop()
		if tlist[0] != 'array':
			self.rstack.push(tlist)
			self.veca()
			tlist = self.rstack.pop()

		atoms = self.blockify(name)
		tatoms = []
		for i, val in enumerate(tlist[1:]):
			tname = self.tempname()
			self.macrolocals[tname] = val
			tatoms.append(tname)
			if i != 0:
				tatoms += atoms
		self.atoms.insert(tatoms)

	def macroassign(self, name):
		self.macrolocals[name] = self.rstack.pop()

	def infertype(self, expr):
		if isinstance(expr, tuple) or isinstance(expr, list):
			if expr[0] == 'var':
				name = expr[1]
				if name in self.globals:
					return self.globals[name].name
				elif name in self.locals:
					return self.locals[name].name
				else:
					assert False
			elif expr[0] == 'arg':
				return self.argtypes[expr[1]]
			elif expr[0][0] == '.':
				subtype = self.infertype(expr[1])
				if subtype in self.structs:
					return str(dict(self.structs[subtype])[expr[0][1:]])
				elif len(expr[0]) == 2:
					return 'float'
				else:
					return 'vec%i' % (len(expr[0])-1)
			elif expr[0].startswith('vec'):
				return expr[0]
			elif expr[0] == 'array':
				types = map(self.infertype, expr[1:])
				length = 0
				for type in types:
					if type.startswith('vec'):
						length += int(type[3:])
					elif type == 'float':
						length += 1
					else:
						assert False

				return 'vec%i' % length
			elif expr[0] in gltypes:
				return gltypes[expr[0]]
			elif expr[0] in self.wordtypes:
				return self.wordtypes[expr[0]][1]
			elif expr[0] == '[]':
				return self.infertype(expr[1])
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
				return vec or mat or other
		elif isinstance(expr, bool):
			return 'bool'
		elif isinstance(expr, int):
			return 'int'
		else:
			return 'float'
		assert False

	def ensure_stored(self, pop=False):
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
			if not pop:
				self.rstack.push(top)
			return top
		else:
			temp = 'var_%i' % len(self.locals)
			self.locals[temp] = Type(self.infertype(top))
			temp = ('var', temp)
			self.effects.append(('=', temp, top))
			if not pop:
				self.rstack.push(temp)
			return temp

	@word('dup')
	def dup(self):
		self.rstack.push(self.ensure_stored())

	@word('swap')
	def swap(self):
		a, b = self.rstack.pop(), self.rstack.pop()
		self.rstack.push(a)
		self.rstack.push(b)

	@word('uniform')
	def uniform(self):
		self.rstack.top().attribute('uniform')

	@word('(')
	def nullparen_open(self):
		self.eatcomment()

	@word('flatten')
	def flatten(self):
		for elem in self.rstack.pop()[1:]:
			self.rstack.push(elem)

	@word('avec')
	def avec(self):
		tlist = self.rstack.pop()
		assert tlist[0] == 'array'
		tlist = tlist[1:]
		types = map(self.infertype, tlist)
		length = 0
		for type in types:
			if type.startswith('vec'):
				length += int(type[3:])
			elif type == 'float':
				length += 1
			else:
				assert False
		self.rstack.push(tuple(['vec%i' % length] + tlist))

	@word('veca')
	def veca(self):
		vec = self.ensure_stored(pop=True)
		type = self.infertype(vec)
		assert 'vec' in type
		size = int(type[type.find('vec')+3:])
		self.rstack.push(['array'] + [('.' + 'xyzw'[i], vec, False) for i in xrange(size)])

	@word('amat')
	def amat(self):
		tlist = self.rstack.pop()
		assert tlist[0] == 'array'
		tlist = tlist[1:]
		if len(tlist) == 4:
			size = 2
		elif len(tlist) == 9:
			size = 3
		elif len(tlist) == 16:
			size = 4
		else:
			assert False
		self.rstack.push(tuple(['mat%i' % size] + tlist))

	@word('=[')
	def arrayass(self):
		names = []
		while True:
			token = self.atoms.consume()
			if token == ']':
				break
			names.append(token)
		arr = self.rstack.pop()
		for i, name in enumerate(names):
			self.rstack.push(arr[i+1])
			self.assign(name)

	@word('=>[')
	def arraymass(self):
		names = []
		while True:
			token = self.atoms.consume()
			if token == ']':
				break
			names.append(token)
		arr = self.rstack.pop()
		for i, name in enumerate(names):
			self.rstack.push(arr[i+1])
			self.macroassign(name)

	@word('call')
	def call(self):
		name = self.rstack.pop()

		atoms = self.blockify(name)
		self.atoms.insert(atoms)

	def blockify(self, atom):
		if isinstance(atom, list):
			return atom

		if atom in self.macrolocals:
			atom = self.macrolocals[atom]

		if atom in self.macros:
			return self.macros[atom]
		elif atom in self.words or atom in bwords:
			return [atom]
		else:
			print 'Unknown atom to blockify', atom
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

	@word('mtimes')
	def mtimes(self):
		count = self.rstack.pop()
		block = self.blockify(self.rstack.pop())

		for i in xrange(int(count)):
			self.atoms.insert([i] + list(block))

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
		self.rstack.push('__term__')
		self.atoms.insert(list(if_) + ['__else'])

	@word('__else')
	def else_(self):
		ass = []
		expand = []
		while True:
			if self.rstack.top() == '__term__':
				self.rstack.pop()
				break
			var = self.tempname()
			ass.append('=' + var)
			expand = [var] + expand
			self.assign(var)
		self.effects.append(('else', ))
		else_ = self.rstack.pop()
		self.rstack.push('__term__')
		self.atoms.insert(list(else_) + ass + ['__endblock'] + expand)

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

	@word('select')
	def select(self):
		cond = self.rstack.pop()
		b = self.rstack.pop()
		a = self.rstack.pop()

		self.rstack.push(('?:', cond, a, b))

	@word('return')
	def return_(self):
		self.effects.append(('return', self.rstack.pop()))

	@word('return-nil')
	def return_nil(self):
		self.effects.append(('return', ))

	@word('cond')
	def cond(self):
		arr = self.rstack.pop()
		assert arr[0] == 'array'

		(cond, block), arr = arr[1:3], arr[3:]
		block = self.blockify(block)

		self.effects.append(('if', cond))
		self.rstack.push(arr)
		self.rstack.push(None)
		self.rstack.push('__term__')
		self.atoms.insert(list(block) + ['__cond'])

	@word('__cond')
	def __cond(self):
		vals = []
		while True:
			if self.rstack.top() == '__term__':
				self.rstack.pop()
				break
			vals.append(self.rstack.pop())
		vars = self.rstack.pop()
		if vars == None:
			vars = [self.tempname() for val in vals]
		assert len(vars) == len(vals)
		for i, val in enumerate(vals):
			self.rstack.push(val)
			self.assign(vars[i])
		arr = self.rstack.pop()
		if len(arr) == 0:
			self.effects.append(('endblock', ))
			vars.reverse()
			self.atoms.insert(vars)
			return
		elif len(arr) == 1:
			block = arr[0]
			arr = []
			self.effects.append(('else', ))
		else:
			(cond, block), arr = arr[:2], arr[2:]
			self.effects.append(('elif', cond))

		block = self.blockify(block)
		self.rstack.push(arr)
		self.rstack.push(vars)
		self.rstack.push('__term__')
		self.atoms.insert(list(block) + ['__cond'])

	@word('and')
	def and_(self):
		b, a = self.rstack.pop(), self.rstack.pop()
		self.rstack.push(('&&', a, b))

	@word('or')
	def or_(self):
		b, a = self.rstack.pop(), self.rstack.pop()
		self.rstack.push(('||', a, b))

	@word('not')
	def not_(self):
		self.rstack.push(('!', self.rstack.pop()))

	@word('choose')
	def choose(self):
		val = self.rstack.pop()
		arr = self.rstack.pop()
		assert arr[0] == 'array'

		cur = arr.pop()
		while len(arr) > 2:
			left = arr.pop()
			comp = arr.pop()
			cur = ('?:', ('==', val, comp), left, cur)

		self.rstack.push(cur)

	@word('take')
	def take(self):
		pos = self.rstack.pop()
		elem = self.rstack.retrieve(pos, remove=True)
		self.rstack.push(elem)

	@word('array')
	def array(self):
		count = self.rstack.pop()
		type = self.rstack.top()
		type.array(count)

	@word('[]')
	def index(self):
		index = self.rstack.pop()
		arr = self.rstack.pop()
		self.rstack.push(('[]', arr, index))

	@word('size')
	def size(self):
		arr = self.rstack.pop()
		if len(arr) and arr[0] == 'array':
			off = 1
		else:
			off = 0
		self.rstack.push(float(len(arr) - off))

	@word('float')
	def float(self):
		val = self.rstack.pop()
		if isinstance(val, float) or isinstance(val, int):
			self.rstack.push(float(val))
		else:
			self.rstack.push(('float', val))

	@word('int')
	def int(self):
		val = self.rstack.pop()
		if isinstance(val, float) or isinstance(val, int):
			self.rstack.push(int(val))
		else:
			self.rstack.push(('int', val))

	@word('neg')
	def neg(self):
		val = self.rstack.pop()
		if isinstance(val, float) or isinstance(val, int):
			self.rstack.push(-val)
		else:
			self.rstack.push(('neg', val))

	@word('drop')
	def drop(self):
		self.rstack.pop()

	@word('set-dimensions')
	def set_dimensions(self):
		var = self.rstack.pop()
		_, width, height = self.rstack.pop()
		self.dimensions[var] = old_float(width), old_float(height)

	@word('toggle')
	def toggle(self):
		var = self.rstack.pop()
		self.options.append((var, 'toggle', None))

	@word('recur')
	def recur(self):
		depth = self.rstack.pop()
		_else = self.blockify(self.rstack.pop())
		_if = self.blockify(self.rstack.pop())

		if depth == 0:
			self.atoms.insert(self.expandmacros(None, _else, self.macros))
		else:
			atoms = self.expandmacros(None, _if, self.macros)
			for i, atom in enumerate(atoms):
				if atom == 'recur':
					atoms[i-1] = depth - 1
			self.atoms.insert(atoms)

	def range(self, elems):
		incl = True in ['+' in elem for elem in elems]
		elems = map(float, elems)
		val = ['array']
		if len(elems) == 1:
			start, max, step = 0., elems[0], 1.
		elif len(elems) == 2:
			(start, max), step = elems, 1.
		else:
			start, max, step = elems

		while (not incl and start < max) or (incl and start <= max):
			val.append(start)
			start += step

		self.rstack.push(val)

	@word('upto')
	def upto(self):
		top = self.rstack.pop()
		self.rstack.push(['array'] + list(map(float, range(int(top)))))

def main(fn, shadertoy=None, minimize=None):
	utility = file('utility.sfr', 'r').read().decode('utf-8')
	compiler = Compiler(file(fn, 'r').read().decode('utf-8'), utility, shadertoy == '--shadertoy', minimize == '--minimize')
	for name, code in compiler.outcode.items():
		print >>sys.stderr, '// Shader', name
		print code
		print >>sys.stderr

if __name__=='__main__':
	import sys
	main(*sys.argv[1:])
