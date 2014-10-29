: foo ( -> float )
	$[0:+3:1] multi2 /{ =>[ x y ]
		x sin y cos *
	} \+
;

[ foo dup dup ] ->fragcolor