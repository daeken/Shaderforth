:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

0.0 =c
{ =f c 0.01 + =c } 40 times

gl_FragCoord .xy iResolution .xy / =p

{ 1.0 =c } p .y 0.5 > when
{ 1.0 c - =c } { 1.0 =c } p .y 0.5 < if

[ c c c 1.0 ]v =gl_FragColor
