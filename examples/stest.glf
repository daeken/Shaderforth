:struct foo
	@float =bar
	@vec3 =baz
;

[ 0.1 [ 1.0 1.0 1.0 ]v ] foo =blah

[ blah .baz blah .bar * 1.0 ]v =gl_FragColor
