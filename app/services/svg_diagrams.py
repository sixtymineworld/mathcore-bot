"""Генератор векторних SVG-малюнків для геометричних та аналітичних задач формату НМТ.

Всі малюнки виконані у фірмовій тепло-молочній та кавовій палітрі mathcore:
- Фон креслення: теплий порцеляновий `#f4f1ec`
- Рамка та сітка: `#d6dfe5`
- Основні контури та фігури: колір `#425a68` (winter slate), товщина 2.2px
- Пастельне заливання фігур: `rgba(124, 150, 166, 0.25)`
- Пунктирні лінії (висоти, невидимі ребра, діагоналі): `stroke-dasharray="4,4"`
- Акценти (кути, дотичні, точки): `#7c96a6` (slate blue)
- Шрифти підписів: вершини та латиниця — 'Apple Garamond' / 'EB Garamond'; розміри, координати та цифри — 'Taktika Sans' / 'Onest'
"""


def diagram_right_trapezoid(
    bc: int = 7,
    cd: int = 10,
    angle_d: int = 60,
    ad: int | None = None,
    ch: int | None = None,
) -> str:
    """Креслення прямокутної трапеції ABCD з висотою CH."""
    return f"""<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Трапеція -->
  <polygon points="50,180 50,65 170,65 310,180" fill="rgba(124, 150, 166, 0.16)" stroke="#425a68" stroke-width="2.2" stroke-linejoin="round"/>
  <!-- Висота CH -->
  <line x1="170" y1="65" x2="170" y2="180" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Символи прямого кута -->
  <rect x="50" y="166" width="14" height="14" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <rect x="50" y="65" width="14" height="14" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <rect x="156" y="166" width="14" height="14" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <!-- Дуга кута D -->
  <path d="M 285,180 A 25 25 0 0 0 293,166" fill="none" stroke="#7c96a6" stroke-width="2"/>
  <text x="270" y="172" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="700" fill="#425a68">{angle_d}°</text>
  <!-- Вершини -->
  <text x="30" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">A</text>
  <text x="30" y="60" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">B</text>
  <text x="170" y="52" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">C</text>
  <text x="320" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">D</text>
  <text x="165" y="198" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">H</text>
  <!-- Розміри -->
  <text x="105" y="58" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">BC = {bc}</text>
  <text x="250" y="115" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">CD = {cd}</text>
  <!-- Точки вершин -->
  <circle cx="50" cy="180" r="3.5" fill="#425a68"/>
  <circle cx="50" cy="65" r="3.5" fill="#425a68"/>
  <circle cx="170" cy="65" r="3.5" fill="#425a68"/>
  <circle cx="310" cy="180" r="3.5" fill="#425a68"/>
  <circle cx="170" cy="180" r="3" fill="#425a68"/>
</svg>"""


def diagram_right_triangle_altitude(ad: int = 9, db: int = 16, cd: int = 12) -> str:
    """Креслення прямокутного трикутника ABC з висотою CD, опущеною на гіпотенузу."""
    return f"""<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Трикутник ABC -->
  <polygon points="40,180 150,55 330,180" fill="rgba(124, 150, 166, 0.16)" stroke="#425a68" stroke-width="2.2" stroke-linejoin="round"/>
  <!-- Висота CD -->
  <line x1="150" y1="55" x2="150" y2="180" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Прямий кут у точці D -->
  <rect x="150" y="166" width="14" height="14" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <!-- Прямий кут у точці C (повернутий) -->
  <path d="M 141,66 L 150,74 L 159,64" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <!-- Вершини -->
  <text x="22" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">A</text>
  <text x="145" y="42" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">C</text>
  <text x="338" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">B</text>
  <text x="145" y="198" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">D</text>
  <!-- Розміри проекцій -->
  <text x="85" y="198" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">AD = {ad}</text>
  <text x="225" y="198" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">DB = {db}</text>
  <!-- Точки -->
  <circle cx="40" cy="180" r="3.5" fill="#425a68"/>
  <circle cx="150" cy="55" r="3.5" fill="#425a68"/>
  <circle cx="330" cy="180" r="3.5" fill="#425a68"/>
  <circle cx="150" cy="180" r="3" fill="#425a68"/>
</svg>"""


