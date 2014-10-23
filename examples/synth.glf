:m slog ( n ) 1 n - 2 ** 1 swap - ;

: adsr ( off:float sample:float env:vec4 -> float )
	[
		sample
		off env .x / 0 1 clamp slog ( Attack )
		1 env .z off env .x - env .y / 0 1 clamp slog mix ( Decay + Sustain )
		1 0 off env .x.y + - env .w / 0 1 clamp slog mix ( Release )
	] \*
;

:m mono->stereo vec2 ;
:m stereo-invert ( sample ) [ sample dup neg ] ;

: synth ( time:float -> vec2 )
		time 12 mod
		tau 440 time * * sin
		[ 2 2 .5 10 ]
	adsr mono->stereo
;

:passes
	{ synth } =sound-pass
;
