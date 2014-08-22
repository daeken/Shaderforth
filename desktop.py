'''
Plasma Shader
=============

This shader example have been taken from http://www.iquilezles.org/apps/shadertoy/
with some adapation.

This might become a Kivy widget when experimentation will be done.
'''

import os, sys
from compiler import Compiler
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Color, Fbo, Rectangle, RenderContext
from kivy.graphics.opengl import glActiveTexture, GL_TEXTURE0
from kivy.properties import StringProperty

# This header must be not changed, it contain the minimum information from Kivy.
header = '''
#ifdef GL_ES
precision highp float;
#endif
'''

class RTT(Fbo):
	def __init__(self, code, **kwargs):
		Fbo.__init__(self, **kwargs)
		self.canvas = RenderContext()

		shader = self.canvas.shader
		shader.fs = header + code
		if not shader.success:
			print '! Shader compilation failed (GLSL)'
			assert False

class ShaderWidget(FloatLayout):

	# property to set the source code for fragment shader
	fs = StringProperty(None)

	def __init__(self, **kwargs):
		# Instead of using Canvas, we will use a RenderContext,
		# and change the default shader used.
		self.canvas = RenderContext()

		# call the constructor of parent
		# if they are any graphics object, they will be added on our new canvas
		super(ShaderWidget, self).__init__(**kwargs)

		# We'll update our glsl variables in a clock
		Clock.schedule_interval(self.update_glsl, 1 / 60.)

	def on_fs(self, instance, value):
		self.shaderfn = value
		self.time_last = os.path.getmtime(self.shaderfn)
		self.utime_last = os.path.getmtime('utility.glf')
		try:
			compiler = Compiler(file(value, 'r').read().decode('utf-8'), False, False)
		except:
			print 'Shaderforth failure'
			import traceback
			traceback.print_exc()
			return
		output = compiler.outcode
		self.build_fbos(compiler)
		for ep, code in output.items():
			print '// !%s!' % ep
			print code
		value = header + output['main']

		# set the fragment shader to our source code
		shader = self.canvas.shader
		old_value = shader.fs
		shader.fs = value
		if not shader.success:
			shader.fs = old_value
			print 'Shader compilation failed (GLSL)'
			#raise Exception('failed')

	def build_fbos(self, compiler):
		self.compiler = compiler
		self.fbos = {}
		for dest, src in compiler.passes:
			if src in compiler.globals:
				self.fbos[dest] = src
				continue
			with self.canvas:
				fbo = self.fbos[dest] = RTT(compiler.outcode[src], size=compiler.dimensions.get(dest, Window.size))

	def update_glsl(self, *largs):
		for i, (name, fbo) in enumerate(self.fbos.items()):
			glActiveTexture(GL_TEXTURE0 + 1)
			fbo.texture.bind()
			self.canvas[str(name)] = 1
			for sfbo in self.fbos.values():
				sfbo.canvas[str(name)] = 1
			fbo.canvas['iGlobalTime'] = Clock.get_boottime()
			fbo.canvas['iResolution'] = list(map(float, self.size)) + [0.0]
			# This is needed for the default vertex shader.
			fbo.canvas['projection_mat'] = Window.render_context['projection_mat']
			fbo.bind()
			fbo.canvas.draw()
			fbo.release()
			glActiveTexture(GL_TEXTURE0 + 1)
			fbo.texture.bind()
		self.canvas['iGlobalTime'] = Clock.get_boottime()
		self.canvas['iResolution'] = list(map(float, self.size)) + [0.0]
		# This is needed for the default vertex shader.
		self.canvas['projection_mat'] = Window.render_context['projection_mat']
		
		mtime = os.path.getmtime(self.shaderfn)
		umtime = os.path.getmtime('utility.glf')
		if mtime != self.time_last or umtime != self.utime_last:
			self.on_fs(self, self.shaderfn)
			self.time_last = mtime

class DesktopApp(App):
	def build(self):
		self.title = 'Shaderforth Live -- ' + sys.argv[1]
		return ShaderWidget(fs=sys.argv[1])

if __name__ == '__main__':
	DesktopApp().run()
