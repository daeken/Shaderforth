assert = require 'cassert'

Array::top = () -> @[@length-1]

origpop = Array::pop
Array::pop = (count=-1) ->
  if count == -1
    origpop.call(this)
  else
    results = []
    while count--
      results.unshift origpop.call(this)
    results

Array::include = (term) -> @indexOf(term) isnt -1

Array::pretty_print = () ->
  switch @length
    when 0
      '[]'
    when 1
      JSON.stringify elem
    else
      console.log '['
      for elem in @
        console.log '  ' + JSON.stringify(elem, null, 1).replace(/\s+/g, ' ')
      console.log ']'

Object::$copyinto = (dest) ->
  for key of @
    dest[key] = @[key]
  dest

String::repeat = (num) ->
  new Array(num+1).join @

class Tokens
  constructor: (@tokens) ->
    @offset = 0
    @length = @tokens.length
  peek: () ->
    assert @offset < @length
    @tokens[@offset]
  consume: () ->
    assert @offset < @length
    @tokens[@offset++]
  insert: (atoms) ->
    @tokens = @tokens[...@offset].concat(atoms).concat(@tokens[@offset...])
    @length += atoms.length
  end: () ->
    @offset >= @length

class Float
  constructor: (@value) ->

  toString: () ->
    @value.toString()

class Int
  constructor: (@value) ->

  toString: () ->
    '#' + @value.toString()

class Block
  constructor: (@compiler, atoms) ->
    @atoms = ['__startclosure', @].concat atoms
    @atoms.push '__endclosure'
    @macrolocals = @compiler.macrolocals.$copyinto {}
    @localstack = []

  invoke: () ->
    @localstack.push @compiler.macrolocals.$copyinto {}
    @macrolocals.$copyinto @compiler.macrolocals
    @compiler.blockstack.push @

  end: () ->
    @localstack.pop().$copyinto @compiler.macrolocals

