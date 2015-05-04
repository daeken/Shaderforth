import coffeescript, json, os, random, sys
from cStringIO import StringIO
from flask import Flask
sys.path = [os.path.abspath(__file__)[:-14]] + sys.path
from compiler import Compiler
app = Flask(__name__)
app.debug = True
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

last_imports = []

def compile():
	global last_imports
	old = sys.stdout
	olde = sys.stderr
	sys.stdout = StringIO()
	sys.stderr = StringIO()
	success = True
	utility = file('utility.sfr', 'r').read().decode('utf-8')
	try:
		compiler = Compiler(file(fn, 'r').read().decode('utf-8'), utility, False, False)
	except:
		import traceback
		success = False
		print >>sys.stderr, 'Error while compiling word %r' % Compiler.compiling
		traceback.print_exc()
	messages = sys.stdout.getvalue()
	errors = sys.stderr.getvalue()
	sys.stdout = old
	sys.stderr = olde
	if success:
		shaders = compiler.outcode
		globals = dict((k, str(v)) for k, v in compiler.globals.items())
		passes = compiler.passes
		dimensions = compiler.dimensions
		options = compiler.options
		last_imports = compiler.imports
		is_static = compiler.is_static_frame
	else:
		shaders = dict(main='void main() { gl_FragColor = vec4(1., 0., 0., 1.); }')
		globals = {}
		passes = []
		dimensions = {}
		options = []
		is_static = True
	return success, shaders, globals, passes, dimensions, is_static, options, messages, errors

@app.route('/')
def index():
	return app.send_static_file('index.html')

rand_push = random.randrange(1, 100)

def getmtime_wrap(fn):
	try:
		return os.path.getmtime(fn)
	except:
		return 0

@app.route('/refresh/<int:time>')
def refresh(time=None):
	mtime = int(max(map(getmtime_wrap, [fn, 'utility.sfr', 'compiler.py', 'live/serve.py'] + last_imports))) + rand_push
	if time == mtime:
		return 'null'
	return json.dumps([mtime] + list(compile()))

@app.route('/<name>.coffee')
def coffee(name=None):
	try:
		return coffeescript.compile_file('live/%s.coffee' % name, bare=True)
	except Exception, e:
		print e.message
		return "$(document).ready(function() { $('#errors').text('Compilation error in \"' + %r + '\": ' + %r) })" % (str(name), str(e.message))

if __name__=='__main__':
	fn = sys.argv[1]
	app.run(host='0.0.0.0')