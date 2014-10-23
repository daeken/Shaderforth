:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

	{ 0 1 }
	{ 1 2 }
iGlobalTime sin 0 >= if
+ =v

: material ( id:float -> vec4 )
	[
		0 id == { [ 1 0 0 1 ]v }
		1 id == { [ 0 1 0 1 ]v }
		2 id == { [ 0 0 1 1 ]v }
		{ [ 1 0 1 1 ]v }
	] cond
;

{
	{
		0 =foo
		1 =bar
		2 =baz
	} 0 1 > when
}
{ 5 =bar } 0 2 < if
baz =v

v material =gl_FragColor