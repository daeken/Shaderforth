import coffeescript
from flask import Flask
app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
	return app.send_static_file('index.html')

@app.route('/<name>.coffee')
def coffee(name=None):
	try:
		return coffeescript.compile_file('%s.coffee' % name, bare=True)
	except Exception, e:
		print e.message
		return "console.log('Compilation error in \"' + %r + '\": ' + %r)" % (str(name), str(e.message))

if __name__=='__main__':
	app.run()