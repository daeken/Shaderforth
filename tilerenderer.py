import os, sys, time, datetime
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import *
from OpenGL.arrays import vbo
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, glBindVertexArray
from PIL import Image
import numpy

from compiler import Compiler

vert = '''
attribute vec3 p;
void main() {
	gl_Position = vec4(p.xyz, 1);
}
'''

tiler = '''
:globals
	@vec2 uniform =tileOff
;
:m gl_FragCoord $gl_FragCoord [ tileOff 0 0 ] + ;
'''

utility = file(os.path.dirname(os.path.realpath(__file__)) + '/utility.sfr', 'r').read().decode('utf-8')
compiler = Compiler(tiler + file(sys.argv[1], 'r').read().decode('utf-8'), utility)
assert len(compiler.outcode) == 1
frag = compiler.outcode['main']

swidth = 960
sheight = 540
scale = 8
twidth = swidth * scale
theight = sheight * scale
final_scale = 4
frametime = 0
frames = []
for x in xrange(0, twidth, swidth):
	for y in xrange(0, theight, sheight):
		frames.append((x, y))

im = Image.new('RGB', (twidth, theight))

def init():
	global program, vertexPositions, indexPositions
	glClearColor(0, 1, 0, 0)

	program = compileProgram(
		compileShader(vert, GL_VERTEX_SHADER), 
		compileShader(frag, GL_FRAGMENT_SHADER)
	)
	vertices = numpy.array([[-1,-1,0],[1,-1,0],[1,1,0], [1,1,0],[-1,1,0],[-1,-1,0]], dtype='f')
	vertexPositions = vbo.VBO(vertices)
	indices = numpy.array([[0,1,2],[3,4,5]], dtype=numpy.int32)
	indexPositions = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
	glEnableVertexAttribArray(glGetAttribLocation(program, 'p'))

def render():
	global im
	glClear(GL_COLOR_BUFFER_BIT)
	glUseProgram(program)
	glViewport(0, 0, swidth, sheight)
	glUniform3f(glGetUniformLocation(program, 'iResolution'), twidth, theight, 0)
	glUniform1f(glGetUniformLocation(program, 'iGlobalTime'), frametime)
	glUniform2f(glGetUniformLocation(program, 'R'), twidth, theight)
	glUniform1f(glGetUniformLocation(program, 'T'), frametime)
	print 'Frames left:', len(frames)
	off = frames.pop(0)
	glUniform2f(glGetUniformLocation(program, 'tileOff'), *off)
	indexPositions.bind()
	vertexPositions.bind()
	glEnableVertexAttribArray(0)
	glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)
	glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
	data = glReadPixels(0, 0, swidth, sheight, GL_RGB, GL_UNSIGNED_BYTE, outputType=None)
	data = numpy.flipud(data.reshape((sheight, swidth, 3)).astype(numpy.uint8))
	im.paste(Image.fromarray(data), (off[0], theight - off[1] - sheight))
	#glutSwapBuffers()
	if len(frames):
		glutPostRedisplay()
	else:
		if sys.argv[2] != '-':
			im.save(sys.argv[2])
		if scale != final_scale and sys.argv[3] != '-':
			im = im.resize((swidth * final_scale, sheight * final_scale), Image.LANCZOS)
			im.save(sys.argv[3])
		sys.exit(0)

glutInit([])
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(swidth, sheight)
glutCreateWindow("Shaderforth Renderer")
glutDisplayFunc(render)

init()

glutMainLoop()