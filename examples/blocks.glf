:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@float =c
;

0 =c
{ drop c 0.01 + =c } #40 times

gl_FragCoord .xy iResolution .xy / =p

{ 1 =c } p .y 0.5 > when

:m invert 1 c - =c ;
: whiten ( ) 1 =c ;

&invert &whiten p .y 0.5 < if

: blah ( int -> int ) #1 + ;

[ #0 #1 #2 #3 ] /{ #6 + } /blah \{ + } =f

:m test #5 swap call ;

{ #1 + } test =f

[ c c c 1 ]v =gl_FragColor
