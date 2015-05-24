// vec2 operators
function vec2_add_vec2(a, b) {
	return [a[0] + b[0], a[1] + b[1]];
}
function vec2_add_float(a, b) {
	return [a[0] + b, a[1] + b];
}
function float_add_vec2(a, b) {
	return [a + b[0], a + b[1]];
}
function vec2_sub_vec2(a, b) {
	return [a[0] - b[0], a[1] - b[1]];
}
function vec2_sub_float(a, b) {
	return [a[0] - b, a[1] - b];
}
function float_sub_vec2(a, b) {
	return [a - b[0], a - b[1]];
}
function vec2_mul_vec2(a, b) {
	return [a[0] * b[0], a[1] * b[1]];
}
function vec2_mul_float(a, b) {
	return [a[0] * b, a[1] * b];
}
function float_mul_vec2(a, b) {
	return [a * b[0], a * b[1]];
}
function vec2_div_vec2(a, b) {
	return [a[0] / b[0], a[1] / b[1]];
}
function vec2_div_float(a, b) {
	return [a[0] / b, a[1] / b];
}
function float_div_vec2(a, b) {
	return [a / b[0], a / b[1]];
}
function vec2_pow_vec2(a, b) {
	return [Math.pow(a[0], b[0]), Math.pow(a[1], b[1])];
}
function vec2_pow_float(a, b) {
	return [Math.pow(a[0], b), Math.pow(a[1], b)];
}
function float_pow_vec2(a, b) {
	return [Math.pow(a, b[0]), Math.pow(a, b[1])];
}
function vec2_lt_vec2(a, b) {
	return [a[0] < b[0], a[1] < b[1]];
}
function vec2_lt_float(a, b) {
	return [a[0] < b, a[1] < b];
}
function float_lt_vec2(a, b) {
	return [a < b[0], a < b[1]];
}
function vec2_gt_vec2(a, b) {
	return [a[0] > b[0], a[1] > b[1]];
}
function vec2_gt_float(a, b) {
	return [a[0] > b, a[1] > b];
}
function float_gt_vec2(a, b) {
	return [a > b[0], a > b[1]];
}
function vec2_lte_vec2(a, b) {
	return [a[0] <= b[0], a[1] <= b[1]];
}
function vec2_lte_float(a, b) {
	return [a[0] <= b, a[1] <= b];
}
function float_lte_vec2(a, b) {
	return [a <= b[0], a <= b[1]];
}
function vec2_gte_vec2(a, b) {
	return [a[0] >= b[0], a[1] >= b[1]];
}
function vec2_gte_float(a, b) {
	return [a[0] >= b, a[1] >= b];
}
function float_gte_vec2(a, b) {
	return [a >= b[0], a >= b[1]];
}
function vec2_eq_vec2(a, b) {
	return [a[0] == b[0], a[1] == b[1]];
}
function vec2_eq_float(a, b) {
	return [a[0] == b, a[1] == b];
}
function float_eq_vec2(a, b) {
	return [a == b[0], a == b[1]];
}
function vec2_neq_vec2(a, b) {
	return [a[0] != b[0], a[1] != b[1]];
}
function vec2_neq_float(a, b) {
	return [a[0] != b, a[1] != b];
}
function float_neq_vec2(a, b) {
	return [a != b[0], a != b[1]];
}

// vec3 operators
function vec3_add_vec3(a, b) {
	return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}
function vec3_add_float(a, b) {
	return [a[0] + b, a[1] + b, a[2] + b];
}
function float_add_vec3(a, b) {
	return [a + b[0], a + b[1], a + b[2]];
}
function vec3_sub_vec3(a, b) {
	return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}