def diagram_circle_tangents(r: int = 8, angle_m: int = 60, dist: int = 16) -> str:
    """Креслення кола з центром O та дотичними MA і MB з зовнішньої точки M."""
    return f"""<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Коло -->
  <circle cx="230" cy="115" r="68" fill="rgba(124, 150, 166, 0.12)" stroke="#425a68" stroke-width="2.2"/>
  <!-- Дотичні MA та MB -->
  <line x1="50" y1="115" x2="196" y2="56" stroke="#425a68" stroke-width="2.2"/>
  <line x1="50" y1="115" x2="196" y2="174" stroke="#425a68" stroke-width="2.2"/>
  <!-- Радіуси OA та OB -->
  <line x1="230" y1="115" x2="196" y2="56" stroke="#8c6239" stroke-width="1.8"/>
  <line x1="230" y1="115" x2="196" y2="174" stroke="#8c6239" stroke-width="1.8"/>
  <!-- Лінія центрів MO -->
  <line x1="50" y1="115" x2="230" y2="115" stroke="#425a68" stroke-width="1.5" stroke-dasharray="4,4"/>
  <!-- Прямі кути дотику -->
  <path d="M 189,68 L 199,74 L 205,62" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <path d="M 189,162 L 199,156 L 205,168" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <!-- Дуга кута M -->
  <path d="M 85,105 A 35 35 0 0 1 85,125" fill="none" stroke="#7c96a6" stroke-width="2"/>
  <text x="95" y="119" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="700" fill="#425a68">{angle_m}°</text>
  <!-- Підписи -->
  <text x="30" y="120" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">M</text>
  <text x="195" y="45" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">A</text>
  <text x="195" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">B</text>
  <text x="240" y="120" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">O</text>
  <text x="220" y="80" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">r = {r}</text>
  <!-- Точки -->
  <circle cx="50" cy="115" r="3.5" fill="#425a68"/>
  <circle cx="196" cy="56" r="3.5" fill="#425a68"/>
  <circle cx="196" cy="174" r="3.5" fill="#425a68"/>
  <circle cx="230" cy="115" r="3.5" fill="#425a68"/>
</svg>"""


def diagram_quadrangular_pyramid(base_a: int = 12, height: int = 8, apothem: int = 10) -> str:
    """3D креслення правильної чотирикутної піраміди SABCD з висотою SO та апофемою SK."""
    return f"""<svg viewBox="0 0 380 250" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="234" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Основа: невидимі ребра AD та CD -->
  <line x1="70" y1="180" x2="160" y2="135" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <line x1="160" y1="135" x2="300" y2="145" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Основа: видимі грані та заливка -->
  <polygon points="70,180 210,210 300,145 160,135" fill="rgba(124, 150, 166, 0.12)" stroke="none"/>
  <line x1="70" y1="180" x2="210" y2="210" stroke="#425a68" stroke-width="2.2"/>
  <line x1="210" y1="210" x2="300" y2="145" stroke="#425a68" stroke-width="2.2"/>
  <!-- Бічні ребра -->
  <line x1="185" y1="35" x2="70" y2="180" stroke="#425a68" stroke-width="2.2"/>
  <line x1="185" y1="35" x2="210" y2="210" stroke="#425a68" stroke-width="2.2"/>
  <line x1="185" y1="35" x2="300" y2="145" stroke="#425a68" stroke-width="2.2"/>
  <line x1="185" y1="35" x2="160" y2="135" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Діагоналі основи AC і BD -->
  <line x1="70" y1="180" x2="300" y2="145" stroke="#7c96a6" stroke-width="1.2" stroke-dasharray="3,3"/>
  <line x1="210" y1="210" x2="160" y2="135" stroke="#7c96a6" stroke-width="1.2" stroke-dasharray="3,3"/>
  <!-- Висота SO -->
  <line x1="185" y1="35" x2="185" y2="167" stroke="#425a68" stroke-width="2" stroke-dasharray="4,4"/>
  <!-- Апофема SK (K середина CD) -->
  <line x1="185" y1="35" x2="230" y2="140" stroke="#8c6239" stroke-width="2" stroke-dasharray="4,4"/>
  <line x1="185" y1="167" x2="230" y2="140" stroke="#7c96a6" stroke-width="1.5" stroke-dasharray="3,3"/>
  <!-- Підписи -->
  <text x="182" y="26" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">S</text>
  <text x="50" y="190" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">A</text>
  <text x="210" y="228" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">B</text>
  <text x="310" y="150" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">C</text>
  <text x="145" y="130" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">D</text>
  <text x="175" y="180" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">O</text>
  <text x="235" y="135" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#8c6239">K</text>
  <!-- Розміри -->
  <text x="125" y="212" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">AB = {base_a}</text>
  <text x="190" y="105" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#425a68">h = {height}</text>
  <!-- Точки -->
  <circle cx="185" cy="35" r="3.5" fill="#425a68"/>
  <circle cx="70" cy="180" r="3.5" fill="#425a68"/>
  <circle cx="210" cy="210" r="3.5" fill="#425a68"/>
  <circle cx="300" cy="145" r="3.5" fill="#425a68"/>
  <circle cx="160" cy="135" r="3" fill="#425a68"/>
  <circle cx="185" cy="167" r="3" fill="#425a68"/>
  <circle cx="230" cy="140" r="3" fill="#8c6239"/>
</svg>"""


