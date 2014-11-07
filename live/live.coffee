last = 0
ctx = null
attachments = {}
mousepos = [0, 0]
mousestate = [0, 0]

soptions = null

$(document).ready () ->
	cvs = $('#cvs')[0]
	cvs.width = cvs.style['width'] = 800
	cvs.height = cvs.style['height'] = 450
	ctx = cvs.getContext('webgl')
	ctx.getExtension('OES_texture_float')

	$('#cvs').mousemove (evt) ->
		parentOffset = $(this).parent().offset()
		mousepos = [(evt.pageX - parentOffset.left) / cvs.width * 2 - 1, (evt.pageY - parentOffset.top) / cvs.height * 2 - 1]
	$('#cvs').mousedown () ->
		mousestate[0] = 1
	$('#cvs').mouseup () ->
		mousestate[0] = 0
	
	refresh = ->
		setTimeout refresh, 500
		success = (data) ->
			if data == null
				return
			[last, success, shaders, globals, passes, dimensions, options, messages, errors] = data
			$('#messages').text(messages)
			$('#errors').text(errors)
			if success
				init_options options
				init shaders, globals, passes, dimensions
		$.ajax 'refresh/' + last, { dataType: 'json', success: success }
	refresh()

class Renderer
	constructor: (@name, @target, @code, @dimensions=[800, 450]) ->
		@texture = null
		@textures = []
		if @name == 'main'
			@rtt = null
		else
			@rtt = ctx.createFramebuffer()
			ctx.bindFramebuffer(ctx.FRAMEBUFFER, @rtt)
			@texture = @fresh_texture()

			@renderbuffer = ctx.createRenderbuffer()
			ctx.bindRenderbuffer(ctx.RENDERBUFFER, @renderbuffer)
			ctx.renderbufferStorage(ctx.RENDERBUFFER, ctx.DEPTH_COMPONENT16, @dimensions[0], @dimensions[1])

			ctx.framebufferRenderbuffer(ctx.FRAMEBUFFER, ctx.DEPTH_ATTACHMENT, ctx.RENDERBUFFER, @renderbuffer)

			ctx.bindTexture(ctx.TEXTURE_2D, null)
			ctx.bindRenderbuffer(ctx.RENDERBUFFER, null)
			ctx.bindFramebuffer(ctx.FRAMEBUFFER, null)

		p = ctx.createProgram()
		v = ctx.createShader(ctx.VERTEX_SHADER)
		ctx.shaderSource(v, 'precision highp float; attribute vec3 p; void main() { gl_Position = vec4(p.xyz-1.0, 1); }')
		ctx.compileShader(v)
		if !ctx.getShaderParameter(v, ctx.COMPILE_STATUS)
			console.log('Failed to compile vertex shader.')
			console.log(ctx.getShaderInfoLog(v))
		ctx.attachShader(p, v)
		f = ctx.createShader(ctx.FRAGMENT_SHADER)
		ctx.shaderSource(f, 'precision highp float; ' + @code)
		ctx.compileShader(f)
		if !ctx.getShaderParameter(f, ctx.COMPILE_STATUS)
			console.log('Failed to compile fragment shader ' + @name + '.')
			$('#errors').text($('#errors').text() + '\n' + ctx.getShaderInfoLog(f))
		$('#messages').text($('#messages').text() + '\n' + @code)
		ctx.attachShader(p, f)
		ctx.linkProgram(p)
		@p = p

	fresh_texture: ->
		need = @texture == null

		if not need
			for name, id of attachments
				if name != @target and id == @texture
					need = true

		if need
			attachments[@target] = null
			for id in @textures
				found = false
				for name, aid of attachments
					if aid == id
						found = true
						break
				if !found
					attachments[@target] = id
					break
			if attachments[@target] == null
				@texture = ctx.createTexture()
				ctx.bindTexture(ctx.TEXTURE_2D, @texture)
				ctx.texParameteri(ctx.TEXTURE_2D, ctx.TEXTURE_MAG_FILTER, ctx.NEAREST)
				ctx.texParameteri(ctx.TEXTURE_2D, ctx.TEXTURE_MIN_FILTER, ctx.NEAREST)
				ctx.texParameteri(ctx.TEXTURE_2D, ctx.TEXTURE_WRAP_S, ctx.CLAMP_TO_EDGE)
				ctx.texParameteri(ctx.TEXTURE_2D, ctx.TEXTURE_WRAP_T, ctx.CLAMP_TO_EDGE)
				ctx.texImage2D(ctx.TEXTURE_2D, 0, ctx.RGBA, @dimensions[0], @dimensions[1], 0, ctx.RGBA, ctx.FLOAT, null)
				@textures.push @texture

		ctx.framebufferTexture2D(ctx.FRAMEBUFFER, ctx.COLOR_ATTACHMENT0, ctx.TEXTURE_2D, @texture, 0)
		return @texture

	render: (time) ->
		if @rtt != null
			ctx.bindFramebuffer(ctx.FRAMEBUFFER, @rtt)
			@fresh_texture()

		ctx.viewport(0, 0, @dimensions[0], @dimensions[1])
		ctx.bindBuffer ctx.ARRAY_BUFFER, ctx.createBuffer()
		ctx.bufferData ctx.ARRAY_BUFFER, new Float32Array([0,0,2,0,0,2,2,0,2,2,0,2]), ctx.STATIC_DRAW
		ctx.vertexAttribPointer 0, 2, ctx.FLOAT, 0, 0, 0
		ctx.enableVertexAttribArray(ctx.getAttribLocation @p, 'p')
		ctx.useProgram(@p)
		ctx.uniform3f(ctx.getUniformLocation(@p, 'iResolution'), 800, 450, 0)
		ctx.uniform4f(ctx.getUniformLocation(@p, 'iMouse'), mousepos[0], mousepos[1], mousestate[0], mousestate[1])
		ctx.uniform1f(ctx.getUniformLocation(@p, 'iGlobalTime'), time)
		date = new Date
		ctx.uniform4f(ctx.getUniformLocation(@p, 'iDate'), date.getFullYear(), date.getMonth(), date.getDay(), date.getHours() * 60 * 60 + date.getMinutes() * 60 + date.getSeconds())

		for name, [type, elem] of soptions
			if type == 'bool'
				if elem.is(':checked')
					ctx.uniform1i(ctx.getUniformLocation(@p, name), 1)
				else
					ctx.uniform1i(ctx.getUniformLocation(@p, name), 0)

		i = 0
		for name, id of attachments
			ctx.activeTexture(ctx.TEXTURE0 + i)
			ctx.bindTexture(ctx.TEXTURE_2D, id)
			ctx.uniform1i(ctx.getUniformLocation(@p, name), i)
			i++

		ctx.drawArrays 4, 0, 6

		ctx.finish()

		ctx.bindFramebuffer(ctx.FRAMEBUFFER, null)

		return @texture

init = (shaders, globals, passes, dimensions) ->
	clast = last
	mousepos = [0, 0]

	renderers = {}
	for [dest, src] in passes
		if shaders[src] != undefined
			renderers[dest] = new Renderer(src, dest, shaders[src], dimensions[dest])
		attachments[dest] = null
	main = new Renderer('main', null, shaders['main'])

	start = new Date
	frame = ->
		if clast != last
			return
		time = ((new Date) - start) / 1000
		for [dest, src] in passes
			if renderers[dest] != undefined
				attachments[dest] = renderers[dest].render time
			else
				attachments[dest] = attachments[src]
		main.render time

		requestAnimationFrame frame
	frame()

init_options = (options) ->
	soptions = {}
	elem = $('#options')
	elem.empty()
	for [name, type, params] in options
		if type == 'toggle'
			elem.append('<input type="checkbox" id="__option_' + name + '"> ' + name + '<br>')
			soptions[name] = ['bool', $('#__option_' + name)]
