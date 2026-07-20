"""
math_report_notation.py

Demonstrate Unicode mathematical and scientific notation in Logduo.

Unicode symbols are ordinary text:
  - no additional import or renderer is required
  - symbols display directly in the console
  - symbols are preserved in UTF-8 log files
  - available superscript and subscript characters are limited

This example uses Unicode escape codes so each symbol can be identified
and reproduced without copying it from another source.
"""
from pathlib import Path

from logduo import log

LOG_DIR = Path.cwd() / "logs"
log.configure(log_dir_path=LOG_DIR)


# ===========================================================================
# BASIC OPERATORS AND RELATIONS
# ===========================================================================

plus_minus = "\u00b1"          # ±
minus_plus = "\u2213"           # ∓
multiplication = "\u00d7"       # ×
division = "\u00f7"             # ÷
middle_dot = "\u00b7"           # ·
fraction_slash = "\u2044"       # ⁄

approximately = "\u2248"        # ≈
not_equal = "\u2260"            # ≠
identical = "\u2261"            # ≡
proportional = "\u221d"         # ∝
less_equal = "\u2264"           # ≤
greater_equal = "\u2265"        # ≥
much_less = "\u226a"            # ≪
much_greater = "\u226b"         # ≫

infinity = "\u221e"             # ∞
square_root = "\u221a"           # √
cube_root = "\u221b"             # ∛
fourth_root = "\u221c"           # ∜
degree = "\u00b0"                # °
percent = "\u0025"               # %
per_mille = "\u2030"             # ‰


# ===========================================================================
# CALCULUS, ALGEBRA, AND GEOMETRY
# ===========================================================================

summation = "\u2211"             # ∑
product = "\u220f"               # ∏
integral = "\u222b"              # ∫
double_integral = "\u222c"       # ∬
triple_integral = "\u222d"       # ∭
contour_integral = "\u222e"      # ∮
partial = "\u2202"               # ∂
nabla = "\u2207"                 # ∇
increment = "\u2206"             # ∆
therefore = "\u2234"             # ∴
because = "\u2235"               # ∵

angle = "\u2220"                 # ∠
parallel = "\u2225"              # ∥
perpendicular = "\u27c2"         # ⟂
congruent = "\u2245"             # ≅
similar = "\u223c"               # ∼

left_arrow = "\u2190"            # ←
right_arrow = "\u2192"           # →
up_arrow = "\u2191"              # ↑
down_arrow = "\u2193"            # ↓
left_right_arrow = "\u2194"      # ↔
implies = "\u21d2"               # ⇒
equivalent = "\u21d4"            # ⇔


# ===========================================================================
# SETS AND LOGIC
# ===========================================================================

element_of = "\u2208"            # ∈
not_element_of = "\u2209"        # ∉
contains = "\u220b"              # ∋
subset = "\u2282"                # ⊂
subset_equal = "\u2286"          # ⊆
superset = "\u2283"              # ⊃
superset_equal = "\u2287"        # ⊇
union = "\u222a"                 # ∪
intersection = "\u2229"          # ∩
empty_set = "\u2205"             # ∅
universal = "\u2200"             # ∀
exists = "\u2203"                # ∃
not_exists = "\u2204"            # ∄

logical_and = "\u2227"           # ∧
logical_or = "\u2228"            # ∨
logical_not = "\u00ac"           # ¬
true_symbol = "\u22a4"           # ⊤
false_symbol = "\u22a5"          # ⊥

natural_numbers = "\u2115"       # ℕ
integers = "\u2124"              # ℤ
rational_numbers = "\u211a"      # ℚ
real_numbers = "\u211d"          # ℝ
complex_numbers = "\u2102"       # ℂ


# ===========================================================================
# STATISTICS AND PROBABILITY
# ===========================================================================

mean = "\u03bc"                  # μ
standard_deviation = "\u03c3"    # σ
variance = "\u03c3\u00b2"        # σ²
correlation = "\u03c1"           # ρ
chi = "\u03c7"                   # χ

probability = "\u2119"           # ℙ
expected_value = "\u1d53c"       # 𝔼
approximately_normal = "\u223c"  # ∼


# ===========================================================================
# COMMON GREEK LETTERS
# ===========================================================================

alpha = "\u03b1"                 # α
beta = "\u03b2"                  # β
gamma = "\u03b3"                 # γ
delta = "\u03b4"                 # δ
epsilon = "\u03b5"               # ε
theta = "\u03b8"                 # θ
lambda_ = "\u03bb"               # λ
mu = "\u03bc"                    # μ
nu = "\u03bd"                    # ν
xi = "\u03be"                    # ξ
pi = "\u03c0"                    # π
rho = "\u03c1"                   # ρ
sigma = "\u03c3"                 # σ
tau = "\u03c4"                   # τ
phi = "\u03c6"                   # φ
chi = "\u03c7"                   # χ       # noqa  # intentionally defined twice
psi = "\u03c8"                   # ψ
omega = "\u03c9"                 # ω

capital_delta = "\u0394"         # Δ
capital_gamma = "\u0393"         # Γ
capital_lambda = "\u039b"        # Λ
capital_pi = "\u03a0"            # Π
capital_sigma = "\u03a3"         # Σ
capital_phi = "\u03a6"           # Φ
capital_psi = "\u03a8"           # Ψ
capital_omega = "\u03a9"         # Ω


# ===========================================================================
# SUPERSCRIPTS
# ===========================================================================
# Unicode does not provide a complete superscript alphabet.

super_zero = "\u2070"            # ⁰
super_one = "\u00b9"             # ¹
super_two = "\u00b2"             # ²
super_three = "\u00b3"           # ³
super_four = "\u2074"            # ⁴
super_five = "\u2075"            # ⁵
super_six = "\u2076"             # ⁶
super_seven = "\u2077"           # ⁷
super_eight = "\u2078"           # ⁸
super_nine = "\u2079"            # ⁹