def diagram_cylinder(d: int = 8, h: int = 8) -> str:
    """3D креслення циліндра з осьовим перерізом ABCD."""
    return f"""<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Тіло циліндра -->
  <!-- Нижній еліпс: задня частина пунктир, передня суцільна -->
  <path d="M 120,175 A 70 24 0 0 1 260,175" fill="none" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <path d="M 120,175 A 70 24 0 0 0 260,175" fill="none" stroke="#425a68" stroke-width="2.2"/>
  <!-- Твірні (бічні сторони) -->
  <line x1="120" y1="55" x2="120" y2="175" stroke="#425a68" stroke-width="2.2"/>
  <line x1="260" y1="55" x2="260" y2="175" stroke="#425a68" stroke-width="2.2"/>
  <!-- Верхній еліпс -->
  <ellipse cx="190" cy="55" rx="70" ry="24" fill="rgba(124, 150, 166, 0.15)" stroke="#425a68" stroke-width="2.2"/>
  <!-- Осьовий переріз ABCD -->
  <polygon points="120,55 260,55 260,175 120,175" fill="rgba(124, 150, 166, 0.2)" stroke="#8c6239" stroke-width="1.8"/>
  <!-- Діагональ перерізу AC -->
  <line x1="120" y1="175" x2="260" y2="55" stroke="#8c6239" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Вісь циліндра O1O2 -->
  <line x1="190" y1="55" x2="190" y2="175" stroke="#425a68" stroke-width="1.5" stroke-dasharray="4,4"/>
  <!-- Підписи вершин перерізу -->
  <text x="105" y="55" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">B</text>
  <text x="268" y="55" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">C</text>
  <text x="105" y="185" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">A</text>
  <text x="268" y="185" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">D</text>
  <text x="185" y="45" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="13" font-weight="700" fill="#425a68">O₁</text>
  <text x="185" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="13" font-weight="700" fill="#425a68">O₂</text>
  <text x="195" y="110" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">AC = 8√2</text>
</svg>"""


