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

def compile():
	old = sys.stdout
	olde = sys.stderr
	sys.stdout = StringIO()
	# sys.stderr = sys.stdout
	success = True
	utility = file('utility.sfr', 'r').read().decode('utf-8')
	try:
		compiler = Compiler(file(fn, 'r').read().decode('utf-8'), utility, False, False)
	except:
		import traceback
		success = False
		print 'Error while compiling word %r' % Compiler.compiling
		traceback.print_exc()
	messages = sys.stdout.getvalue()
	sys.stdout = old
	#sys.stderr = olde
	if success:
		shaders = compiler.outcode
		globals = dict((k, str(v)) for k, v in compiler.globals.items())
		passes = compiler.passes
		dimensions = compiler.dimensions
		options = compiler.options
	else:
		shaders = dict(main='void main() { gl_FragColor = vec4(1., 0., 0., 1.); }')
		globals = {}
		passes = []
		dimensions = {}
		options = []
	return success, shaders, globals, passes, dimensions, options, messages

@app.route('/')
def index():
	return app.send_static_file('index.html')

rand_push = random.randrange(1, 100)

@app.route('/refresh/<int:time>')
def refresh(time=None):
	mtime = int(max(map(os.path.getmtime, [fn, 'utility.sfr', 'compiler.py', 'live/serve.py']))) + rand_push
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