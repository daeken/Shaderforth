from decimal import *
import pprint, re, sys

def format_float(tval):
	if _language == 'c++' or _language == 'js':
		return str(tval)
	if tval == Decimal('-0'):
		return '0.'
	val = ('%f' % Decimal(tval)).rstrip('0')
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

old_list = list
class list(old_list):
	def __hash__(self):
		return hash(tuple(self))

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

	tokens = []
	code += u' '
	i = 0
	whitespace = u' \r\n\t'
	while i < len(code):
		while i < len(code) and code[i] in whitespace:
			i += 1
		if i == len(code):
			break
		token = u''
		if code[i] == '"':
			i += 1
			while True:
				if code[i] == '\\':
					i += 1
					if code[i] == 'n':
						token += '\n'
						i += 1
					elif code[i] == 'r':
						token += '\r'
						i += 1
					elif code[i] == 't':
						token += '\t'
						i += 1
					elif code[i] == '"':
						token += '"'
						i += 1
					elif code[i] == '\\':
						token += '\\'
						i += 1
					elif code[i] == 'x':
						i += 1
						token += chr(int(code[i:i+2], 16))
						i += 2
				elif code[i] == '"':
					i += 1
					break
				else:
					token += code[i]
					i += 1
			tokens.append('str-load')
			tokens.append(token)
		else:
			while code[i] not in whitespace:
				token += code[i]
				i += 1
			tokens.append(sub(token))

	return tokens

_language = 'glsl'

class Type(object):
	def __init__(self, name):
		self.name = unicode(name)
		self.attributes = []
		self.array_count = None

	def attribute(self, name):
		self.attributes.append(name)

	def array(self, count):
		self.array_count = count

	def __repr__(self):
		return ' '.join(self.attributes) + (' ' if self.attributes else '') + self.name + ('' if self.array_count is None else '[%i]' % self.array_count)

	def rename(self, tl=False):
		body = Compiler.instance.rename(self.name) + ('' if self.array_count is None or tl else '[%i]' % self.array_count)
		if _language == 'c++':
			return body
		return ' '.join(self.attributes) + (' ' if self.attributes else '') + body

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

	def replace(self, offset, value):
		self.list = self.list[:offset] + [value] + self.list[offset+1:]

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

class Block(object):
	def __init__(self, compiler, atoms, spec):
		self.compiler = compiler
		self.macrolocals = {k : v for k, v in compiler.macrolocals.items()}
		self.localstack = []
		self.atoms = ['__startclosure', self] + list(atoms) + ['__endclosure']
		self.spec = spec
		self.args = None

	def callback(self):
		self.args = ['block_%i_arg_%i' % (self.compiler.rename_i, i) for i in xrange(len(self.cbtype.args))]
		for i, arg in enumerate(self.args):
			self.compiler.locals[arg] = self.cbtype.args[i]
		self.compiler.rename_i += 1
		for arg in self.args:
			self.compiler.rstack.push(('var', arg))

	def callback_type(self, type):
		self.cbtype = type

	def invoke(self):
		self.localstack.append({k : v for k, v in self.compiler.macrolocals.items()})
		self.compiler.macrolocals.update(self.macrolocals)
		self.compiler.blockstack.append(self)

	def end(self):
		self.compiler.macrolocals.update(self.localstack.pop())