def diagram_function_roots() -> str:
    """Графік функції y = f(x) на координатній площині з лінією y = 1."""
    return """<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Координатна сітка -->
  <g stroke="#d6dfe5" stroke-width="1" stroke-dasharray="2,2">
    <line x1="30" y1="50" x2="350" y2="50"/>
    <line x1="30" y1="80" x2="350" y2="80"/>
    <line x1="30" y1="110" x2="350" y2="110"/>
    <line x1="30" y1="140" x2="350" y2="140"/>
    <line x1="30" y1="170" x2="350" y2="170"/>
    <line x1="70" y1="30" x2="70" y2="190"/>
    <line x1="100" y1="30" x2="100" y2="190"/>
    <line x1="130" y1="30" x2="130" y2="190"/>
    <line x1="160" y1="30" x2="160" y2="190"/>
    <line x1="190" y1="30" x2="190" y2="190"/>
    <line x1="220" y1="30" x2="220" y2="190"/>
    <line x1="250" y1="30" x2="250" y2="190"/>
    <line x1="280" y1="30" x2="280" y2="190"/>
    <line x1="310" y1="30" x2="310" y2="190"/>
    <line x1="340" y1="30" x2="340" y2="190"/>
  </g>
  <!-- Осі координат -->
  <line x1="30" y1="140" x2="360" y2="140" stroke="#425a68" stroke-width="2"/>
  <polygon points="360,140 352,136 352,144" fill="#425a68"/>
  <line x1="190" y1="200" x2="190" y2="25" stroke="#425a68" stroke-width="2"/>
  <polygon points="190,25 186,33 194,33" fill="#425a68"/>
  <text x="355" y="157" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">x</text>
  <text x="175" y="32" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">y</text>
  <text x="178" y="155" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="600" fill="#425a68">0</text>
  <text x="216" y="155" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="600" fill="#425a68">1</text>
  <text x="178" y="114" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="600" fill="#425a68">1</text>
  <text x="65" y="155" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="600" fill="#425a68">-4</text>
  <text x="335" y="155" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="600" fill="#425a68">5</text>
  <!-- Пряма y = 1 -->
  <line x1="35" y1="110" x2="350" y2="110" stroke="#7c96a6" stroke-width="2" stroke-dasharray="5,4"/>
  <text x="35" y="104" font-family="'Apple Garamond', 'EB Garamond', 'Taktika Sans', 'Onest', sans-serif" font-size="13" font-weight="700" fill="#8c6239">y = 1</text>
  <!-- Крива y = f(x) -->
  <path d="M 70,185 C 100,50 140,50 170,120 C 195,175 230,170 260,70 C 285,-10 320,110 340,140" fill="none" stroke="#425a68" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Точки перетину з y = 1 -->
  <circle cx="85" cy="110" r="4.5" fill="#7c96a6" stroke="#425a68" stroke-width="1.5"/>
  <circle cx="166" cy="110" r="4.5" fill="#7c96a6" stroke="#425a68" stroke-width="1.5"/>
  <circle cx="288" cy="110" r="4.5" fill="#7c96a6" stroke="#425a68" stroke-width="1.5"/>
</svg>"""


def diagram_derivative_tangent() -> str:
    """Геометричний зміст похідної: графік кривої y = f(x) та дотична через вузли A(-2,-1) та B(2,5)."""
    return """<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Координатна сітка -->
  <g stroke="#d6dfe5" stroke-width="1" stroke-dasharray="2,2">
    <line x1="30" y1="50" x2="350" y2="50"/>
    <line x1="30" y1="80" x2="350" y2="80"/>
    <line x1="30" y1="110" x2="350" y2="110"/>
    <line x1="30" y1="140" x2="350" y2="140"/>
    <line x1="30" y1="170" x2="350" y2="170"/>
    <line x1="100" y1="30" x2="100" y2="190"/>
    <line x1="140" y1="30" x2="140" y2="190"/>
    <line x1="180" y1="30" x2="180" y2="190"/>
    <line x1="220" y1="30" x2="220" y2="190"/>
    <line x1="260" y1="30" x2="260" y2="190"/>
  </g>
  <!-- Осі -->
  <line x1="30" y1="140" x2="360" y2="140" stroke="#425a68" stroke-width="2"/>
  <polygon points="360,140 352,136 352,144" fill="#425a68"/>
  <line x1="180" y1="200" x2="180" y2="25" stroke="#425a68" stroke-width="2"/>
  <polygon points="180,25 176,33 184,33" fill="#425a68"/>
  <!-- Підписи осей -->
  <text x="355" y="157" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">x</text>
  <text x="165" y="32" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">y</text>
  <text x="168" y="155" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="600" fill="#425a68">0</text>
  <!-- Дотична лінія (через вузли сітки) -->
  <line x1="80" y1="185" x2="280" y2="35" stroke="#8c6239" stroke-width="2.2"/>
  <!-- Точки на дотичній: A(-2, -1) ~ (140, 155), B(2, 5) ~ (220, 65) -->
  <circle cx="140" cy="155" r="4.5" fill="#7c96a6" stroke="#425a68" stroke-width="1.8"/>
  <text x="110" y="165" font-family="'Apple Garamond', 'EB Garamond', 'Taktika Sans', 'Onest', sans-serif" font-size="14" font-weight="700" fill="#425a68">A(-2; -1)</text>
  <circle cx="220" cy="95" r="4.5" fill="#7c96a6" stroke="#425a68" stroke-width="1.8"/>
  <text x="230" y="95" font-family="'Apple Garamond', 'EB Garamond', 'Taktika Sans', 'Onest', sans-serif" font-size="14" font-weight="700" fill="#425a68">B(2; 5)</text>
  <!-- Графік y = f(x) з точкою дотику -->
  <path d="M 100,195 Q 160,170 180,125 T 260,35" fill="none" stroke="#425a68" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="180" cy="125" r="4" fill="#425a68"/>
  <text x="190" y="130" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">(x₀; y₀)</text>
</svg>"""