super_plus = "\u207a"            # ⁺
super_minus = "\u207b"           # ⁻
super_equals = "\u207c"          # ⁼
super_left_parenthesis = "\u207d"   # ⁽
super_right_parenthesis = "\u207e"  # ⁾

super_i = "\u2071"               # ⁱ
super_n = "\u207f"               # ⁿ


# ===========================================================================
# SUBSCRIPTS
# ===========================================================================
# Unicode provides digits and only a limited selection of subscript letters.

sub_zero = "\u2080"              # ₀
sub_one = "\u2081"               # ₁
sub_two = "\u2082"               # ₂
sub_three = "\u2083"             # ₃
sub_four = "\u2084"              # ₄
sub_five = "\u2085"              # ₅
sub_six = "\u2086"               # ₆
sub_seven = "\u2087"             # ₇
sub_eight = "\u2088"             # ₈
sub_nine = "\u2089"              # ₉

sub_plus = "\u208a"              # ₊
sub_minus = "\u208b"             # ₋
sub_equals = "\u208c"            # ₌
sub_left_parenthesis = "\u208d"  # ₍
sub_right_parenthesis = "\u208e"  # ₎

sub_a = "\u2090"                 # ₐ
sub_e = "\u2091"                 # ₑ
sub_h = "\u2095"                 # ₕ
sub_i = "\u1d62"                 # ᵢ
sub_j = "\u2c7c"                 # ⱼ
sub_k = "\u2096"                 # ₖ
sub_l = "\u2097"                 # ₗ
sub_m = "\u2098"                 # ₘ
sub_n = "\u2099"                 # ₙ
sub_o = "\u2092"                 # ₒ
sub_p = "\u209a"                 # ₚ
sub_r = "\u1d63"                 # ᵣ
sub_s = "\u209b"                 # ₛ
sub_t = "\u209c"                 # ₜ
sub_x = "\u2093"                 # ₓ


# ===========================================================================
# SCIENCE AND ENGINEERING
# ===========================================================================

micro = "\u00b5"                 # µ
angstrom = "\u00c5"              # Å
ohm = "\u03a9"                   # Ω
celsius = "\u00b0C"              # °C
fahrenheit = "\u00b0F"           # °F

approximately_equal = "\u2243"   # ≃
measured_angle = "\u2221"        # ∡
wave = "\u223f"                  # ∿

male = "\u2642"                  # ♂
female = "\u2640"                # ♀

# ===========================================================================
# EXAMPLES
# ===========================================================================

log("Unicode mathematical notation")
log("-----------------------------")


# Example 1: algebra and summation

log(
    f"{summation}{sub_i}{sub_equals}{sub_one}{super_n} i "
    f"= n(n + 1) / 2"
)
# ∑ᵢ₌₁ⁿ i = n(n + 1) / 2

log(
    f"x = (\u2212b {plus_minus} {square_root}"
    f"(b{super_two} \u2212 4ac)) / 2a"
)
# x = (−b ± √(b² − 4ac)) / 2a

log(
    f"(a + b){super_two} "
    f"= a{super_two} + 2ab + b{super_two}"
)
# (a + b)² = a² + 2ab + b²


# Example 2: calculus and physics

log(f"{integral}{sub_zero}{infinity} e\u207b\u02e3 dx")
# ∫₀∞ e⁻ˣ dx

log(
    f"F = ma;  E = mc{super_two};  "
    f"v = f{lambda_};  V = IR"
)
# F = ma;  E = mc²;  v = fλ;  V = IR

log(
    f"{capital_delta}x {right_arrow} 0  "
    f"{implies} sin({theta}) / {theta} {right_arrow} 1"
)
# Δx → 0  ⇒ sin(θ) / θ → 1


# Example 3: chemistry and scientific units

log(
    f"2H{sub_two} + O{sub_two} {right_arrow} 2H{sub_two}O"
)
# 2H₂ + O₂ → 2H₂O

log(
    f"CO{sub_two};  H{sub_two}SO{sub_four};  "
    f"Na{sub_two}CO{sub_three}"
)
# CO₂;  H₂SO₄;  Na₂CO₃

log(
    f"T = 22{degree}C;  "
    f"{lambda_} = 500 nm;  "
    f"R = 10 {ohm};  "
    f"d = 1.54 {angstrom}"
)
# T = 22°C;  λ = 500 nm;  R = 10 Ω;  d = 1.54 Å


# Example 4: statistics and probability

log(
    f"{mean} = {summation}x{sub_i} / n;  "
    f"{standard_deviation}{super_two} = variance"
)
# μ = ∑xᵢ / n;  σ² = variance

log(
    f"{probability}(A {intersection} B) "
    f"= {probability}(A){probability}(B)"
)
# ℙ(A ∩ B) = ℙ(A)ℙ(B)

log(
    f"x {approximately_normal} N({mean}, "
    f"{standard_deviation}{super_two})"
)
# x ∼ N(μ, σ²)


# Example 5: sets and logic

log(
    f"x {element_of} {real_numbers};  "
    f"{natural_numbers} {subset} {integers} "
    f"{subset} {rational_numbers} "
    f"{subset} {real_numbers}"
)
# x ∈ ℝ;  ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ

log(
    f"A {intersection} B {subset_equal} A;  "
    f"A {union} {empty_set} = A"
)
# A ∩ B ⊆ A;  A ∪ ∅ = A

log(
    f"{universal}x {element_of} {real_numbers}, "
    f"x{super_two} {greater_equal} 0"
)
# ∀x ∈ ℝ, x² ≥ 0


log("Math notation example complete.")