function vec3_sub_float(a, b) {
	return [a[0] - b, a[1] - b, a[2] - b];
}
function float_sub_vec3(a, b) {
	return [a - b[0], a - b[1], a - b[2]];
}
function vec3_mul_vec3(a, b) {
	return [a[0] * b[0], a[1] * b[1], a[2] * b[2]];
}
function vec3_mul_float(a, b) {
	return [a[0] * b, a[1] * b, a[2] * b];
}
function float_mul_vec3(a, b) {
	return [a * b[0], a * b[1], a * b[2]];
}
function vec3_div_vec3(a, b) {
	return [a[0] / b[0], a[1] / b[1], a[2] / b[2]];
}
function vec3_div_float(a, b) {
	return [a[0] / b, a[1] / b, a[2] / b];
}
function float_div_vec3(a, b) {
	return [a / b[0], a / b[1], a / b[2]];
}
function vec3_pow_vec3(a, b) {
	return [Math.pow(a[0], b[0]), Math.pow(a[1], b[1]), Math.pow(a[2], b[2])];
}
function vec3_pow_float(a, b) {
	return [Math.pow(a[0], b), Math.pow(a[1], b), Math.pow(a[2], b)];
}
function float_pow_vec3(a, b) {
	return [Math.pow(a, b[0]), Math.pow(a, b[1]), Math.pow(a, b[2])];
}
function vec3_lt_vec3(a, b) {
	return [a[0] < b[0], a[1] < b[1], a[2] < b[2]];
}
function vec3_lt_float(a, b) {
	return [a[0] < b, a[1] < b, a[2] < b];
}
function float_lt_vec3(a, b) {
	return [a < b[0], a < b[1], a < b[2]];
}
function vec3_gt_vec3(a, b) {
	return [a[0] > b[0], a[1] > b[1], a[2] > b[2]];
}
function vec3_gt_float(a, b) {
	return [a[0] > b, a[1] > b, a[2] > b];
}
function float_gt_vec3(a, b) {
	return [a > b[0], a > b[1], a > b[2]];
}
function vec3_lte_vec3(a, b) {
	return [a[0] <= b[0], a[1] <= b[1], a[2] <= b[2]];
}
function vec3_lte_float(a, b) {
	return [a[0] <= b, a[1] <= b, a[2] <= b];
}
function float_lte_vec3(a, b) {
	return [a <= b[0], a <= b[1], a <= b[2]];
}
function vec3_gte_vec3(a, b) {
	return [a[0] >= b[0], a[1] >= b[1], a[2] >= b[2]];
}
function vec3_gte_float(a, b) {
	return [a[0] >= b, a[1] >= b, a[2] >= b];
}
function float_gte_vec3(a, b) {
	return [a >= b[0], a >= b[1], a >= b[2]];
}
function vec3_eq_vec3(a, b) {
	return [a[0] == b[0], a[1] == b[1], a[2] == b[2]];
}
function vec3_eq_float(a, b) {
	return [a[0] == b, a[1] == b, a[2] == b];
}
function float_eq_vec3(a, b) {
	return [a == b[0], a == b[1], a == b[2]];
}
function vec3_neq_vec3(a, b) {
	return [a[0] != b[0], a[1] != b[1], a[2] != b[2]];
}
function vec3_neq_float(a, b) {
	return [a[0] != b, a[1] != b, a[2] != b];
}
function float_neq_vec3(a, b) {
	return [a != b[0], a != b[1], a != b[2]];
}

// vec4 operators
function vec4_add_vec4(a, b) {
	return [a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]];
}
function vec4_add_float(a, b) {
	return [a[0] + b, a[1] + b, a[2] + b, a[3] + b];
}
function float_add_vec4(a, b) {
	return [a + b[0], a + b[1], a + b[2], a + b[3]];
}
function vec4_sub_vec4(a, b) {
	return [a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3]];
}
function vec4_sub_float(a, b) {
	return [a[0] - b, a[1] - b, a[2] - b, a[3] - b];
}
function float_sub_vec4(a, b) {
	return [a - b[0], a - b[1], a - b[2], a - b[3]];
}
function vec4_mul_vec4(a, b) {
	return [a[0] * b[0], a[1] * b[1], a[2] * b[2], a[3] * b[3]];
}
function vec4_mul_float(a, b) {
	return [a[0] * b, a[1] * b, a[2] * b, a[3] * b];
}
function float_mul_vec4(a, b) {
	return [a * b[0], a * b[1], a * b[2], a * b[3]];
}
function vec4_div_vec4(a, b) {
	return [a[0] / b[0], a[1] / b[1], a[2] / b[2], a[3] / b[3]];
}
function vec4_div_float(a, b) {
	return [a[0] / b, a[1] / b, a[2] / b, a[3] / b];
}
function float_div_vec4(a, b) {
	return [a / b[0], a / b[1], a / b[2], a / b[3]];
}
function vec4_pow_vec4(a, b) {
	return [Math.pow(a[0], b[0]), Math.pow(a[1], b[1]), Math.pow(a[2], b[2]), Math.pow(a[3], b[3])];
}
function vec4_pow_float(a, b) {
	return [Math.pow(a[0], b), Math.pow(a[1], b), Math.pow(a[2], b), Math.pow(a[3], b)];
}
function float_pow_vec4(a, b) {
	return [Math.pow(a, b[0]), Math.pow(a, b[1]), Math.pow(a, b[2]), Math.pow(a, b[3])];
}
function vec4_lt_vec4(a, b) {
	return [a[0] < b[0], a[1] < b[1], a[2] < b[2], a[3] < b[3]];
}
function vec4_lt_float(a, b) {
	return [a[0] < b, a[1] < b, a[2] < b, a[3] < b];
}
function float_lt_vec4(a, b) {
	return [a < b[0], a < b[1], a < b[2], a < b[3]];
}
function vec4_gt_vec4(a, b) {
	return [a[0] > b[0], a[1] > b[1], a[2] > b[2], a[3] > b[3]];
}
function vec4_gt_float(a, b) {
	return [a[0] > b, a[1] > b, a[2] > b, a[3] > b];
}
function float_gt_vec4(a, b) {
	return [a > b[0], a > b[1], a > b[2], a > b[3]];
}
function vec4_lte_vec4(a, b) {
	return [a[0] <= b[0], a[1] <= b[1], a[2] <= b[2], a[3] <= b[3]];
}
function vec4_lte_float(a, b) {
	return [a[0] <= b, a[1] <= b, a[2] <= b, a[3] <= b];
}
function float_lte_vec4(a, b) {
	return [a <= b[0], a <= b[1], a <= b[2], a <= b[3]];
}
function vec4_gte_vec4(a, b) {
	return [a[0] >= b[0], a[1] >= b[1], a[2] >= b[2], a[3] >= b[3]];
}
function vec4_gte_float(a, b) {
	return [a[0] >= b, a[1] >= b, a[2] >= b, a[3] >= b];
}
function float_gte_vec4(a, b) {
	return [a >= b[0], a >= b[1], a >= b[2], a >= b[3]];
}
function vec4_eq_vec4(a, b) {
	return [a[0] == b[0], a[1] == b[1], a[2] == b[2], a[3] == b[3]];
}
function vec4_eq_float(a, b) {
	return [a[0] == b, a[1] == b, a[2] == b, a[3] == b];
}
function float_eq_vec4(a, b) {
	return [a == b[0], a == b[1], a == b[2], a == b[3]];
}
function vec4_neq_vec4(a, b) {
	return [a[0] != b[0], a[1] != b[1], a[2] != b[2], a[3] != b[3]];
}
function vec4_neq_float(a, b) {
	return [a[0] != b, a[1] != b, a[2] != b, a[3] != b];
}
function float_neq_vec4(a, b) {
	return [a != b[0], a != b[1], a != b[2], a != b[3]];
}

