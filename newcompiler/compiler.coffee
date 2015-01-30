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

Array::retrieve = (offset) ->
  val = @[@.length - offset - 1]
  @splice @.length - offset - 1, 1
  val

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
  consume_if: (token) ->
    if @peek() == token
      return @consume()
    return false
  insert: (atoms) ->
    @tokens = @tokens[...@offset].concat(atoms).concat(@tokens[@offset...])
    @length += atoms.length
  end: () ->
    @offset >= @length
  rest: () ->
    @tokens[@offset...]

class Float
  constructor: (@value) ->

  toString: () ->
    @value.toString()

class Int
  constructor: (@value) ->

  toString: () ->
    '#' + @value.toString()

class Type
  constructor: (@name) ->
    @attributes = []

  add_attribute: (attr) ->
    @attributes.push attr if not @attributes.include attr
    @

  toString: () ->
    [@name].concat(@attributes).join ' '


toNative = (val) ->
  if val instanceof Int or val instanceof Float
    val.value
  else
    val

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
    [@words, @macros, @globals] = @parse_top @tokens
    for name of @macros
      continue if name[0] == '$'
      @macros[name] = @rewrite_macro name
    for name of @words
      continue if name[0] == '$'
      @words[name] = @parse_args name
    for name of @words
      continue if name[0] == '$'
      word = @words[name]
      [effects, locals] = @compile_word name
      @words[name] = {
        args: word.args, 
        return_type: word.return_type, 
        locals: locals, 
        effects: @ssaize(effects, word.args)
      }

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

  parse_top: (tokens) ->
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

    if words.main.length == 0
      delete words.main

    [words, macros, __globals]

  rewrite_macro: (name) ->
    @rewrite_block @macros[name], name

  rewrite_block: (rtokens, name) ->
    name = "block_#{@tempname()}" if not name
    tokens = new Tokens rtokens

    namei = 0
    specstack = [[]]
    stored = []
    all_names = []
    if tokens.consume_if '('
      while (token = tokens.consume()) != ')'
        switch token
          when '['
            specstack.top().push nspec = []
            specstack.push nspec
          when ']'
            specstack.pop()
          else
            if token[0] == '$'
              token = token[1...]
              stored.push token
            specstack.top().push token
            all_names.push token
    else
      prefixes = '&\\/?*'.split('').concat ['']
      for prefix in prefixes
        if rtokens.include(prefix + '_')
          specstack = [['_']]
          all_names = ['_']
          break

    result = []
    recurspec = (spec) ->
      for elem, i in spec
        if i != spec.length - 1
          result.push spec.length - i - 1
          result.push 'take'
        if elem instanceof Array
          result.push 'flatten'
          recurspec elem
        else if stored.include elem
          result.push "=$macro_#{name}_#{elem}"
        else
          result.push "=>macro_#{name}_#{elem}"
    recurspec specstack[0]
    while not tokens.end()
      token = tokens.consume()
      stoken = token.toString()
      sigil = ''
      if /\*\\\/&/.test stoken[0]
        sigil = stoken[0]
        stoken = stoken[1...]
      if all_names.include stoken
        result.push "#{sigil}macro_#{name}_#{token}"
      else
        result.push token
    result

  parse_args: (name) ->
    tokens = new Tokens @words[name]
    if tokens.consume() != '('
      return {args: [], return_type: 'void', tokens: @words[name]}

    args = []
    return_type = 'void'
    args_done = false
    preamble = []
    while true
      token = tokens.consume()
      if token == ')'
        break
      else if token == '->'
        args_done = true
      else if args_done
        return_type = token
        assert tokens.peek() == ')'
      else
        if token.indexOf(':') != -1
          [aname, type] = token.split ':'
          args.push [aname, type]
        else
          aname = @tempname()
          args.push [aname, token]
          preamble.push aname
    tokens.insert preamble

    {args: args, return_type: return_type, tokens: tokens.rest()}

  compile_word: (name) ->
    @tokens = new Tokens @words[name].tokens
    @stack = []
    @locals = {}
    @macrolocals = {}
    @effectstack = [[]]

    for [aname, type] in @words[name].args
      @locals[aname] = type
    
    while not @tokens.end()
      token = @tokens.consume()
      if token instanceof Float or token instanceof Int
        @stack.push token
      else if @['bword_' + token]
        @['bword_' + token]()
      else if @macros[token]
        @tokens.insert @macros[token]
      else if token == '{'
        @stack.push @parse_block()
      else if token[...2] == '=>'
        @macro_assign token[2...]
      else if token[...2] == '=$'
        @macro_store token[2...]
      else if token[0] == '='
        @assign token[1...]
      else if @macrolocals[token]
        @stack.push @macrolocals[token]
      else if token[0] == '@'
        @stack.push new Type token[1...]
      else if @words[token]
        params = @stack.pop @words[token].args.length
        if @words[token][1] != 'void'
          @stack.push ['call', token, params]
        else
          @effectstack.top().push ['call', token, params]
      else if @locals[token] or @globals[token]
        @stack.push ['var', token]
      else
        console.log 'Unhandled token in word ' + name + ': ' + JSON.stringify(token)
        console.log 'Stack:', @stack
        assert false
      first = false
    assert @effectstack.length == 1

    if @words[name].return_type == 'void'
      assert @stack.length == 0
    else
      assert @stack.length == 1
      @effectstack[0].push ['return', @stack.pop()]

    [@effectstack[0], @locals]

  infer_type: (atom) ->
    return atom if atom instanceof Type
    return new Type('float') if atom instanceof Float
    return new Type('int') if atom instanceof Int
    switch atom[0]
      when 'var'
        if @globals[atom[1]]
          @globals[atom[1]]
        else if @locals[atom[1]]
          @locals[atom[1]]
        else
          console.log 'Unknown atom to infer_type:', atom
          assert false
      when 'call'
        assert @words[atom[1]]
        @words[atom[1]].return_type
      when '+', '-', '*', '/'
        @infer_type atom[1]
      else
        console.log 'Unknown atom to infer_type:', atom
        assert false

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
    new Block @, @rewrite_block(block_tokens)

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

  is_stored: (val) ->
    (
      val instanceof Int or val instanceof Float or 
      val[0] == 'var' or
      (val[0] == 'swizzle' and val[1][0] == 'var')
    )

  ensure_stored: (pop=false) ->
    top = @stack.pop()

    if @is_stored top
      if not pop
        @stack.push top
      top
    else
      name = "tvar_#{@tempname()}"
      tvar = ['var', name]
      @locals[name] = @infer_type top
      @effectstack.top().push ['assign', name, top]
      if not pop
        @stack.push tvar
      tvar

  assign: (name) ->
    value = @stack.pop()
    if not @globals[name] and not @locals[name]
      @locals[name] = @infer_type value
    @effectstack.top().push ['assign', name, value]
  macro_assign: (name) ->
    @macrolocals[name] = @stack.pop()
  macro_store: (name) ->
    if @is_stored @stack.top()
      @macrolocals[name] = @stack.pop()
    else
      @assign name

  'bword_+': () -> @stack.push ['bop', '+'].concat @stack.pop 2
  'bword_-': () -> @stack.push ['bop', '-'].concat @stack.pop 2
  'bword_*': () -> @stack.push ['bop', '*'].concat @stack.pop 2
  'bword_/': () -> @stack.push ['bop', '/'].concat @stack.pop 2
  'bword_<': () -> @stack.push ['bop', '<'].concat @stack.pop 2
  'bword_>': () -> @stack.push ['bop', '>'].concat @stack.pop 2
  'bword_==': () -> @stack.push ['bop', '=='].concat @stack.pop 2

  push_block: () ->
    nblock = ['block']
    @effectstack.top().push nblock
    @effectstack.push nblock
    nblock

  bword_times: () ->
    [block, count] = @stack.pop 2
    tname = @tempname()

    @effectstack.top().push ['for', tname, new Int(0), count]
    @push_block()
    @stack.push '__term__'
    @stack.push ['var', tname]
    @locals[tname] = 'int'

    @tokens.insert block.atoms.concat ['__endblock']

  bword_when: () ->
    [block, cond] = @stack.pop 2
    @effectstack.top().push ['if', cond]
    @push_block()
    @stack.push '__term__'

    @tokens.insert block.atoms.concat ['__endblock']

  bword_if: () ->
    [if_, else_, cond] = @stack.pop 3
    @effectstack.top().push ['if', cond]
    @push_block()
    @stack.push else_
    @stack.push '__term__'
    @tokens.insert if_.atoms.concat ['__endblock', '__else']

  bword___else: () ->
    else_ = @stack.pop()
    @effectstack.top().push ['else']
    @push_block()
    @stack.push '__term__'
    @tokens.insert else_.atoms.concat ['__endblock']

  bword___endblock: () ->
    @effectstack.pop()
    while @stack.pop() != '__term__'
      ;

  bword_call: () ->
    block = @stack.pop()
    @tokens.insert block.atoms

  bword___startclosure: () ->
    block = @tokens.consume()
    block.invoke()
  bword___endclosure: () ->
    @blockstack.pop().end()

  bword_return: () ->
    @effectstack.top().push ['return', @stack.pop()]
  'bword_return-nil': () ->
    @effectstack.top().push ['return']

  bword_swap: () ->
    [a, b] = @stack.pop 2
    @stack.push b
    @stack.push a
  bword_drop: () ->
    @stack.pop()
  bword_take: () ->
    offset = toNative @stack.pop()
    @stack.push @stack.retrieve offset
  bword_dup: () ->
    @stack.push @ensure_stored()

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

  compile: (code) ->
    @compiler = new EffectCompiler()
    @compiler.compile code
    #console.log JSON.stringify @compiler.words
    for name of @compiler.words
      continue if name[0] == '$'

      @build_word name
    console.log @code

  build_word: (name) ->
    @vars_defined = (aname for aname in @compiler.words[name].args)
    @locals = @compiler.words[name].locals

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

  build_var: ([_, name, __]) ->
    name

  build_return: (effect) ->
    if effect.length == 1
      'return'
    else
      "return #{@build_one effect[1]}"

  build_call: ([_, name, args]) ->
    "#{name}(#{(@build_one arg for arg in args).join ', '})"

  'build_bop': ([_, op, left, right]) ->
    "#{@build_one left} #{op} #{@build_one right}"

  build_if: ([_, cond]) ->
    @pushblock "if(#{@build_one cond})"
  build_else: () ->
    @pushblock "else"

  build_phi: () ->