def diagram_rhombus_diagonals(d1: int = 24, d2: int = 10, side: int = 13) -> str:
    """Креслення ромба ABCD з діагоналями AC та BD."""
    return f"""<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Ромб -->
  <polygon points="190,40 310,115 190,190 70,115" fill="rgba(124, 150, 166, 0.16)" stroke="#425a68" stroke-width="2.2" stroke-linejoin="round"/>
  <!-- Діагоналі -->
  <line x1="70" y1="115" x2="310" y2="115" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <line x1="190" y1="40" x2="190" y2="190" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Прямий кут у центрі O -->
  <rect x="190" y="103" width="12" height="12" fill="none" stroke="#425a68" stroke-width="1.5"/>
  <!-- Вершини -->
  <text x="185" y="30" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">B</text>
  <text x="320" y="120" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">C</text>
  <text x="185" y="208" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">D</text>
  <text x="50" y="120" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="16" font-weight="700" fill="#425a68">A</text>
  <text x="195" y="110" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#8c6239">O</text>
  <!-- Розміри діагоналей -->
  <text x="105" y="105" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">AC = {d1}</text>
  <text x="198" y="75" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">BD = {d2}</text>
  <!-- Точки -->
  <circle cx="190" cy="40" r="3.5" fill="#425a68"/>
  <circle cx="310" cy="115" r="3.5" fill="#425a68"/>
  <circle cx="190" cy="190" r="3.5" fill="#425a68"/>
  <circle cx="70" cy="115" r="3.5" fill="#425a68"/>
  <circle cx="190" cy="115" r="3" fill="#8c6239"/>
</svg>"""


def diagram_vectors() -> str:
    """Вектори a та b у прямокутній системі координат."""
    return """<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Координатна сітка -->
  <g stroke="#d6dfe5" stroke-width="1" stroke-dasharray="2,2">
    <line x1="30" y1="50" x2="350" y2="50"/>
    <line x1="30" y1="85" x2="350" y2="85"/>
    <line x1="30" y1="120" x2="350" y2="120"/>
    <line x1="30" y1="155" x2="350" y2="155"/>
    <line x1="30" y1="190" x2="350" y2="190"/>
    <line x1="90" y1="30" x2="90" y2="200"/>
    <line x1="130" y1="30" x2="130" y2="200"/>
    <line x1="170" y1="30" x2="170" y2="200"/>
    <line x1="210" y1="30" x2="210" y2="200"/>
    <line x1="250" y1="30" x2="250" y2="200"/>
    <line x1="290" y1="30" x2="290" y2="200"/>
  </g>
  <!-- Осі з початком у (130, 120) -->
  <line x1="30" y1="120" x2="350" y2="120" stroke="#425a68" stroke-width="2"/>
  <polygon points="350,120 342,116 342,124" fill="#425a68"/>
  <line x1="130" y1="205" x2="130" y2="25" stroke="#425a68" stroke-width="2"/>
  <polygon points="130,25 126,33 134,33" fill="#425a68"/>
  <!-- Підписи осей -->
  <text x="345" y="137" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">x</text>
  <text x="115" y="32" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="14" font-weight="700" fill="#425a68">y</text>
  <text x="115" y="135" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="13" font-weight="600" fill="#425a68">O</text>
  <!-- Вектор a(3; 4) -> x = 130 + 3*25 = 205, y = 120 - 4*17.5 = 50 -->
  <line x1="130" y1="120" x2="205" y2="50" stroke="#425a68" stroke-width="2.5"/>
  <polygon points="205,50 195,54 200,61" fill="#425a68"/>
  <text x="160" y="70" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">a⃗</text>
  <text x="212" y="48" font-family="'Apple Garamond', 'EB Garamond', 'Taktika Sans', 'Onest', sans-serif" font-size="14" font-weight="700" fill="#425a68">A(3; 4)</text>
  <!-- Вектор b(6; -2) -> x = 130 + 6*25 = 280, y = 120 + 2*17.5 = 155 -->
  <line x1="130" y1="120" x2="280" y2="155" stroke="#8c6239" stroke-width="2.5"/>
  <polygon points="280,155 272,148 269,156" fill="#8c6239"/>
  <text x="220" y="152" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#8c6239">b⃗</text>
  <text x="286" y="165" font-family="'Apple Garamond', 'EB Garamond', 'Taktika Sans', 'Onest', sans-serif" font-size="14" font-weight="700" fill="#8c6239">B(6; -2)</text>
</svg>"""