function vec2(x) {
	return [x, x];
}
function vec3(x) {
	return [x, x, x];
}
function vec4(x) {
	return [x, x, x, x];
}

function abs_float(x) {
	return Math.abs(x);
}
function abs_vec2(x) {
	return [
		Math.abs(x[0]), 
		Math.abs(x[1])
	];
}
function abs_vec3(x) {
	return [
		Math.abs(x[0]), 
		Math.abs(x[1]), 
		Math.abs(x[2])
	];
}
function abs_vec4(x) {
	return [
		Math.abs(x[0]), 
		Math.abs(x[1]), 
		Math.abs(x[2]), 
		Math.abs(x[3])
	];
}

function clamp_float_float_float(x, minVal, maxVal) {
	return Math.min(Math.max(x, minVal), maxVal);
}
function clamp_vec2_float_float(x, minVal, maxVal) {
	return [
		clamp_float_float_float(x[0], minVal, maxVal), 
		clamp_float_float_float(x[1], minVal, maxVal)
	];
}
function clamp_vec3_float_float(x, minVal, maxVal) {
	return [
		clamp_float_float_float(x[0], minVal, maxVal), 
		clamp_float_float_float(x[1], minVal, maxVal), 
		clamp_float_float_float(x[2], minVal, maxVal)
	];
}
function clamp_vec4_float_float(x, minVal, maxVal) {
	return [
		clamp_float_float_float(x[0], minVal, maxVal), 
		clamp_float_float_float(x[1], minVal, maxVal), 
		clamp_float_float_float(x[2], minVal, maxVal), 
		clamp_float_float_float(x[3], minVal, maxVal)
	];
}

function mix_float_float_float(x, y, a) {
	return x * (1 - a) + y * a;
}
function mix_vec2_vec2_float(x, y, a) {
	return vec2_add_vec2(vec2_mul_float(x, 1-a), vec2_mul_float(y, a));
}
function mix_vec3_vec3_float(x, y, a) {
	return vec3_add_vec3(vec3_mul_float(x, 1-a), vec3_mul_float(y, a));
}
function mix_vec4_vec4_float(x, y, a) {
	return vec3_add_vec4(vec4_mul_float(x, 1-a), vec4_mul_float(y, a));
}

function mod_float_float(x, y) {
	return x - y * Math.floor(x / y);
}
function mod_vec2_float(x, y) {
	return [
		mod_float_float(x[0], y), 
		mod_float_float(x[1], y)
	];
}
function mod_vec3_float(x, y) {
	return [
		mod_float_float(x[0], y), 
		mod_float_float(x[1], y), 
		mod_float_float(x[2], y)
	];
}
function mod_vec4_float(x, y) {
	return [
		mod_float_float(x[0], y), 
		mod_float_float(x[1], y), 
		mod_float_float(x[2], y), 
		mod_float_float(x[3], y)
	];
}

function sin_float(x) {
	return Math.sin(x);
}
function sin_vec2(x) {
	return [
		Math.sin(x[0]), 
		Math.sin(x[1])
	];
}
function sin_vec3(x) {
	return [
		Math.sin(x[0]), 
		Math.sin(x[1]), 
		Math.sin(x[2])
	];
}
function sin_vec4(x) {
	return [
		Math.sin(x[0]), 
		Math.sin(x[1]), 
		Math.sin(x[2]), 
		Math.sin(x[3])
	];
}