class EffectCompiler
  compile: (code) ->
    @globals = {}
    @tempi = 0
    @blockstack = []

    @tokens = @tokenize code
    [@words, @macros, @globals] = @parseTop @tokens
    for name of @words
      continue if name[0] == '$'
      [args, effects] = @compile_word name
      @words[name] = [args, @ssaize(effects, args)]

  tokenize: (code) ->
    sub = (token) ->
      if (
        /^-?[0-9]+\.[0-9]*$/.test(token) ||
        /^-?\.[0-9]+$/.test(token) ||
        /^-?[0-9]+$/.test(token)
      )
        new Float(parseFloat token)
      else if /^#(-?[0-9]+)$/.test token
        new Int(parseInt token[1...])
      else
        token
    (sub(token) for token in code.split(/[ \t\n\r]+/))

  parseTop: (tokens) ->
    __globals = []
    words = {main : []}
    macros = {}
    stack = [words.main]
    i = 0
    while i < tokens.length
      token = tokens[i++]
      switch token
        when '(('
          comment_depth = 1
          while comment_depth > 0
            switch tokens[i++]
              when '))'
                comment_depth--
              when '(('
                comment_depth++
        when ':'
          name = tokens[i++]
          words[name] = []
          stack.push words[name]
        when ':m'
          name = tokens[i++]
          macros[name] = []
          stack.push macros[name]
        when ':globals'
          stack.push __globals
        when ';'
          stack.pop()
        else
          stack.top().push token

    [words, macros, __globals]

  compile_word: (name) ->
    @tokens = new Tokens(@words[name])
    @stack = []
    @locals = {}
    @macrolocals = {}
    @effectstack = [[]]

    while not @tokens.end()
      token = @tokens.consume()
      if token instanceof Float or token instanceof Int
        @stack.push token
      else if @['bword_' + token]
        @['bword_' + token]()
      else if token == '{'
        @stack.push @parse_block()
      else if token[...2] == '=>'
        @macro_assign token[2...]
      else if token[0] == '='
        @assign token[1...]
      else if @macrolocals[token]
        @stack.push @macrolocals[token]
      else if @locals[token] or @globals[token]
        @stack.push ['var', token]
      else
        console.log 'Unhandled token in word ' + name + ': ' + JSON.stringify(token)
        console.log 'Stack:', @stack
        assert false

    #console.log @stack
    assert @effectstack.length == 1
    #@effectstack[0].pretty_print()

    [[], @effectstack[0]]

  parse_block: () ->
    block_tokens = []
    block_depth = 1
    while block_depth > 0
      token = @tokens.consume()
      switch token
        when '}'
          block_depth--
        when '{', '/{', '\\{', '?{', '~{'
          block_depth++
      block_tokens.push token if block_depth > 0
    new Block @, block_tokens

  ssaize: (effects, args) ->
    ivars = {}
    for arg in args
      ivars[arg] = 0
    sub = (block, ivars) ->
      rewrite_vars = (effect) ->
        if effect instanceof Array
          switch effect[0]
            when 'var'
              ['var', effect[1], vars[effect[1]]]
            else
              rewrite_vars(elem) for elem in effect
        else
          effect
      vars = ivars.$copyinto {}
      neweffects = []
      i = 0
      for effect in block
        if i++ == 0 and effect == 'block'
          neweffects.push 'block'
          continue
        switch effect[0]
          when 'assign'
            val = rewrite_vars effect[2]
            if vars[effect[1]] == undefined
              vars[effect[1]] = 0
            else
              vars[effect[1]]++
            neweffects.push ['assign', [effect[1], vars[effect[1]]], val]
          when 'for'
            [start, end] = [rewrite_vars(effect[2]), rewrite_vars(effect[3])]
            if vars[effect[1]] == undefined
              vars[effect[1]] = 0
            else
              vars[effect[1]]++
            neweffects.push ['for', [effect[1], vars[effect[1]]], start, end]
          when 'block'
            [nblock, ovars] = sub effect, vars
            neweffects.push nblock
            for key of ovars
              if vars[key] == undefined or ovars[key] > vars[key]
                neweffects.push ['phi', key, ovars[key]+1, ovars[key], vars[key]]
                vars[key] = ovars[key]+1
          else
            neweffects.push rewrite_vars effect
      [neweffects, vars]
    sub(effects, ivars)[0]

  tempname: () ->
    'temp_' + @tempi++

  assign: (name) ->
    if not @globals[name] and not @locals[name]
      @locals[name] = 'int' # XXX: infer type here
    @effectstack.top().push ['assign', name, @stack.pop()]
  macro_assign: (name) ->
    @macrolocals[name] = @stack.pop()

  'bword_+': () -> @stack.push ['+'].concat @stack.pop 2
  'bword_-': () -> @stack.push ['-'].concat @stack.pop 2
  'bword_*': () -> @stack.push ['*'].concat @stack.pop 2
  'bword_/': () -> @stack.push ['/'].concat @stack.pop 2
  'bword_<': () -> @stack.push ['<'].concat @stack.pop 2

  'bword_times': () ->
    [block, count] = @stack.pop 2
    tname = @tempname()

    @effectstack.top().push ['for', tname, new Int(0), count]
    nblock = ['block']
    @effectstack.top().push nblock
    @effectstack.push nblock
    @stack.push '__term__'
    @stack.push ['var', tname]
    @locals[tname] = 'int'

    @tokens.insert block.atoms.concat ['__endblock']

  'bword___endblock': () ->
    @effectstack.pop()
    while @stack.pop() != '__term__'
      ;

  'bword___startclosure': () ->
    block = @tokens.consume()
    block.invoke()
  'bword___endclosure': () ->
    @blockstack.pop().end()

class CodeBuilder
  constructor: () ->
    @code = ''
    @depth = 0

  pushstmt: (snippet) ->
    @code += '  '.repeat(@depth) + snippet + ';\n'
    return
  pushblock: (pre) ->
    @code += '  '.repeat(@depth++) + pre + ' {\n'
    return
  popblock: () ->
    @code += '  '.repeat(--@depth) + '}\n'
    return

  build_all: (effects) ->
    for effect in effects
      built = @build_one effect
      if built != undefined
        @pushstmt built

  build_one: (effect) ->
    if effect instanceof Object and effect.value != undefined
      return effect.value.toString()
    if @['build_' + effect[0]] == undefined
      console.log 'Unknown effect:', effect
      assert false
    @['build_' + effect[0]] effect

  build_assign: ([_, name, value]) ->
    "#{name[0]} = #{@build_one value}"

  build_for: ([_, name, start, end]) ->
    @pushblock "for(#{name[0]} = #{@build_one start}; #{name[0]} < #{@build_one end}; #{name[0]}++)"

  build_block: (block) ->
    @build_all block[1...]
    @popblock()

  build_phi: () ->

  'build_+': ([_, left, right]) ->
    "#{@build_one left} + #{@build_one right}"

  build_var: ([_, name, __]) ->
    name

class JSCompiler extends CodeBuilder
  compile: (code) ->
    @compiler = new EffectCompiler()
    @compiler.compile code
    #console.log JSON.stringify @compiler.words
    for name of @compiler.words
      continue if name[0] == '$'

      @build_word name
    console.log @code

  build_word: (name) ->
    @pushblock 'function ' + name + '()'
    @build_all @compiler.words[name][1]
    @popblock()

new JSCompiler().compile '5 =>foo 0 =temp { temp + =temp } 10 times temp foo + =bar temp 6 + =temp bar 7 + =bar'