class Callback(object):
	def __init__(self, args, ret):
		self.args, self.ret = map(Type, args), Type(ret)
		self.name = self # Hack hack hack hack hack.

	def __repr__(self):
		return 'Callback(%r, %r)' % (self.args, self.ret)

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
	'==' : lambda a, b: a == b,
	'!=' : lambda a, b: a != b,
	'>' : lambda a, b: a > b,
	'<' : lambda a, b: a < b,
	'>=' : lambda a, b: a >= b,
	'<=' : lambda a, b: a <= b,
	'clamp' : None, 
	'sign' : None, 
	'min' : lambda a, b: min(a, b), 
	'max' : lambda a, b: max(a, b), 
	'mod' : lambda a, b: a % b, 
}
glfuncs = dict(
	dot=2, 
	sin=1, 
	abs=1, 
	atan=1, 
	atan2=2, 
	bool=1,
	cos=1, 
	exp=1, 
	sqrt=1, 
	inversesqrt=1, 
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
	step=2, 
	smoothstep=3, 
	ceil=1, 
	floor=1, 
	fract=1, 
	sign=1, 
	texture2D=2, 
	log=1, 
	log2=1, 
	vec2=1, 
	vec3=1, 
	vec4=1, 
	dFdx=1, 
	dFdy=1, 
	fwidth=1, 
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

if '/' in __file__:
	compiler_root = __file__.rsplit('/', 1)[0]
elif '\\' in __file__:
	compiler_root = __file__.rsplit('\\', 1)[0]
else:
	compiler_root = './'

letterElem = dict(x=0, y=1, z=2, w=3, r=0, g=1, b=2, a=3)

class Compiler(object):
	def __init__(self, code, utility, language='glsl', shadertoy=False, minimize=False, entry_point=None):
		global _language
		self.barecode = code
		self.code = utility + code
		Compiler.imports = []
		self.loaded_modules = []
		self.blockstack = []
		self.tempi = 0
		self.language = language
		self.gmp = False
		if self.language == 'c++-gmp':
			self.language, self.gmp = 'c++', True
		_language = self.language
		self.entry_point = entry_point
		self.resetprecision()
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
		self.is_static_frame = False
		self.typetags = {}
		self.wordtypes = {}
		self.externs = {}
		self.words, self.wordtypes, self.macros, self.structs, self.externs = self.parsewords(self.code)
		self.deps = {}
		self.gdeps = {}
		self.exports = []
		self.mainWords = {}

		if self.shadertoy:
			self.words['mainImage'] = self.words['main']
			del self.words['main']
			self.wordtypes['mainImage'] = (('out vec4', 'in vec2'), 'void', ['fragColor', 'fragCoord'])
			del self.wordtypes['main']
			self.macroglobals['gl_FragColor'] = ('var', 'fragColor')
			self.macroglobals['gl_FragCoord'] = ('var', 'fragCoord')
			self.mainWords['mainImage'] = 'mainImage'

		for name, atoms in (self.words.items() + self.macros.items()):
			self.deps[name] = deps = []
			for atom in atoms:
				if not isinstance(atom, unicode):
					continue
				if atom[0] in '&\\/=!*?~':
					atom = atom[1:]
				if (atom in self.words or atom in self.macros) and atom not in deps:
					deps.append(atom)
				elif atom in self.globals:
					if atom not in self.gdeps:
						self.gdeps[atom] = []
					self.gdeps[atom].append(name)
				elif len(atom) > 1 and atom[0] == '$' and atom[1:] in self.globals:
					if atom[1:] not in self.gdeps:
						self.gdeps[atom[1:]] = []
					self.gdeps[atom[1:]].append(name)
		remaining = list(self.words.keys())
		order = []
		while len(remaining):
			rep = []
			for elem in remaining:
				if False in [dep in order or dep in self.macros for dep in self.deps[elem]]:
					rep.append(elem)
				else:
					order.append(elem)
			remaining = rep
		for name in order:
			self.words[name] = self.compile(name, self.words[name])
		
		self.passes, eps = self.parsepasses()
		eps.append('mainImage' if shadertoy else 'main')
		if self.entry_point is not None:
			eps = [self.entry_point]
		for i, ep in enumerate(eps):
			if len(self.words[ep][1]) == 0:
				del eps[i]

		if len(eps) == 0 and len(self.exports) > 0:
			eps.append(self.exports[0])

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
		def emiteffects(effects, out=True):
			accum = ''
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
					if out:
						self.emitnl('\t' * (indentlevel[0] - off) + line)
					else:
						accum += '\t' * (indentlevel[0] - off) + line + '\n'
				else:
					if out:
						self.emitnl('\t' * indentlevel[0] + line + ';')
					else:
						accum += '\t' * indentlevel[0] + line + ';\n'
			return accum

		self.emitted = ''
		indentlevel = [1]
		operators = 'neg + - / * ** < > <= >= == != && ||'.split(' ')
		operator_names = {
			'+' : 'add', 
			'-' : 'sub', 
			'*' : 'mul', 
			'/' : 'div', 
			'**' : 'pow', 
			'<' : 'lt', 
			'>' : 'gt', 
			'<=' : 'lte', 
			'>=' : 'gte', 
			'==' : 'eq', 
			'!=' : 'neq', 
		}
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
			if isinstance(atom, Block):
				indentlevel[0] += 1
				defd.extend(atom.args)
				body = emiteffects(atom.effects, out=False)
				for arg in atom.args:
					defd.remove(arg)
				indentlevel[0] -= 1
				return 'function(%s) {\n%s%s}' % (', '.join(atom.args), body, '\t' * indentlevel[0])
			elif not isinstance(atom, tuple):
				if atom is True:
					return 'true'
				elif atom is False:
					return 'false'
				elif isinstance(atom, float):
					return format_float(atom)
				elif isinstance(atom, unicode):
					if atom in self.externs:
						return self.externs[atom][2]
					return self.rename(atom)
				return unicode(atom)

			if atom[0] == '**' and self.language != 'js':
				if self.language == 'c++':
					prefix = 'sf_'
				else:
					prefix = ''
				return '%spow(%s, %s)' % (prefix, structure(atom[1]), structure(atom[2]))
			elif atom[0] in operators:
				if self.language == 'js':
					if atom[0] == 'neg':
						if self.infertype(atom[1]) in ('float', 'int'):
							return '-%s' % paren(atom[1], 'neg')
						else:
							pass
					else:
						ltype, rtype = self.infertype(atom[1]), self.infertype(atom[2])
						if ltype == rtype == 'float' or ltype == rtype == 'int':
							if atom[0] == '**':
								return 'Math.pow(%s, %s)' % (structure(atom[1]), structure(atom[2]))
							else:
								return '%s %s %s' % (paren(atom[1], atom[0], True), atom[0], paren(atom[2], atom[0], False))
						else:
							return '%s_%s_%s(%s, %s)' % (ltype, operator_names[atom[0]], rtype, structure(atom[1]), structure(atom[2]))
				else:
					if atom[0] == 'neg':
						return '-%s' % paren(atom[1], 'neg')
					else:
						return '%s %s %s' % (paren(atom[1], atom[0], True), atom[0], paren(atom[2], atom[0], False))
			elif atom[0] == '=':
				if atom[2] is None:
					return '%s' % structure(atom[1])
				else:
					if isinstance(atom[2], tuple) and atom[2][0] in ('+', '-', '*', '/'):
						if (
							(atom[2][0] in ('+', '*') and atom[1] in atom[2]) or
							(atom[2][1] == atom[1])
						):
							other = structure([elem for elem in atom[2] if elem != atom[1]][1])
							a, b = self.infertype(atom[1]), self.infertype(other)
							if self.language != 'js' or (a == b and a in ('float', 'int')):
								return '%s %s= %s' % (structure(atom[1]), atom[2][0], other)
					return '%s = %s' % (structure(atom[1]), structure(atom[2]))
			elif atom[0][0] == '.':
				swizzle = atom[0]
				if self.language != 'js' and atom[2]:
					swizzle = '.' + self.rename(atom[0][1:])
				elif self.language == 'c++':
					swizzle = swizzle.replace('r', 'x').replace('g', 'y').replace('b', 'z').replace('a', 'w')
				if not atom[2] and self.language == 'c++' and len(swizzle) > 2:
					val = paren(atom[1], '.')
					return 'vec%i(%s)' % (len(swizzle)-1, ', '.join('%s.%s' % (val, x) for x in swizzle[1:]))
				elif self.language == 'js':
					if atom[2]:
						struct = self.structs[self.infertype(atom[1])]
						elem_i = None
						for i, (ename, _) in enumerate(struct):
							if ename == atom[0][1:]:
								elem_i = i
								break
						assert elem_i is not None
						return '%s[%i]' % (structure(atom[1]), elem_i)
					elif self.infertype(atom[1]) == 'object':
						return '%s.%s' % (paren(atom[1], '.'), atom[0][1:])
					else:
						val = paren(atom[1], '.')
						if len(swizzle) > 2:
							return '[%s]' % (', '.join('%s[%i]' % (val, letterElem[x]) for x in swizzle[1:]))
						else:
							return '%s[%i]' % (val, letterElem[swizzle[1]])
				return '%s%s' % (paren(atom[1], '.'), swizzle)
			elif atom[0] == 'var':
				if atom[1].startswith('gl_') or atom[1] in self.globals or atom[1] in defd:
					return self.rename(atom[1])
				else:
					defd.append(atom[1])
					if self.language == 'js':
						return 'var %s' % self.rename(atom[1])
					else:
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
				vtype = 'val' if self.language == 'js' else 'int'
				return 'for(%s %s = %s; %s < %s; ++%s) {' % (vtype, name, structure(start), name, structure(top), name), True
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
			elif atom[0] == 'print':
				if self.language == 'c++':
					return 'cout << %s << endl' % paren(atom[1])
				elif self.language == 'js':
					return 'console.log(%s)' % structure(atom[1])
				else:
					return ''
			elif atom[0] == 'string-literal':
				assert self.language == 'js' # XXX: C++ support needs to be added.
				# XXX: Need to always double quote, for C++
				str = `atom[1]`
				if str[0] == 'u':
					return str[1:]
				else:
					return str
			elif atom[0] == 'string':
				assert self.language == 'js' # XXX: C++ support needs to be added.
				
				return paren(atom[1]) + '.toString()'
			elif atom[0] == '?:':
				c, a, b = atom[1:]
				return '(%s ? %s : %s)' % (paren(c, '?:'), paren(a, '?:'), paren(b, '?:'))
			elif atom[0] == '[]':
				return '%s[%s]' % (paren(atom[1], '[]'), structure(atom[2]))
			elif atom[0] == 'carray':
				return '{%s}' % (', '.join(structure(elem) for elem in atom[1:]))
			elif self.language == 'js' and atom[0] in ('vec2', 'vec3', 'vec4'):
				if len(atom) == int(atom[0][3]) + 1:
					return '[%s]' % (', '.join(structure(elem) for elem in atom[1:]))
				else:
					return '%s(%s)' % (atom[0], structure(atom[1]))
			elif self.language == 'glsl' and atom[0] in ('vec2', 'vec3', 'vec4'):
				first = atom[1]
				if False not in [x == first for x in atom[2:]]:
					return '%s(%s)' % tuple(map(structure, atom[:2]))
				return '%s(%s)' % (structure(atom[0]), ', '.join(map(structure, atom[1:])))
			elif atom[0] == 'call':
				return '%s(%s)' % (structure(atom[2]), ', '.join(map(structure, atom[3:])))
			elif atom[0] == 'method-call':
				assert atom[2] in self.externs
				name = self.externs[atom[2]][2]
				return '%s%s(%s)' % (paren(atom[1], '.'), name, ', '.join(map(structure, atom[3:])))
			else:
				if self.language in 'c++' and atom[0] in glfuncs:
					prefix = 'sf_'
				else:
					prefix = ''
				if atom[0] in self.externs:
					name = self.externs[atom[0]][2]
				else:
					name = self.rename(atom[0])
				if self.language == 'js' and atom[0] in glfuncs:
					suffix = ''.join('_%s' % self.infertype(arg) for arg in atom[1:])
				else:
					suffix = ''
				return '%s%s%s(%s)' % (prefix, name, suffix, ', '.join(map(structure, atom[1:])))

		if self.shadertoy:
			self.emitnl('/* Compiled with Shaderforth: https://github.com/daeken/Shaderforth')
			self.emitnl(self.barecode.rstrip('\n'))
			self.emitnl('*/')
			self.emitnl()

		if self.language == 'c++':
			if self.gmp:
				self.emitnl('#define GMP')
			self.emitnl('#include "Shaderforth.hpp"')

		if main in self.exports:
			main = '__placeholder__' # Necessary to stop name rewriting from triggering
			required = self.exports
		else:
			required = [main] + self.exports
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

		if self.language == 'js':
			for name, elems in self.structs.items():
				args = ', '.join(self.rename(ename) for ename, type in elems)
				self.emitnl('function %s(%s) {' % (self.rename(name), args))
				self.emitnl('\treturn [%s];' % args)
				self.emitnl('}')
		else:
			for name, elems in self.structs.items():
				self.emitnl('struct %s {' % self.rename(name))
				for ename, type in elems:
					self.emitnl('\t%s %s;' % (type.rename(), self.rename(ename)))
				if self.language == 'c++':
					self.emitnl('\tSF_FUNC %s() {}' % self.rename(name))
					self.emitnl('\tSF_FUNC %s(%s) : %s {}' % (
						self.rename(name), 
						', '.join('%s %s' % (type.rename(), self.rename(ename)) for ename, type in elems), 
						', '.join('%s(%s)' % (self.rename(ename), self.rename(ename)) for ename, type in elems)
					))
				self.emitnl('};')
		for name, type in self.globals.items():
			if name.startswith('gl_') or ((self.shadertoy or self.language == 'c++') and 'uniform' in type.attributes):
				continue
			elif name not in self.gdeps or True not in [x not in dead for x in self.gdeps[name]]:
				continue

			if self.language == 'js':
				self.emitnl('var', self.rename(name) + ';')
			else:
				self.emitnl(type.rename(tl=True), self.rename(name, type) + ';')

		deps = depcopy(self.deps)
		wordorder = []
		while len(deps):
			for name, wdeps in deps.items():
				made = True
				for dname in wdeps:
					if name != dname and dname not in wordorder:
						made = False
						break
				if made:
					del deps[name]
					wordorder.append(name)
					break
		for name in wordorder:
			if name in dead or name not in self.words:
				continue
			locals, effects, localorder, argnames = self.words[name]
			defd = self.wordtypes[name][2]
			effects = self.predeclare(effects, argnames)

			Compiler.compiling = [name]

			if name == main:
				if name in self.mainWords:
					pname = self.mainWords[name]
				else:
					pname = 'main'
			else:
				pname = name

			prefix = ''
			if self.language == 'c++':
				prefix = 'SF_FUNC '
			if self.language == 'js':
				self.emitnl('function %s(%s) {' % (self.rename(name) if pname == name else pname, ', '.join(self.rename(self.wordtypes[name][2][i]) for i in xrange(len(self.wordtypes[name][0])))))
			else:
				self.emitnl('%s%s %s(%s) {' % (prefix, self.rename(self.wordtypes[name][1]) if pname != 'main' else 'void', self.rename(name) if pname == name else pname, ', '.join('%s %s' % (self.rename(type), self.rename(self.wordtypes[name][2][i])) for i, type in enumerate(self.wordtypes[name][0]))))
			emiteffects(effects)
			self.emitnl('}')

		return self.emitted

	def addeffect(self, effect):
		def tag_and_blockify(elem):
			self.typetags[hash((Compiler.compiling[0], elem))] = self.infertype(elem)
			if isinstance(elem, tuple):
				return tuple(map(tag_and_blockify, elem))
			elif isinstance(elem, list):
				return list(map(tag_and_blockify, elem))
			elif isinstance(elem, Block):
				self.atoms.insert(['__start_callback', elem])
				return elem
			else:
				return elem
		if effect[0] == '=' and effect[1] == effect[2]:
			return
		effect = tag_and_blockify(effect)
		self.effects.append(effect)

	def predeclare(self, effects, argnames):
		def vars_referenced(effect):
			if not isinstance(effect, tuple) and not isinstance(effect, list):
				return list()
			if effect[0] == 'var':
				return list([effect[1]])
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
			elif effect[0] == '=' and effect[1][0] == 'var' and effect[1][1] not in argnames:
				decls[-1].append(effect[1][1])
			refs = vars_referenced(effect)
			for ref in refs:
				if ref in inside and ref not in need:
					need.append(ref)
		return list(('=', ('var', var), None) for var in need if var not in declared and var not in decls[0]) + effects
	
	def rename(self, name, type=None):
		if name in glfuncs or name in btypes or name.startswith('gl_'):
			if name == 'atan2':
				return 'atan'
			return name
		elif name in self.globals and ('uniform' in self.globals[name].attributes or 'varying' in self.globals[name].attributes):
			if type is not None and type.array_count is not None:
				return name + '[%i]' % type.array_count
			return name
		elif name in self.renamed:
			return self.renamed[name]
		elif not self.minimize:
			tname = name
			for x in '-><?[]*+/!@#$%^(){}\'':
				if x in name:
					tname = tname.replace(x, '_' + str(self.rename_i))
					self.rename_i += 1
			self.renamed[name] = name = tname.replace('__', '_')
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

	def preprocess(self, code):
		code = Code(code)

		while code.peek() is not None:
			token = code.consume()
			if token == 'import[':
				start = code.i - 1
				fp = code.consume()
				while fp.endswith('\\'):
					fp = fp[:-1] + ' ' + code.consume()
				assert code.consume() == ']'

				if fp not in self.loaded_modules:
					self.loaded_modules.append(fp)
					
					try:
						tfp = compiler_root + '/modules/' + fp + '.sfr'
						subcode = file(str(tfp)).read()
						Compiler.imports.append(tfp)
					except:
						try:
							subcode = file(fp + '.sfr').read()
							Compiler.imports.append(fp + '.sfr')
						except:
							print >>sys.stderr, 'Failed to load import:', `fp`
							subcode = ''
					subcode = self.preprocess(parse(subcode))
				else:
					subcode = []
				code.elems = code.elems[:start] + subcode + code.elems[code.i:]
				code.i = start

		return code.elems

	def parse_arg_type(self, type):
		if type[0] == '(' and type[-1] == ')':
			args = []
			ret = 'void'
			i = 1
			nest = None
			in_ret = False
			while i < len(type)-1:
				if type[i] == '(':
					nest = '('
					i += 1
				elif type[i] == ')':
					if in_ret:
						ret = self.parse_arg_type(nest + ')')
					else:
						args.append(self.parse_arg_type(nest + ')'))
					nest = None
					i += 1
				elif nest is not None:
					nest += type[i]
					i += 1
				elif type[i] == '-' and type[i+1] == '>':
					i += 2
					in_ret = True
					continue
				else:
					start = i
					while i < len(type)-1 and type[i] not in '*-':
						i += 1
					if in_ret:
						ret = type[start:i]
					else:
						args.append(type[start:i])
					if type[i] == '*':
						i += 1
			return Callback(args, ret)

		return type

	def parsewords(self, code):
		def sanitize(name, atoms):
			mspec = macrospec[name]
			if len(atoms) and (len(mspec) or (not len(mspec) and self.has_underscore(atoms))):
				if len(mspec) == 0:
					spec = ['_']
					all_names = spec
					stored = []
				else:
					spec = []
					all_names = []
					specstack = [spec]
					stored = []
					in_ret = False
					for i, atom in enumerate(mspec):
						if atom == ')':
							break
						if atom == '[':
							specstack.append([])
							specstack[-2].append(specstack[-1])
						elif atom == ']':
							specstack.pop()
						elif atom == '->':
							in_ret = True
						elif not in_ret:
							if ':' in atom:
								atom = atom.split(':', 1)[0]
							if atom.startswith('$'):
								stored.append(atom[1:])
								atom = atom[1:]
							specstack[-1].append(atom)
							all_names.append(atom)
				preamble = []
				def recurspec(spec):
					for i, elem in enumerate(spec):
						if i != len(spec) - 1:
							preamble.append(len(spec) - i - 1)
							preamble.append('take')
						if isinstance(elem, list):
							preamble.append('flatten')
							recurspec(elem)
							continue
						if elem in stored:
							preamble.append('=$macro_' + name + '_' + elem)
						else:
							preamble.append('=>macro_' + name + '_' + elem)
				recurspec(spec)
				for i, elem in enumerate(atoms):
					if elem in all_names:
						atoms[i] = 'macro_' + name + '_' + elem
					elif isinstance(elem, unicode) and len(elem) > 1 and elem[0] in '*\\/' and elem[1:] in all_names:
						atoms[i] = elem[0] + 'macro_' + name + '_' + elem[1:]
				macros[name] = preamble + atoms

		parsed = Code(self.preprocess(parse(code)))
		parseloc = 0
		words, macros, externs = {'main': []}, {}, {}
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

			if token == ':' or token == ':extern':
				ttoken = token
				modstack.append(cur)
				name = parsed.consume()
				if token == ':extern':
					cur = externs[name] = []
				else:
					cur = words[name] = []

				if parsed.peek() != '(':
					wordtypes[name] = (), 'void', []
				else:
					parsed.consume()
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
					args = map(self.parse_arg_type, args)
					parsed.consume()
					assert len([_ for _ in argnames if _ != None]) == 0 or None not in argnames
					if None in argnames:
						argnames = ['arg_%i' % i for i in xrange(len(argnames))]
					if ttoken == ':extern':
						if parsed.peek() != ';':
							repl = parsed.consume()
						else:
							repl = self.rename(name)
						externs[name] = args, ret, repl
					else:
						wordtypes[name] = tuple(args), ret, argnames
			elif token == ':m':
				modstack.append(cur)
				name = parsed.consume()
				cur = macros[name] = ['__push_macro', 'macro:' + name]
				macrospec[name] = []
				in_macro = name
				cdepth = 0
				if parsed.peek() == '(':
					parsed.consume()
					while True:
						token = parsed.consume()
						if token == '(':
							cdepth += 1
						elif token == ')':
							if cdepth == 0:
								break
							cdepth -= 1
						else:
							macrospec[name].append(token)
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
					cur.append('__pop_macro')
					sanitize(in_macro, cur)
					in_macro = None
				cur = modstack.pop()
			else:
				cur.append(token)

		for name, tokens in words.items():
			words[name] = self.expandmacros(name, tokens, macros)

		self.words = {}
		self.macros = {}
		self.macroglobals = {}
		self.structs = {}
		locals, effects, localorder, argnames = self.compile('__globals', globals, pre=True)
		self.macroglobals = self.macrolocals
		self.globals.update(locals)
		macros['__globals_dep'] = globals

		def subword(name):
			return lambda self: self.rstack.push(tuple([name] + self.rstack.pop()[1:]))
		sdefs = {}
		for name, atoms in structs.items():
			locals, effects, localorder, argnames = self.compile('__' + name, atoms, pre=True)
			sdefs[name] = [(ename, locals[ename]) for ename in localorder]
			word(name)(subword(name))
			gltypes[name] = name

		return words, wordtypes, macros, sdefs, externs

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
		locals, effects, localorder, argnames = self.compile('__passes', self.passes, pre=True)
		passes = []
		eps = []
		for effect in effects:
			assert effect[0] == '='
			if effect[2][0] == 'var':
				passes.append((effect[1][1], effect[2][1]))
			else:
				if effect[1][1] == 'sound-pass':
					self.mainWords[effect[2]] = 'mainSound'
				eps.append(effect[2])
				passes.append((effect[1][1], effect[2]))
		return passes, eps

	def fold_constants(self, op, operands):
		def eligible(val):
			return (
				isinstance(val, float) or 
				isinstance(val, int) or 
				isinstance(val, bool) or 
				isinstance(val, Block) or 
				(isinstance(val, list) and False not in map(eligible, val[1:]))
			)

		def fold(a, b):
			self.resetprecision()
			if isinstance(a, list):
				if isinstance(b, list):
					assert len(a) == len(b)
					return list(['array'] + map(lambda i: self.fold_constants(op, [a[i], b[i]]), xrange(1, len(a))))
				elif False not in map(eligible, a[1 if len(a) > 0 and a[0] == 'array' else 0:]):
					return list(['array'] + map(lambda x: foldops[op](x, b), a[1:]))
				else:
					return tuple([op, a, b])
			elif isinstance(b, list):
				if False not in map(eligible, b[1 if len(b) > 0 and b[0] == 'array' else 0:]):
					return list(['array'] + map(lambda x: foldops[op](a, x), b[1:]))
				else:
					return tuple([op, a, b])
			else:
				return foldops[op](a, b)
		def unvec(x):
			if isinstance(x, tuple) and x[0].startswith(u'vec'):
				if eligible(x[1]):
					return x[1]
			elif isinstance(x, list) and x[0] == 'array':
				first = x[1]
				if False not in [y == first for y in x[2:]]:
					return first
			return x

		def retype(x, type):
			if self.infertype(x) != type:
				return (type, x)
			else:
				return x

		if foldops[op] and False not in map(eligible, operands):
			return reduce(fold, operands)

		if op == '*':
			type = self.infertype(tuple([op] + operands))
			operands = map(unvec, operands)
			if 0 in operands:
				return retype(float(0), type)
			elif 1 in operands:
				operands = [val for val in operands if val != 1]
				if len(operands) == 0:
					return retype(float(1), type)
				elif len(operands) == 1:
					return retype(operands[0], type)
		elif op == '/':
			type = self.infertype(tuple([op] + operands))
			operands = map(unvec, operands)
			while len(operands) and operands[-1] == 1:
				operands = operands[:-1]
			if len(operands) == 0:
				return retype(float(0), type)
			elif len(operands) == 1:
				return retype(operands[0], type)
		elif op == '**':
			assert len(operands) == 2
			if operands[0] == 0:
				return float(0)
			elif operands[0] == 1 or operands[1] == 0:
				return float(1)
			elif operands[1] == 1:
				return operands[0]
		elif op == '+':
			type = self.infertype(tuple([op] + operands))
			operands = map(unvec, operands)
			operands = [val for val in operands if val != 0]
			if len(operands) == 0:
				return retype(float(0), type)
			elif len(operands) == 1:
				return retype(operands[0], type)
		elif op == '-':
			type = self.infertype(tuple([op] + operands))
			operands = map(unvec, operands)
			while len(operands) and operands[-1] == 0:
				operands = operands[:-1]
			if len(operands) == 0:
				return retype(float(0), type)
			elif len(operands) == 1:
				return retype(operands[0], type)
		elif op == 'clamp' and False not in map(eligible, operands):
			val, a, b = operands
			if isinstance(val, list):
				return list(['array'] + [min(max(elem, a), b) for elem in val[1:]])
			else:
				return min(max(val, a), b)
		elif op == 'sign' and False not in map(eligible, operands):
			sign = lambda x: (0 if x == 0 else -1) if x <= 0 else 1
			val, = operands
			if isinstance(val, list):
				return list(['array'] + [sign for elem in val[1:]])
			else:
				return sign(val)

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

		if eligible(elem, top=True):
			for swizzle in swizzles:
				if len(swizzle) == 1:
					self.rstack.push(elem[letterElem[swizzle] + 1])
				else:
					self.rstack.push(list(['array'] + [elem[letterElem[char] + 1] for char in swizzle]))
		elif isinstance(elem, tuple) and elem[0][0] == '.' and self.infertype(elem[1]).startswith('vec'):
			reorder = elem[0][1:]
			for swizzle in swizzles:
				self.rstack.push(('.' + ''.join(reorder[letterElem[c]] for c in swizzle), elem[1], False))
		else:
			for swizzle in swizzles:
				self.rstack.push(('.' + swizzle, elem, False))

	def compile(self, name, atoms, pre=False):
		Compiler.compiling = [name]
		self.atoms = Code(atoms)
		self.rstack = Stack()
		self.sstack = Stack()
		self.locals = {}
		self.localorder = []
		self.macrolocals = {}
		self.macrolocals.update(self.macroglobals)
		self.effects = list()
		if not pre:
			self.argcount = len(self.wordtypes[name][0])+1
			argtypes = self.wordtypes[name][0]
			self.argnames = self.wordtypes[name][2]
			self.argtypes = dict((self.argnames[i], type) for i, type in enumerate(argtypes))
			for name, type in self.argtypes.items():
				if isinstance(type, Callback):
					self.locals[name] = type
				else:
					self.locals[name] = Type(type)
		else:
			self.argnames = []

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
				self.atoms.insert(self.expandmacros(None, ['{', token[1:], '}'], self.macros))
			elif len(token) > 1 and token[0] == '$' and token[1] != '[':
				self.rstack.push(('var', token[1:]))
			elif len(token) > 1 and token[0] == '*' and token != '**':
				name = token[1:]
				if name in self.macrolocals:
					self.rstack.push(self.macrolocals[name])
					self.call()
				elif name in self.locals:
					self.rstack.push(('var', name))
					self.call(self.locals[name])
				elif name in self.globals:
					self.rstack.push(('var', name))
					self.call(self.globals[name])
				else:
					assert False
			elif len(token) > 4 and token[:2] == '##':
				self.rgb(token[2:])
			elif len(token) > 2 and token[:2] == '=>':
				self.macroassign(token[2:])
			elif len(token) > 2 and token[:2] == '=$':
				self.macrocopy(token[2:])
			elif len(token) > 1 and token[0] == '=':
				self.assign(token[1:])
			elif token == '=':
				var = self.rstack.pop()
				value = self.rstack.pop()
				self.addeffect(('=', var, value))
			elif len(token) > 1 and token[0] == '.':
				if self.language == 'c++' or '.' in token[1:]:
					elem = self.ensure_stored(pop=True)
				else:
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
			elif len(token) > 1 and token[0] == '?':
				if token == '?{':
					self.filter(self.block())
				else:
					self.filter(token[1:])
			elif len(token) > 3 and token.startswith('$['):
				self.range(token[2:-1].split(':'))
			elif len(token) > 1 and token[0] == '!' and token != '!=':
				self.dup()
				self.rstack.push(token[1:])
				self.call()
			elif len(token) > 1 and token[0] == '~':
				if token == '~{':
					self.condexec(self.block())
				else:
					self.condexec(token[1:])
			elif token in self.macrolocals:
				self.rstack.push(self.macrolocals[token])
			elif token in self.globals or token in self.locals:
				self.rstack.push(('var', token))
			elif token in self.words:
				for i, type in enumerate(self.wordtypes[token][0]):
					arg_i = len(self.wordtypes[token][0]) - i - 1
					arg = self.rstack.retrieve(arg_i)
					if arg in self.words or arg in self.externs:
						pass
					elif isinstance(type, Callback):
						if not isinstance(arg, Block):
							arg = self.blockify(arg)
							self.rstack.replace(i, arg)
						arg.callback_type(type)
				elem = tuple([token] + [self.rstack.pop() for i in xrange(len(self.wordtypes[token][0]))][::-1])
				if self.wordtypes[token][1] == 'void':
					self.addeffect(elem)
				else:
					self.rstack.push(elem)
			elif token in self.externs:
				obj = None
				if self.externs[token][2][0] == '.':
					obj = self.rstack.pop()
				for i, type in enumerate(self.externs[token][0]):
					arg_i = len(self.externs[token][0]) - i - 1
					arg = self.rstack.retrieve(arg_i)
					if arg in self.words or arg in self.externs:
						pass
					elif isinstance(type, Callback):
						if not isinstance(arg, Block):
							arg = self.blockify(arg)
							self.rstack.replace(i, arg)
						arg.callback_type(type)
				if obj is not None:
					elem = tuple(['method-call', obj, token] + [self.rstack.pop() for i in xrange(len(self.externs[token][0]))][::-1])
				else:
					elem = tuple([token] + [self.rstack.pop() for i in xrange(len(self.externs[token][0]))][::-1])
				if self.externs[token][1] == 'void':
					self.addeffect(elem)
				else:
					self.rstack.push(elem)
			elif token == '[':
				self.sstack.push(self.rstack)
				self.rstack = Stack()
			elif token == ']':
				temp = self.rstack.list
				self.rstack = self.sstack.pop()
				self.rstack.push(list(['array'] + temp))
			elif token == ']m':
				temp = self.rstack.list
				self.rstack = self.sstack.pop()
				self.rstack.push(list(['array'] + temp))
				self.amat()
			elif token == '{':
				self.rstack.push(self.block())
			elif token == 'true':
				self.rstack.push(True)
			elif token == 'false':
				self.rstack.push(False)
			else:
				print >>sys.stderr, 'unknown token', token, self.rstack
				raise Exception('Unknown token')

		assert len(self.rstack) <= 1
		if len(self.rstack) == 1:
			self.addeffect(('return', self.rstack.pop()))

		self.effects = self.vectorize(self.effects)
		return self.locals, self.effects, self.localorder, self.argnames

	def vectorize(self, obj):
		def flatten_arr(arr):
			if not isinstance(arr, list) or len(arr) < 2 or arr[0] != 'array':
				return self.vectorize(arr)

			narr = list(['array'])
			for i, val in enumerate(arr[1:]):
				if isinstance(val, list):
					if len(val) > 1 and val[0] == 'array':
						narr += map(self.vectorize, val[1:])
					else:
						narr += map(self.vectorize, val)
				else:
					narr.append(self.vectorize(val))
			return narr

		if isinstance(obj, list) and len(obj) > 0 and obj[0] == 'array':
			self.rstack.push(flatten_arr(obj))
			self.avec()
			return self.rstack.pop()
		elif isinstance(obj, tuple):
			return tuple(map(self.vectorize, obj))
		elif isinstance(obj, list):
			return list(map(self.vectorize, obj))
		else:
			return obj

	def resetprecision(self):
		if self.language == 'c++':
			getcontext().prec = 25
		else:
			getcontext().prec = 5

	def has_underscore(self, atoms):
		prefix = '&\\/?*'
		return '_' in atoms or True in [pfx + '_' in atoms for pfx in prefix]

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
			elif cdepth == 0 and token in ('{', '\\{', '/{', '?{', '~{'):
				depth += 1
			elif cdepth == 0 and token == '}':
				depth -= 1
				if depth == 0:
					break
		atoms = atoms[:-1]
		spec = []
		if len(atoms) and (atoms[0] == '(' or (atoms[0] != '(' and self.has_underscore(atoms))):
			if atoms[0] != '(' and self.has_underscore(atoms):
				spec = ['_']
				all_names = spec
				stored = []
			else:
				spec = []
				all_names = []
				specstack = [spec]
				stored = []
				for i, atom in enumerate(atoms[1:]):
					if atom == ')':
						break
					if atom == '[':
						specstack.append([])
						specstack[-2].append(specstack[-1])
					elif atom == ']':
						specstack.pop()
					else:
						if atom.startswith('$'):
							stored.append(atom[1:])
							atom = atom[1:]
						specstack[-1].append(atom)
						all_names.append(atom)
				atoms = atoms[i+2:]
			name = self.tempname()
			preamble = []
			def recurspec(spec):
				for i, elem in enumerate(spec):
					if i != len(spec) - 1:
						preamble.append(len(spec) - i - 1)
						preamble.append('take')
					if isinstance(elem, list):
						preamble.append('flatten')
						recurspec(elem)
						continue
					if elem in stored:
						preamble.append('=$macro_' + name + '_' + elem)
					else:
						preamble.append('=>macro_' + name + '_' + elem)
			recurspec(spec)
			for i, elem in enumerate(atoms):
				if elem in all_names:
					atoms[i] = 'macro_' + name + '_' + elem
				elif isinstance(elem, unicode) and len(elem) > 1 and elem[0] in '*\\/?~!' and elem[1:] in all_names:
					atoms[i] = elem[0] + 'macro_' + name + '_' + elem[1:]
			atoms = preamble + atoms

		return Block(self, atoms, spec)

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
		if name in self.macroglobals:
			if isinstance(self.macroglobals[name], tuple) and self.macroglobals[name][0] == 'var':
				name = self.macroglobals[name][1]

		swizzle = False
		if name[0] == '.':
			parent = self.rstack.pop()
			elem = (name, parent, self.infertype(parent) in self.structs)
			swizzle = True
		else:
			elem = ('var', name)

		if isinstance(self.rstack.top(), Type):
			type = self.rstack.pop()
			if not swizzle:
				self.locals[name] = type
				if name not in self.localorder:
					self.localorder.append(name)
			self.addeffect(('=', elem, None))
		else:
			value = self.rstack.pop()
			if not swizzle and name not in self.locals and name not in self.globals:
				self.locals[name] = Type(self.infertype(value))
				self.localorder.append(name)
			self.addeffect(('=', elem, value))

	def map(self, name):
		tlist = self.rstack.pop()
		if tlist[0] != 'array':
			self.rstack.push(tlist)
			self.veca()
			tlist = self.rstack.pop()
		
		block = self.blockify(name)
		tatoms = []
		tatoms.append(u'[')
		for i, val in enumerate(tlist[1:]):
			tname = self.tempname()
			self.macrolocals[tname] = val
			tatoms.append(tname)
			tatoms += block.atoms
		tatoms.append(u']')
		self.atoms.insert(tatoms)

	@word('enumerate')
	def enumerate(self):
		tlist = self.rstack.pop()
		if tlist[0] != 'array':
			self.rstack.push(tlist)
			self.veca()
			tlist = self.rstack.pop()
		
		tlist = list(['array'] + [['array', float(i), e] for i, e in enumerate(tlist[1:])])
		self.rstack.push(tlist)

	def reduce(self, name):
		tlist = self.rstack.pop()
		if tlist[0] != 'array':
			self.rstack.push(tlist)
			self.veca()
			tlist = self.rstack.pop()

		block = self.blockify(name)
		tatoms = []
		for i, val in enumerate(tlist[1:]):
			tname = self.tempname()
			self.macrolocals[tname] = val
			tatoms.append(tname)
			if i != 0:
				tatoms += block.atoms
		self.atoms.insert(tatoms)

	def filter(self, name):
		block = self.blockify(name)
		tlist = self.rstack.pop()
		assert tlist[0] == 'array'

		tatoms = [u'[']
		for elem in tlist[1:]:
			tatoms += [elem, u'dup'] + block.atoms + [u'not', u'~drop']
		tatoms.append(u']')

		self.atoms.insert(tatoms)

	def macroassign(self, name):
		self.macrolocals[name] = self.rstack.pop()

	def macrocopy(self, name):
		val = self.rstack.pop()

		if isinstance(val, float) or isinstance(val, int):
			inline = True
		elif val[0] == 'var' or val[0] == 'arg':
			inline = True
		elif val[0][0] == '.' and val[1][0] == 'var':
			inline = True
		else:
			inline = False

		if inline:
			self.macrolocals[name] = val
		else:
			self.rstack.push(val)
			self.assign(name)

	def infertype(self, expr):
		if isinstance(expr, tuple) or isinstance(expr, list):
			if hash((Compiler.compiling[0], expr)) in self.typetags:
				return self.typetags[hash((Compiler.compiling[0], expr))]
			if expr[0] == 'call':
				return unicode(expr[1].ret)
			elif expr[0] == 'var':
				name = expr[1]
				if name in self.macrolocals and isinstance(self.macrolocals[name], list) and self.macrolocals[name][0] == 'var':
					name = self.macrolocals[name][1]
				if name in self.globals:
					obj = self.globals[name].name
				elif name in self.locals:
					obj = self.locals[name].name
				else:
					assert False
				if isinstance(obj, Callback):
					return obj.ret.name
				else:
					return obj
			elif expr[0] == 'arg':
				obj = self.argtypes[expr[1]]
				if isinstance(obj, Callback):
					return obj.ret.name
				else:
					return obj
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
			elif expr[0] == 'carray':
				return 'const ' + self.infertype(expr[1]) + '[' + str(len(expr)-1) + ']'
			elif expr[0] == '[]':
				return self.infertype(expr[1]).split('const ', 1)[-1].split('[', 1)[0]
			elif expr[0] in gltypes:
				return gltypes[expr[0]]
			elif expr[0] in self.wordtypes:
				return self.wordtypes[expr[0]][1]
			elif expr[0] in self.externs:
				return self.externs[expr[0]][1]
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
			self.addeffect(('=', temp, top))
			if not pop:
				self.rstack.push(temp)
			return temp

	@word('store')
	def store(self):
		self.ensure_stored()

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
	@word('attribute')
	def attribute(self):
		self.rstack.top().attribute('attribute')

	@word('(')
	def nullparen_open(self):
		self.eatcomment()

	@word('flatten')
	def flatten(self, deep=False):
		arr = self.rstack.top()
		if not isinstance(arr, list) or len(arr) == 0 or arr[0] != 'array':
			if self.infertype(arr) in self.structs:
				arr = self.ensure_stored(pop=True)
				struct = self.structs[self.infertype(arr)]
				self.rstack.push(list(['array'] + [('.' + elem[0], arr, True) for elem in struct]))
			elif not self.infertype(arr).startswith('vec'):
				return
			else:
				self.veca()
		for elem in self.rstack.pop()[1:]:
			self.rstack.push(elem)
			if deep:
				self.flatten(deep=True)

	@word('flatten-deep')
	def flatten_deep(self):
		self.flatten(deep=True)

	def rgb(self, color):
		if len(color) == 3:
			r, g, b = list(color)
			color = '%s%s%s%s%s%s' % (r, r, g, g, b, b)
		assert len(color) == 6
		self.resetprecision()
		r, g, b = [float(int(color[i:i+2], 16)) / 255 for i in xrange(0, 6, 2)]
		self.rstack.push(list(['array', r, g, b]))

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

	def veca(self):
		vec = self.ensure_stored(pop=True)
		type = self.infertype(vec)
		assert 'vec' in type
		size = int(type[type.find('vec')+3:])
		self.rstack.push(list(['array'] + [('.' + 'xyzw'[i], vec, False) for i in xrange(size)]))

	@word('amat')
	def amat(self):
		tlist = self.rstack.pop()
		assert tlist[0] == 'array'
		tlist = tlist[1:]
		if len(tlist) in (2, 4):
			size = 2
		elif len(tlist) in (3, 9):
			size = 3
		elif len(tlist) in (4, 16):
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
		nstack = [names]
		while True:
			token = self.atoms.consume()
			if token == '[':
				nstack.append([])
				nstack[-2].append(nstack[-1])
			elif token == ']':
				nstack.pop()
				if len(nstack) == 0:
					break
			else:
				nstack[-1].append(token)
		arr = self.rstack.pop()

		def assign(arr, names):
			for i, name in enumerate(names):
				if isinstance(name, list):
					assign(arr[i+1], name)
				else:
					self.rstack.push(arr[i+1])
					self.macroassign(name)

		assign(arr, names)

	@word('call')
	def call(self, type=None):
		name = self.rstack.pop()
		if isinstance(name, tuple):
			assert isinstance(type, Callback)
			args = tuple(self.rstack.pop() for i in xrange(len(type.args)))[::-1]
			self.rstack.push(('call', type, name) + args)
			return

		block = self.blockify(name)
		self.atoms.insert(block.atoms)

	@word('__startclosure', 1)
	def startclosure(self, block):
		block.invoke()

	@word('__endclosure')
	def endclosure(self):
		self.blockstack.pop().end()

	def blockify(self, atom):
		if isinstance(atom, Block):
			return atom
		elif isinstance(atom, list):
			return Block(self, atom, [])

		if atom in self.macrolocals:
			atom = self.macrolocals[atom]
			if isinstance(atom, Block):
				return atom

		if atom in self.macros:
			return Block(self, self.macros[atom], [])
		return Block(self, [atom], [])

	@word('times')
	def times(self):
		self.int()
		count = self.rstack.pop()
		block = self.blockify(self.rstack.pop())
		var = self.tempname()

		self.addeffect(('for', var, 0, count))
		self.rstack.push('__term__')
		self.rstack.push(('var', var))
		self.atoms.insert(block.atoms + ['__endblock'])
		self.locals[var] = Type('int')

	@word('mtimes')
	def mtimes(self):
		count = self.rstack.pop()
		block = self.blockify(self.rstack.pop())

		for i in xrange(int(count)):
			self.atoms.insert([i] + block.atoms)

	def condexec(self, name):
		def all_true(cond):
			if isinstance(cond, list):
				assert [elem in (True, False) for elem in cond[1:]]
				return False not in map(all_true, cond[1:])
			if cond in (True, False):
				return cond
			return True
		block = self.blockify(name)
		cond = self.rstack.pop()
		if all_true(cond):
			self.atoms.insert(block.atoms)

	@word('cif')
	def cif(self):
		def all_true(cond):
			if isinstance(cond, list):
				assert [elem in (True, False) for elem in cond[1:]]
				return False not in map(all_true, cond[1:])
			if cond in (True, False):
				return cond
			return True
		cond = self.rstack.pop()
		else_ = self.blockify(self.rstack.pop())
		if_ = self.blockify(self.rstack.pop())
		if all_true(cond):
			self.atoms.insert(if_.atoms)
		else:
			self.atoms.insert(else_.atoms)

	@word('when')
	def when(self):
		cond = self.rstack.pop()
		block = self.blockify(self.rstack.pop())

		self.addeffect(('if', cond))
		self.rstack.push('__term__')
		self.atoms.insert(block.atoms + ['__endblock'])

	@word('if')
	def if_(self):
		cond = self.rstack.pop()
		else_ = self.blockify(self.rstack.pop())
		if_ = self.blockify(self.rstack.pop())

		self.addeffect(('if', cond))
		self.rstack.push(else_.atoms)
		self.rstack.push('__term__')
		self.atoms.insert(if_.atoms + ['__else'])

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
		self.addeffect(('else', ))
		else_ = self.rstack.pop()
		self.rstack.push('__term__')
		self.atoms.insert(else_ + ass + ['__endblock'] + expand)

	@word('__endblock')
	def endblock(self):
		self.addeffect(('endblock', ))
		while self.rstack.pop() != '__term__':
			pass

	@word('break')
	def break_(self):
		self.addeffect(('break', ))

	@word('continue')
	def continue_(self):
		self.addeffect(('continue', ))

	@word('select')
	def select(self):
		cond = self.rstack.pop()
		b = self.rstack.pop()
		a = self.rstack.pop()

		self.rstack.push(('?:', cond, a, b))

	@word('return')
	def return_(self):
		self.addeffect(('return', self.rstack.pop()))

	@word('return-nil')
	def return_nil(self):
		self.addeffect(('return', ))

	@word('printdbg')
	def printdbg(self):
		pprint.pprint(self.rstack.top())

	@word('printstack')
	def printstack(self):
		pprint.pprint(self.rstack.list)

	@word('print')
	def print_(self):
		if self.language in ('c++', 'js'):
			self.dup()
			self.addeffect(('print', self.rstack.pop()))

	@word('switch')
	def switch(self):
		val = self.ensure_stored(pop=True)
		arr = self.rstack.pop()
		assert arr[0] == 'array'
		elems = list(['array'])
		for i in xrange(1, len(arr), 2):
			if i == len(arr) - 1:
				elems.append(arr[i])
			else:
				elems.append((u'==', val, arr[i]))
				elems.append(arr[i+1])
		
		self.rstack.push(elems)
		self.cond()

	@word('cond')
	def cond(self):
		arr = self.rstack.pop()
		assert arr[0] == 'array'

		(cond, block), arr = arr[1:3], arr[3:]
		block = self.blockify(block)

		self.addeffect(('if', cond))
		self.rstack.push(arr)
		self.rstack.push(None)
		self.rstack.push('__term__')
		self.atoms.insert(block.atoms + ['__cond'])

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
			self.addeffect(('endblock', ))
			vars.reverse()
			self.atoms.insert(vars)
			return
		elif len(arr) == 1:
			block = arr[0]
			arr = []
			self.addeffect(('else', ))
		else:
			(cond, block), arr = arr[:2], arr[2:]
			self.addeffect(('elif', cond))

		block = self.blockify(block)
		self.rstack.push(arr)
		self.rstack.push(vars)
		self.rstack.push('__term__')
		self.atoms.insert(block.atoms + ['__cond'])

	@word('and')
	def and_(self):
		b, a = self.rstack.pop(), self.rstack.pop()
		if isinstance(a, bool) and isinstance(b, bool):
			self.rstack.push(a and b)
		else:
			self.rstack.push(('&&', a, b))

	@word('or')
	def or_(self):
		b, a = self.rstack.pop(), self.rstack.pop()
		if isinstance(a, bool) and isinstance(b, bool):
			self.rstack.push(a or b)
		else:
			self.rstack.push(('||', a, b))

	@word('not')
	def not_(self):
		def foldable(cond):
			if isinstance(cond, list):
				return False not in [elem in (True, False) for elem in cond[1:]]
			return cond in (True, False)
		def not_all(cond):
			if isinstance(cond, list):
				return list(['array'] + map(not_all, cond[1:]))
			return not cond
		val = self.rstack.pop()
		if foldable(val):
			self.rstack.push(not_all(val))
		else:
			self.rstack.push(('!', val))

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
		if isinstance(count, list):
			self.rstack.push(tuple(['carray'] + count[1:]))
		else:
			type = self.rstack.top()
			type.array(count)

	@word('[]')
	def index(self):
		self.int()
		index = self.rstack.pop()
		arr = self.rstack.pop()
		if isinstance(arr, list) and arr and arr[0] == 'array' and isinstance(index, int):
			self.rstack.push(arr[index+1])
		else:
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
		elif self.infertype(val) == 'float':
			self.rstack.push(val)
		else:
			self.rstack.push(('float', val))

	@word('int')
	def int(self):
		val = self.rstack.pop()
		if isinstance(val, float) or isinstance(val, int):
			self.rstack.push(int(val))
		elif self.infertype(val) == 'int':
			self.rstack.push(val)
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

	@word('slider')
	def slider(self):
		steps = int(self.rstack.pop())
		val = old_float(self.rstack.pop())
		max = old_float(self.rstack.pop())
		min = old_float(self.rstack.pop())
		var = self.rstack.pop()
		self.options.append((var, 'slider', (min, max, val, steps)))

	@word('recur')
	def recur(self):
		depth = self.rstack.pop()
		_else = self.blockify(self.rstack.pop())
		_if = self.blockify(self.rstack.pop())

		if depth == 0:
			self.atoms.insert([depth] + self.expandmacros(None, _else.atoms, self.macros))
		else:
			atoms = [depth] + self.expandmacros(None, _if.atoms, self.macros)
			for i, atom in enumerate(atoms):
				if atom == 'recur':
					atoms[i-1] = depth - 1
			self.atoms.insert(atoms)

	def range(self, elems):
		incl = True in ['+' in elem for elem in elems]
		elems = map(float, elems)
		val = list(['array'])
		if len(elems) == 1:
			start, max, step = 0., elems[0], float(1.)
		elif len(elems) == 2:
			(start, max), step = elems, float(1.)
		else:
			start, max, step = elems

		while (not incl and start < max) or (incl and start <= max):
			val.append(start)
			start += step

		self.rstack.push(val)

	@word('range')
	def range_word(self):
		self.int()
		top = self.rstack.pop()
		self.rstack.push(list(['array'] + list(range(0, top))))

	@word('upto')
	def upto(self):
		top = self.rstack.pop()
		self.rstack.push(list(['array'] + list(map(float, range(int(top))))))

	@word('static-frame')
	def static_frame(self):
		self.is_static_frame = True

	@word('str-load', 1)
	def str_load(self, str):
		self.rstack.push(('string-literal', str))

	@word('string')
	def string(self):
		self.rstack.push(('string', self.rstack.pop()))

	@word('__start_callback', 1)
	def start_callback(self, block):
		prev_effects = self.effects
		self.effects = list()
		self.rstack.push('__callback__term__')
		block.callback()
		self.atoms.insert(block.atoms + ['__end_callback', block, prev_effects])

	@word('__end_callback', 2)
	def end_callback(self, effects, block):
		retval = self.rstack.pop()
		if retval != '__callback__term__':
			self.addeffect(('return', retval))
			assert self.rstack.pop() == '__callback__term__'
		block.effects = self.vectorize(self.effects)
		self.effects = effects

	@word('export')
	def export(self):
		func = self.rstack.pop()
		if func not in self.exports:
			self.exports.append(func)

	@word('__push_macro', 1)
	def __push_macro(self, name):
		print '-->', name
		Compiler.compiling.append(name)

	@word('__pop_macro')
	def __pop_macro(self):
		print '<--', Compiler.compiling.pop()

def main():
	import argparse, os

	parser = argparse.ArgumentParser(description='Shaderforth compiler')
	parser.add_argument('filename', metavar='filename.sfr', type=unicode,
						help='a Shaderforth file')
	parser.add_argument('--shadertoy', action='store_true', 
						help='enable Shadertoy mode')
	parser.add_argument('--minimize', action='store_true', 
						help='minimize GLSL output')
	parser.add_argument('--language', choices=['glsl', 'c++', 'c++-gmp', 'js'], default='glsl', 
						help='language output')

	args = parser.parse_args()
	utility = file(os.path.dirname(os.path.realpath(__file__)) + '/utility.sfr', 'r').read().decode('utf-8')
	compiler = Compiler(
		file(args.filename, 'r').read().decode('utf-8'), 
		utility, 
		language=args.language, 
		shadertoy=args.shadertoy, 
		minimize=args.minimize)
	for name, code in compiler.outcode.items():
		print >>sys.stderr, '// Shader', name
		print code
		print >>sys.stderr

if __name__=='__main__':
	main()
