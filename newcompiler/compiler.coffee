assert = require 'cassert'
fs = require 'fs'

Array::is_array = true
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
      console.log '[]'
    when 1
      console.log JSON.stringify elem
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
    val = @value.toFixed(5)
    val.replace /0+$/, ''

  fold: (right, func) ->
    new Float func(@value, right.value)
  '+': (right) -> @fold right, (a, b) -> a + b
  '-': (right) -> @fold right, (a, b) -> a - b
  '**': (right) -> @fold right, (a, b) -> Math.pow a, b


class Int
  constructor: (@value) ->

  toString: () ->
    @value.toString()

class Type
  constructor: (@name) ->
    @attributes = []

  add_attribute: (attr) ->
    @attributes.push attr if not @attributes.include attr
    @

  toString: () ->
    @attributes.concat([@name]).join ' '


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

builtin_vars = {
  gl_FragCoord: 'vec4', 
  gl_FragColor: 'vec4'
}

class EffectCompiler
  compile: (code) ->
    @globals = {}
    @tempi = 0
    @blockstack = []

    @tokens = @tokenize code
    [@words, @macros, wrappers, globals] = @parse_top @tokens
    @wrappers = {}
    for name, tokens of wrappers
      continue if name[0] == '$'
      @add_wrapper name, tokens
    @words['__globals'] = {args: [], return_type: 'void', tokens: globals}
    [_, @globals] = @compile_word '__globals'
    delete @words['__globals']
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
    wrappers = {}
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
        when ':wrap'
          name = tokens[i++]
          wrappers[name] = []
          stack.push wrappers[name]
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

    [words, macros, wrappers, __globals]

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

  add_wrapper: (name, tokens) ->
    tokens = new Tokens tokens
    args = []
    return_type = 'void'
    native_name = name
    assert tokens.consume() == '('
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
        args.push token
    native_name = tokens.consume() if not tokens.end()
    assert tokens.end()

    @wrappers[name] = {args: args, return_type: return_type, native_name: native_name}

  compile_word: (name) ->
    @tokens = new Tokens @words[name].tokens

    @stack = []
    @stackstack = []
    @locals = {}
    @macrolocals = {}
    @effectstack = [[]]
    for [aname, type] in @words[name].args
      @locals[aname] = new Type type

    while not @tokens.end()
      token = @tokens.consume()
      if token instanceof Float or token instanceof Int
        @stack.push token
      else if @['word_' + token]
        @['word_' + token]()
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
      else if token[0] == '.'
        @swizzle token[1...]
      else if token[0] == '!' and token.length > 1
        @word_dup()
        @tokens.insert @parse_block(token[1...]).atoms
      else if token[0] == '\\' and token.length > 1
        @reduce @parse_block token[1...]
      else if token[0] == '/' and token.length > 1
        @map @parse_block token[1...]
      else if token[...2] == '$[' and token[token.length-1] == ']'
        @range_literal token[2...-1]
      else if @words[token]
        params = @stack.pop @words[token].args.length
        if @words[token].return_type != 'void'
          @stack.push ['call', token, params]
        else
          @effectstack.top().push ['call', token, params]
      else if @wrappers[token]
        params = @stack.pop @wrappers[token].args.length
        if @wrappers[token].return_type != 'void'
          @stack.push ['call', @wrappers[token].native_name, params]
        else
          @effectstack.top().push ['call', @wrappers[token].native_name, params]
      else if @locals[token] or @globals[token] or builtin_vars[token]
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

    [@vectorize(@effectstack[0]), @locals]

  vectorize: (effect) ->
    return effect if not effect.is_array or not effect.length

    if effect[0] == 'list'
      @stack.push effect
      @avec()
      @vectorize @stack.pop()
    else
      @vectorize(elem) for elem in effect

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
        else if builtin_vars[atom[1]]
          new Type builtin_vars[atom[1]]
        else
          console.log 'Unknown atom to infer_type:', atom
          assert false
      when 'call'
        if @words[atom[1]]
          new Type @words[atom[1]].return_type
        else if @wrappers[atom[1]]
          wrapper = @wrappers[atom[1]]
          if wrapper.return_type == 'T'
            @infer_type atom[2][0]
          else
            new Type wrapper.return_type
        else
          assert false
      when 'bop'
        switch atom[1]
          when '+', '-', '*', '/', '**'
            @infer_type atom[2]
          when '<', '>', '==', '<=', '>='
            new Type 'bool'
      when 'neg'
        @infer_type atom[1]
      when 'list'
        new Type 'vec' + (@list_length atom)
      when 'vec'
        new Type 'vec' + atom[1]
      when 'swizzle'
        assert @infer_type(atom[2]).name[...3] == 'vec'
        if atom[1].length == 1
          new Type 'float'
        else
          new Type 'vec' + atom[1].length
      else
        console.log 'Unknown atom to infer_type:', atom
        assert false

  list_length: (list) ->
    types = (@infer_type elem for elem in list[1..])
    length = 0
    for type in types
      if /^vec[0-9]+$/.test type.name
        length += parseInt type.name[3...]
      else if type.name == 'float'
        length += 1
      else
        assert false
    length

  parse_block: (init='{') ->
    if init != '{'
      return new Block @, [init]
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
      (val[0] == 'swizzle' and val[1][0] == 'var') or
      val[0] == 'list'
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

  fold: (element) ->
    all_constant = (element) ->
      if element.is_array and element.length > 1
        switch element[0]
          when 'val', 'call'
            false
        for sub in element
          if not all_constant(sub)
            return false
        true
      else
        true
    if not element.is_array or not all_constant element
      element
    else
      switch element[0]
        when 'bop'
          [a, b] = element[2...]
          if a[element[1]]
            a[element[1]](b)
          else
            element
        when 'neg'
          if element[1].neg
            element[1].neg()
          else
            element
        else
          element

  assign: (name) ->
    value = @stack.pop()
    if not @globals[name] and not @locals[name] and not builtin_vars[name]
      @locals[name] = @infer_type value
    @effectstack.top().push ['assign', name, value]
  macro_assign: (name) ->
    @macrolocals[name] = @stack.pop()
  macro_store: (name) ->
    if @is_stored @stack.top()
      @macrolocals[name] = @stack.pop()
    else
      @assign name

  swizzle: (swizzle) ->
    if swizzle.indexOf('.') != -1
      val = @ensure_stored pop=true
      swizzles = swizzle.split '.'
      for swizzle in swizzles
        @stack.push ['swizzle', swizzle, val]
    else
      @stack.push ['swizzle', swizzle, @stack.pop()]

  avec: () ->
    list = @stack.pop()
    assert list[0] == 'list'
    size = @list_length list
    @stack.push ['vec', size].concat list[1...]

  word_size: () ->
    val = @stack.pop()
    if val[0] == 'list'
      @stack.push new Float val.length-1
    else
      type = @infer_type val
      assert type[...3] == 'vec'
      @stack.push new Float parseInt type[3...]

  reduce: (block) ->
    list = @stack.pop()
    if list[0] != 'list'
      @stack.push list
      @veca()
      list = @stack.pop()

    tatoms = []
    for val, i in list[1...]
      tname = @tempname()
      @macrolocals[tname] = val
      tatoms.push tname
      if i != 0
        tatoms = tatoms.concat block.atoms
    @tokens.insert tatoms

  map: (block) ->
    list = @stack.pop()
    if list[0] != 'list'
      @stack.push list
      @veca()
      list = @stack.pop()

    tatoms = ['[']
    for val, i in list[1...]
      tname = @tempname()
      @macrolocals[tname] = val
      tatoms.push tname
      tatoms = tatoms.concat block.atoms
    @tokens.insert tatoms.concat [']']

  range_literal: (token) ->
    token = token.split(/:/)
    if token.length == 1
      if token[0][0] == '+'
        tokens = "0 #{token[0][1...]} 1 inclusive-range"
      else
        tokens = "0 #{token[0]} 1 range"
    else if token.length == 2
      if token[1][0] == '+'
        token[1] = token[1][1...]
        tokens = "#{token.join ' '} 1 inclusive-range"
      else
        tokens = "#{token.join ' '} 1 range"
    else
      if token[1][0] == '+'
        token[1] = token[1][1...]
        tokens = "#{token.join ' '} inclusive-range"
      else
        tokens = "#{token.join ' '} range"
    @tokens.insert @tokenize tokens

  word_range: () ->
    [start, end, step] = @stack.pop 3
    list = ['list']
    for num in [toNative(start)...toNative(end)] by toNative(step)
      list.push new Float num
    @stack.push list

  'word_inclusive-range': () ->
    [start, end, step] = @stack.pop 3
    list = ['list']
    for num in [toNative(start)..toNative(end)] by toNative(step)
      list.push new Float num
    @stack.push list

  'word_+': () -> @stack.push @fold ['bop', '+'].concat @stack.pop 2
  'word_-': () -> @stack.push @fold ['bop', '-'].concat @stack.pop 2
  'word_*': () -> @stack.push @fold ['bop', '*'].concat @stack.pop 2
  'word_/': () -> @stack.push @fold ['bop', '/'].concat @stack.pop 2
  'word_**': () -> @stack.push @fold ['bop', '**'].concat @stack.pop 2
  'word_<': () -> @stack.push @fold ['bop', '<'].concat @stack.pop 2
  'word_>': () -> @stack.push @fold ['bop', '>'].concat @stack.pop 2
  'word_==': () -> @stack.push @fold ['bop', '=='].concat @stack.pop 2
  word_neg: () -> @stack.push @fold ['neg', @stack.pop()]

  push_block: () ->
    nblock = ['block']
    @effectstack.top().push nblock
    @effectstack.push nblock
    nblock

  word_times: () ->
    [block, count] = @stack.pop 2
    tname = @tempname()

    @effectstack.top().push ['for', tname, new Int(0), count]
    @push_block()
    @stack.push '__term__'
    @stack.push ['var', tname]
    @locals[tname] = 'int'

    @tokens.insert block.atoms.concat ['__endblock']

  word_mtimes: () ->
    [block, count] = @stack.pop 2
    tokens = []
    for i in [0...toNative count]
      tokens = tokens.concat [new Int i].concat block.atoms
    @tokens.insert tokens

  word_when: () ->
    [block, cond] = @stack.pop 2
    @effectstack.top().push ['if', cond]
    @push_block()
    @stack.push '__term__'

    @tokens.insert block.atoms.concat ['__endblock']

  word_if: () ->
    [if_, else_, cond] = @stack.pop 3
    @effectstack.top().push ['if', cond]
    @push_block()
    @stack.push else_
    @stack.push '__term__'
    @tokens.insert if_.atoms.concat ['__endblock', '__else']

  word___else: () ->
    else_ = @stack.pop()
    @effectstack.top().push ['else']
    @push_block()
    @stack.push '__term__'
    @tokens.insert else_.atoms.concat ['__endblock']

  word___endblock: () ->
    @effectstack.pop()
    while @stack.pop() != '__term__'
      ;

  word_call: () ->
    block = @stack.pop()
    @tokens.insert block.atoms

  word___startclosure: () ->
    block = @tokens.consume()
    block.invoke()
  word___endclosure: () ->
    @blockstack.pop().end()

  word_return: () ->
    @effectstack.top().push ['return', @stack.pop()]
  'word_return-nil': () ->
    @effectstack.top().push ['return']
  word_continue: () ->
    @effectstack.top().push ['continue']
  word_break: () ->
    @effectstack.top().push ['break']

  word_swap: () ->
    [a, b] = @stack.pop 2
    @stack.push b
    @stack.push a
  word_drop: () ->
    @stack.pop()
  word_take: () ->
    offset = toNative @stack.pop()
    @stack.push @stack.retrieve offset
  word_dup: () ->
    @stack.push @ensure_stored()

  'word_[': () ->
    @stackstack.push @stack
    @stack = []
  'word_]': () ->
    list = ['list'].concat @stack
    @stack = @stackstack.pop()
    @stack.push list

  word_uniform: () ->
    @stack.top().add_attribute 'uniform'

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
    @build_head()
    for name of @compiler.words
      continue if name[0] == '$'

      @build_word name
    console.log @code

  build_head: () ->


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
      return effect.toString()
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
  build_continue: () -> 'continue'
  build_break: () -> 'break'

  build_call: ([_, name, args]) ->
    "#{name}(#{(@build_one arg for arg in args).join ', '})"

  build_bop: ([_, op, left, right]) ->
    if op == '**'
      @build_pow [op, left, right]
    else
      "(#{@build_one left} #{op} #{@build_one right})"
  build_neg: ([_, val]) ->
    "-#{@build_one val}"

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
    if @vars_defined.include(name[0]) or name[0][...3] == 'gl_'
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

  build_vec: (effect) ->
    "[#{(@build_one elem for elem in effect[2...]).join ', '}]"

  build_swizzle: ([_, swizzle, vec]) ->
    "swizzle('#{swizzle}', #{@build_one vec})"

  build_pow: ([_, left, right]) ->
    "Math.pow(#{@build_one left}, #{@build_one right})"