def diagram_box_prism(a: int = 3, b: int = 4, angle: int = 45) -> str:
    """3D прямокутний паралелепіпед ABCDA₁B₁C₁D₁ з діагоналлю BD₁."""
    return f"""<svg viewBox="0 0 380 230" xmlns="http://www.w3.org/2000/svg" class="math-diagram-svg">
  <rect x="8" y="8" width="364" height="214" rx="12" fill="#f4f1ec" stroke="#d6dfe5" stroke-width="1.5"/>
  <!-- Невидимі задні грані (пунктир) -->
  <line x1="80" y1="180" x2="140" y2="140" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <line x1="140" y1="140" x2="280" y2="140" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <line x1="140" y1="140" x2="140" y2="60" stroke="#425a68" stroke-width="1.8" stroke-dasharray="4,4"/>
  <!-- Видимі передні ребра -->
  <polygon points="80,180 220,180 280,140 140,140" fill="rgba(124, 150, 166, 0.12)" stroke="none"/>
  <line x1="80" y1="180" x2="220" y2="180" stroke="#425a68" stroke-width="2.2"/>
  <line x1="220" y1="180" x2="280" y2="140" stroke="#425a68" stroke-width="2.2"/>
  <line x1="80" y1="180" x2="80" y2="100" stroke="#425a68" stroke-width="2.2"/>
  <line x1="220" y1="180" x2="220" y2="100" stroke="#425a68" stroke-width="2.2"/>
  <line x1="280" y1="140" x2="280" y2="60" stroke="#425a68" stroke-width="2.2"/>
  <!-- Верхня основа -->
  <polygon points="80,100 220,100 280,60 140,60" fill="rgba(124, 150, 166, 0.16)" stroke="#425a68" stroke-width="2.2" stroke-linejoin="round"/>
  <!-- Діагональ основи BD (пунктир) -->
  <line x1="220" y1="180" x2="140" y2="140" stroke="#7c96a6" stroke-width="1.5" stroke-dasharray="3,3"/>
  <!-- Просторова діагональ BD₁ (пунктир) -->
  <line x1="220" y1="180" x2="140" y2="60" stroke="#8c6239" stroke-width="2" stroke-dasharray="4,4"/>
  <!-- Кут 45° -->
  <text x="180" y="165" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="700" fill="#8c6239">{angle}°</text>
  <!-- Підписи вершин -->
  <text x="65" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">A</text>
  <text x="225" y="195" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">B</text>
  <text x="290" y="145" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">C</text>
  <text x="125" y="145" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">D</text>
  <text x="65" y="95" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">A₁</text>
  <text x="225" y="95" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">B₁</text>
  <text x="290" y="55" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">C₁</text>
  <text x="125" y="55" font-family="'Apple Garamond', 'EB Garamond', 'Garamond', serif" font-size="15" font-weight="700" fill="#425a68">D₁</text>
  <!-- Розміри -->
  <text x="145" y="195" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">AB = {a}</text>
  <text x="255" y="170" font-family="'Taktika Sans', 'Onest', 'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600" fill="#8c6239">AD = {b}</text>
</svg>"""
