import sys, time, datetime
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import *
from OpenGL.arrays import vbo
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, glBindVertexArray
import cv, cv2
import numpy

from compiler import Compiler

vert = '''
attribute vec3 p;
void main() {
	gl_Position = vec4(p.xyz, 1);
}
'''

utility = file('utility.sfr', 'r').read().decode('utf-8')
compiler = Compiler(file(sys.argv[1], 'r').read().decode('utf-8'), utility, False, False)
assert len(compiler.outcode) == 1
frag = compiler.outcode['main']

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

width, height = 1280, 720
#width, height = 1920, 1080
#width, height = 800, 600
fr = 60
out = cv2.VideoWriter(sys.argv[2], cv2.cv.CV_FOURCC(*'jpeg'), fr, (width, height))

start = time.time()
frame = 0.0
endtime = float(sys.argv[3])
last = endtime * fr
def render():
	global frame, out
	glClear(GL_COLOR_BUFFER_BIT)
	glUseProgram(program)
	glViewport(0, 0, width, height)
	glUniform3f(glGetUniformLocation(program, 'iResolution'), width, height, 0)
	glUniform1f(glGetUniformLocation(program, 'iGlobalTime'), frame / fr)
	if frame % fr == 0 and frame > 0:
		persec = (time.time() - start) / frame
		remaining = persec * (last - frame)
		print 'Rendered %i frames at %f frames/second, %i:%02i remaining (est %s)' % (frame, 1 / persec, remaining / 60, remaining % 60, (datetime.datetime.now() + datetime.timedelta(seconds=remaining)).strftime('%m/%d %H:%M:%S'))
	indexPositions.bind()
	vertexPositions.bind()
	glEnableVertexAttribArray(0)
	glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)
	glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
	data = glReadPixels(0, 0, width, height, GL_BGR, GL_UNSIGNED_BYTE, outputType=None)
	data = numpy.flipud(data.reshape((height, width, 3)).astype(numpy.uint8))
	out.write(data)
	glutSwapBuffers()
	frame += 1
	if frame < last:
		glutPostRedisplay()
	else:
		out.release()
		out = None
		sys.exit()

glutInit([])
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(width, height)
glutCreateWindow("Shaderforth Renderer")
glutDisplayFunc(render)

init()

glutMainLoop()