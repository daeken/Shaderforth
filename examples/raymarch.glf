:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

: rotationmat ( axis:vec3 angle:float -> mat4 )
	axis normalize =axis
	angle sin =s
	angle cos =c
	1.0 c - =>oc

	[
		oc axis .x * axis .x * c +           , oc axis .x * axis .y * axis .z s * - , oc axis .z * axis .x * axis .y s * + , 0.0
		oc axis .x * axis .y * axis .z s * + , oc axis .y * axis .y * c +           , oc axis .y * axis .z * axis .x s * - , 0.0
		oc axis .z * axis .x * axis .y s * - , oc axis .y * axis .z * axis .x s * + , oc axis .z * axis .z * c +           , 0.0
		0.0                                  , 0.0                                  , 0.0                                  , 1.0
	]m
;

:m rotate ( p axis angle ) [ p 1.0 ]v axis angle rotationmat * .xyz ;

:m sphere ( p s ) p length s - ;
:m torus ( p t ) [ p .xy length t .x - p .z ]v length t .y - ;
: box ( p:vec3 b:vec3 -> float )
	p abs b - =d
	d .x.y.z max max 0.0 min
	d 0.0 max length +
;

:m union \min ;
:m matunion \{ ( a b ) a b a .x b .x < select } ;
:m subtract \{ swap negate swap max } ;
:m intersect \max ;
:m repeat ( block p c ) p c mod 0.5 c * - *block ;

:m time iGlobalTime ;

:m tx ( p t ) p [ t   0.0 0.0 ]v + ;
:m ty ( p t ) p [ 0.0 t   0.0 ]v + ;
:m tz ( p t ) p [ 0.0 0.0 t   ]v + ;

: scene ( p:vec3 -> vec2 )
	p 5.0 tz =p

	[
		[ p [ -0.5 -0.7 0.4 ]v + [ 0.0 1.2 5.0 ]v iGlobalTime rotate [ 0.3 0.3 0.5 ]v box 0.0 ]v
		[ p [ 0.2 0.3 0.4 ]v + [ 1.0 0.5 0.2 ]v iGlobalTime rotate [ 0.4 0.4 0.5 ]v box 1.0 ]v
		[ p [ time sin time 0.5 * cos time 1.7 * sin ]v + 0.4 sphere 2.0 ]v
	] matunion
;

: material ( id:float -> vec4 )
	[
		id 0.0 == { [ 0.8 0.0 0.0 30.0 ]v return }
		id 1.0 == { [ 0.0 0.8 0.0 50.0 ]v return }
		id 2.0 == { [ 0.0 0.0 0.8 10.0 ]v return }
		{ [ 1.0 1.0 0.0 0.0 ]v return }
	] cond
;

0.0001 =>eps

:m getnormal ( p )
	[
		p [ eps 0.0 0.0 ]v + scene .x
		p [ eps negate 0.0 0.0 ]v + scene .x -
		p [ 0.0 eps 0.0 ]v + scene .x
		p [ 0.0 eps negate 0.0 ]v + scene .x -
		p [ 0.0 0.0 eps ]v + scene .x
		p [ 0.0 0.0 eps negate ]v + scene .x -
	]v normalize
;

gl_FragCoord .xy 2.0 * iResolution .xy - iResolution .y / =pos

3.0 =>focus
20.0 =>far

[ 0.0 0.0 5.0 ]v =cp
[ 0.0 0.0 0.0 ]v =>ct

ct cp - normalize =>cd
[ 0.0 0.5 0.0 ]v =cu
cd cu cross =>cs
cs pos .x * cu pos .y * + cd focus * + normalize =dir

cp =ray
0.0 =dist

[ 0.0 0.0 ]v =s
[ 0.0 0.0 0.0 ]v =c

10 =>iters
{
	float iters float / 1.0 swap - 2.0 pow =level

	{
		ray scene =s
		dist s .x + =dist
		ray dir s .x * + =ray

		{ break } s .x 0.01 < when
		{ far =dist } dist far > when
	} 40 times

	{
		ray getnormal =normal

		[ 0.0 8.0 5.0 ]v =>lightpos
		[ 1.0 1.0 1.0 ]v =>lightcolor
		lightpos ray - normalize =ivec
		ivec normal dot =incidence
		{ 0.0 =incidence } incidence 0.0 < when
		lightcolor incidence * =>diffuse
		0.1 =>ambient

		s .y material =mat

		0.0 =specular
		lightpos ray - normalize =>lightdir
		{
			lightdir cp + normalize normal dot
			0.0 max mat .w pow
			lightpos ray - length / =specular
		} mat .w 0.0 != normal lightdir dot 0.0 >= and when

		c mat .rgb diffuse ambient + specular + * level * + =c

		{
			dir normal reflect normalize =dir
			ray dir + =ray
			ray =cp
		} {
			break
		} mat .w 0.0 > if
	} {
		break
	} dist far < if
} iters times

[ c 1.0 ]v =gl_FragColor
