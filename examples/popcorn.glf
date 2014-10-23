:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
;
:m time iGlobalTime ;
:m iter #500 ;
:m time-step 1 time sin 1 + / ;
:m tmod dup time + sin swap 30 / time + cos * ;
:m pnoise ( i )
	[
		i 4801 * p .x * 2 ** time * sin
		i 5077 * p .y * time + cos
	] \*
;

:m count-hits ( p f g )
	0 =count
	( [
		37 pnoise
		741 pnoise
	] ) [ 0 0 ] dup =i =prev
	{
		[
			i .x time-step i *f * +
			i .y time-step i *g * +
		] =i
		{
			count 1 + =count
		} p abs i abs - length granularity < when
		i =prev
	} iter times
	count
;

10 iResolution length / =granularity

iResolution frag->position =p
	p
	{ ( i )
		[
			.3 tmod 1000 /
			[
				.7 tmod
				pi i .x *
			] \+ tan
		] \+ .01 *
	}
	{ ( i )
		[
			( .9 tmod 1000 / )
			[
				.2 tmod
				pi i .y *
			] \+ tan
		] \+ .01 *
	}
count-hits =hits
[
	[
		hits 100 * iGlobalTime 10 * + p length time * sin 100 * +
		1
		hits iter float / 200 *
	] hsv->rgb
	1.
] =gl_FragColor