class GLSLCompiler extends CodeBuilder
  build_head: () ->
    for name, type of @compiler.globals
      continue if name[0] == '$'
      @pushstmt "#{type.toString()} #{name}"

  build_word: (name) ->
    super
    @pushblock "#{@compiler.words[name].return_type} #{name}(#{(arg[1] + ' ' + arg[0] for arg in @compiler.words[name].args).join ', '})"
    @build_all @compiler.words[name].effects
    @popblock()

  build_assign: ([_, name, value]) ->
    if @vars_defined.include(name[0]) or name[0][...3] == 'gl_'
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

  build_vec: (effect) ->
    "vec#{effect[1]}(#{(@build_one elem for elem in effect[2...]).join ', '})"

  build_swizzle: ([_, swizzle, vec]) ->
    "#{@build_one vec}.#{swizzle}"

  build_pow: ([_, left, right]) ->
    "pow(#{@build_one left}, #{@build_one right})"

code = """
$[1:+100] !\\+ 2 ** swap /{ 2 ** } \\+ - =temp
"""

basedir = __dirname.split('/')[...-1].join '/'
fs.readFile basedir + '/wrappers.sfr', (err, data) ->
  code = data+'\n'+code
  console.log '// GLSL'
  new GLSLCompiler().compile code
  #console.log '// Javascript'
  #new JSCompiler().compile code