class JSCompiler extends CodeBuilder
  build_word: (name) ->
    super
    @pushblock "function #{name}(#{(arg[0] for arg in @compiler.words[name].args).join ', '})"
    @build_all @compiler.words[name].effects
    @popblock()

  build_assign: ([_, name, value]) ->
    if @vars_defined.include name[0]
      "#{name[0]} = #{@build_one value}"
    else
      @vars_defined.push name[0]
      "var #{name[0]} = #{@build_one value}"

  build_for: ([_, name, start, end]) ->
    if not @vars_defined.include name[0]
      @vars_defined.push name[0]
      def = 'var '
    else
      def = ''
    @pushblock "for(#{def}#{name[0]} = #{@build_one start}; #{name[0]} < #{@build_one end}; #{name[0]}++)"

  build_block: (block) ->
    @build_all block[1...]
    @popblock()

class GLSLCompiler extends CodeBuilder
  build_word: (name) ->
    super
    @pushblock "#{@compiler.words[name].return_type} #{name}(#{(arg[1] + ' ' + arg[0] for arg in @compiler.words[name].args).join ', '})"
    @build_all @compiler.words[name].effects
    @popblock()

  build_assign: ([_, name, value]) ->
    if @vars_defined.include name[0]
      "#{name[0]} = #{@build_one value}"
    else
      @vars_defined.push name[0]
      "#{@locals[name[0]]} #{name[0]} = #{@build_one value}"

  build_for: ([_, name, start, end]) ->
    if not @vars_defined.include name[0]
      @vars_defined.push name[0]
      def = 'var '
    else
      def = ''
    @pushblock "for(#{def}#{name[0]} = #{@build_one start}; #{name[0]} < #{@build_one end}; #{name[0]}++)"

  build_block: (block) ->
    @build_all block[1...]
    @popblock()

code = '5 =foo { foo 1 + =foo } { 0 =foo } foo 5 == if'
new GLSLCompiler().compile code
new JSCompiler().compile code
