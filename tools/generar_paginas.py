"""Genera las páginas de servicio de cliencia.com.ar.

Toma el encabezado, el pie, los íconos y la política de privacidad de index.html,
así todas las páginas comparten exactamente el mismo diseño.

Uso (desde la raíz del proyecto):  python tools/generar_paginas.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://cliencia.com.ar"
ORG_ID = SITE + "/#organization"
WEBSITE_ID = SITE + "/#website"

index = (ROOT / "index.html").read_text(encoding="utf8")


def grab(pattern):
    m = re.search(pattern, index, re.S)
    assert m, pattern
    return m.group(0)


def to_home_links(fragment):
    # Las anclas de la home (#servicios, #contacto...) pasan a /#servicios. Los íconos (#i-...) y href="#" no se tocan.
    fragment = fragment.replace('href="#inicio"', 'href="/"')
    return re.sub(r'href="#(?!i-)([\w-]+)"', r'href="/#\1"', fragment)


SPRITE = grab(r'<svg width="0" height="0".*?</svg>\n')
HEADER = to_home_links(grab(r'<header class="site-header".*?</header>'))
FOOTER = to_home_links(grab(r'<footer class="site-footer">.*?</footer>'))
WA_FLOAT = grab(r'<a class="wa-float.*?</a>')
PRIVACY = grab(r'<dialog id="privacy".*?</dialog>')


def icon(name):
    return f'<svg aria-hidden="true"><use href="#{name}"/></svg>'


def esc(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- bloques

def hero(page):
    return f'''<section class="hero page-hero" id="inicio">
  <div class="container" style="position:relative">
    <nav class="breadcrumb" aria-label="Ruta de navegación">
      <ol>
        <li><a href="/">Inicio</a></li>
        <li><a href="/#servicios">Servicios</a></li>
        <li aria-current="page">{page["crumb"]}</li>
      </ol>
    </nav>
    <span class="eyebrow">{page["eyebrow"]}</span>
    <h1>{page["h1"]}</h1>
    <p class="lead">{page["lead"]}</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/#contacto" data-track="cta_diagnostico_{page["slug"]}">Quiero mi diagnóstico inicial {icon("i-arrow")}</a>
      <a class="btn btn-ghost js-wa" href="#" target="_blank" rel="noopener" data-track="whatsapp_{page["slug"]}">{icon("i-wa")} Hablar por WhatsApp</a>
    </div>
  </div>
</section>'''


def head_block(eyebrow, title, sub=None, hid=None):
    sub_html = f"\n      <p>{sub}</p>" if sub else ""
    return f'''    <div class="section-head reveal">
      <span class="eyebrow">{eyebrow}</span>
      <h2 id="{hid}">{title}</h2>{sub_html}
    </div>'''


def section(cls, sid, inner):
    cls_attr = f' class="{cls}"' if cls else ""
    return f'''<section{cls_attr} id="{sid}" aria-labelledby="t-{sid}">
  <div class="container">
{inner}
  </div>
</section>'''


def b_prose(b):
    paras = "\n".join(f"      <p>{p}</p>" for p in b["paras"])
    checks = ""
    if b.get("checks"):
        items = "\n".join(f"        <li>{c}</li>" for c in b["checks"])
        checks = f'\n      <ul class="checks{" two" if b.get("two") else ""}">\n{items}\n      </ul>'
    inner = f'''    <div class="prose reveal">
      <span class="eyebrow">{b["eyebrow"]}</span>
      <h2 id="t-{b["id"]}">{b["title"]}</h2>
{paras}{checks}
    </div>'''
    return section(b.get("cls", ""), b["id"], inner)


def b_cards(b):
    cards = []
    for c in b["cards"]:
        q = f'\n        <p class="q">{c["q"]}</p>' if c.get("q") else ""
        ul = ""
        if c.get("bullets"):
            ul = "\n        <ul>" + "".join(f"<li>{x}</li>" for x in c["bullets"]) + "</ul>"
        link = ""
        if c.get("link"):
            link = f'\n        <a class="text-link" href="{c["link"][0]}">{c["link"][1]} {icon("i-arrow")}</a>'
        cards.append(f'''      <article class="card reveal">
        <span class="icon">{icon(c["icon"])}</span>
        <h3>{c["title"]}</h3>{q}
        <p>{c["text"]}</p>{ul}{link}
      </article>''')
    inner = head_block(b["eyebrow"], b["title"], b.get("sub"), "t-" + b["id"]) + f'''
    <div class="cards svc-cards {b.get("cols", "three")}">
{chr(10).join(cards)}
    </div>'''
    return section(b.get("cls", ""), b["id"], inner)


def b_steps(b):
    steps = "\n".join(
        f'      <li class="step reveal"><span class="step-num">{i}</span><div><h3>{t}</h3><p>{d}</p></div></li>'
        for i, (t, d) in enumerate(b["steps"], 1))
    style = ""
    if len(b["steps"]) != 6:
        style = f' style="--n:{len(b["steps"])}"'
    inner = head_block(b["eyebrow"], b["title"], b.get("sub"), "t-" + b["id"]) + f'''
    <ol class="steps compact"{style}>
{steps}
    </ol>'''
    return section(b.get("cls", ""), b["id"], inner)


def b_faq(page):
    items = "\n".join(
        f'      <details class="reveal"><summary>{q}</summary><div class="answer"><p>{a}</p></div></details>'
        for q, a in page["faq"])
    inner = head_block("Dudas", "Preguntas frecuentes", None, "t-preguntas") + f'''
    <div class="faq">
{items}
    </div>'''
    return section("soft", "preguntas", inner)


def b_related(page):
    others = [p for p in PAGES if p["slug"] != page["slug"]]
    links = "\n".join(
        f'      <a href="/{p["slug"]}/" class="reveal"><strong>{p["crumb"]}</strong><span>{p["teaser"]}</span></a>'
        for p in others)
    inner = head_block("Seguí leyendo", "Otros servicios de cliencIA", None, "t-relacionados") + f'''
    <div class="related">
{links}
    </div>'''
    return section("", "relacionados", inner)


def b_cta(page):
    return f'''<section class="cta-band" id="empezar" aria-labelledby="t-empezar">
  <div class="container reveal">
    <h2 id="t-empezar">{page.get("cta_title", "¿Listo para entender a tus clientes de verdad?")}</h2>
    <p>Pedí tu diagnóstico inicial: la primera charla para conocer tu caso es sin cargo.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/#contacto" data-track="cta_diagnostico_{page["slug"]}_cierre">Quiero mi diagnóstico inicial {icon("i-arrow")}</a>
      <a class="btn btn-wa js-wa" href="#" target="_blank" rel="noopener" data-track="whatsapp_{page["slug"]}_cierre">{icon("i-wa")} Hablar por WhatsApp</a>
    </div>
  </div>
</section>'''


BUILDERS = {"prose": b_prose, "cards": b_cards, "steps": b_steps}


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def schema(page):
    url = f"{SITE}/{page['slug']}/"
    graph = [
        {
            "@type": "WebPage",
            "@id": url + "#webpage",
            "url": url,
            "name": page["title"],
            "description": page["description"],
            "inLanguage": "es-AR",
            "isPartOf": {"@id": WEBSITE_ID},
            "about": {"@id": url + "#service"},
            "breadcrumb": {"@id": url + "#breadcrumb"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": url + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Servicios", "item": SITE + "/#servicios"},
                {"@type": "ListItem", "position": 3, "name": page["crumb"], "item": url},
            ],
        },
        {
            "@type": "Service",
            "@id": url + "#service",
            "name": page["service_name"],
            "serviceType": page["service_type"],
            "description": strip_tags(page["lead"]),
            "url": url,
            "provider": {"@id": ORG_ID},
            "areaServed": [{"@type": "State", "name": "Misiones"}, {"@type": "Country", "name": "Argentina"}],
        },
        {
            "@type": "FAQPage",
            "@id": url + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in page["faq"]
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)


def render(page):
    url = f"{SITE}/{page['slug']}/"
    body = "\n\n".join([hero(page)] + [BUILDERS[b["type"]](b) for b in page["blocks"]] +
                       [b_faq(page), b_cta(page), b_related(page)])
    return f'''<!DOCTYPE html>
<html lang="es-AR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page["title"])}</title>
<meta name="description" content="{esc(page["description"])}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#030D2B">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" href="/favicon.png" sizes="96x96">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_AR">
<meta property="og:site_name" content="cliencIA">
<meta property="og:title" content="{esc(page["title"])}">
<meta property="og:description" content="{esc(page["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page["title"])}">
<meta name="twitter:description" content="{esc(page["description"])}">
<meta name="twitter:image" content="{SITE}/og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<script type="application/ld+json">
{schema(page)}
</script>
</head>
<body class="no-js">
<a class="skip" href="#contenido">Saltar al contenido</a>

<!-- Página generada con tools/generar_paginas.py: editar el contenido ahí y volver a generar. -->
{SPRITE}
{HEADER}

<main id="contenido">

{body}

</main>

{FOOTER}

{WA_FLOAT}

{PRIVACY}

<script src="/assets/site.js"></script>
</body>
</html>
'''


# ---------------------------------------------------------------- contenido

COMO_EMPEZAR = ("¿Cómo empiezo?",
                "Pedí tu diagnóstico inicial desde el formulario de la página principal o escribinos por WhatsApp. "
                "La primera charla para conocer tu caso es sin cargo, y a partir de ahí te proponemos el alcance y el presupuesto.")
IA_PERSONAS = ("¿Qué hace la inteligencia artificial y qué hacen las personas?",
               "La IA acelera tareas como procesar datos, monitorear opiniones y hacer el primer contacto con potenciales clientes. "
               "Las personas definimos las preguntas, interpretamos los resultados y armamos las recomendaciones: nada se entrega sin revisión profesional.")
PASOS = [
    ("Te escuchamos", "Conocemos tu negocio, tus objetivos y tus dudas."),
    ("Diseñamos tu diagnóstico a medida", "Definimos las preguntas y los indicadores clave."),
    ("Investigamos con rigor profesional", "Aplicamos metodología, no intuición."),
    ("Analizamos los datos", "Cruzamos información para detectar patrones."),
    ("Te entregamos un diagnóstico claro", "Con conclusiones y recomendaciones accionables."),
    ("Seguimos con vos", "Si lo necesitás, te acompañamos a implementar la estrategia."),
]

PAGES = [
    {
        "slug": "inteligencia-comercial",
        "crumb": "Inteligencia comercial",
        "teaser": "Qué es, para qué sirve y cómo la aplicamos en pymes.",
        "title": "Inteligencia comercial para pymes | cliencIA",
        "description": "Qué es la inteligencia comercial y cómo te ayuda a vender más: análisis de clientes, mercado y ventas, con marketing e inteligencia artificial. Consultora en Misiones para todo el país.",
        "service_name": "Inteligencia comercial para pymes",
        "service_type": "Consultoría de inteligencia comercial",
        "eyebrow": "Inteligencia comercial",
        "h1": "Inteligencia comercial para pymes: decisiones basadas en datos reales",
        "lead": "La inteligencia comercial es reunir y analizar información sobre tus clientes, tu mercado y tu proceso de ventas para decidir mejor. En cliencIA la aplicamos a la realidad de cada pyme: investigamos con el rigor de las ciencias económicas, usamos inteligencia artificial para procesar y monitorear datos y te entregamos recomendaciones concretas para vender más.",
        "blocks": [
            {
                "type": "prose", "id": "que-es", "eyebrow": "La idea en simple",
                "title": "¿Qué es la inteligencia comercial?",
                "paras": [
                    "Es el trabajo de convertir datos en decisiones comerciales. En lugar de decidir por intuición, mirás evidencia: quiénes te compran, por qué te eligen, por qué se van, qué hace tu competencia y en qué parte del proceso de venta se pierden oportunidades.",
                    "Un estudio de mercado es una foto de un momento. La inteligencia comercial es un proceso: combina estudios puntuales, los datos de tus propias ventas y el monitoreo continuo de lo que dicen tus clientes, para que puedas ajustar el rumbo a tiempo.",
                    "<strong>Te ayuda a responder preguntas como:</strong>",
                ],
                "checks": [
                    "¿Por qué me eligen mis clientes y por qué se van?",
                    "¿Quiénes son mis mejores clientes y dónde encuentro más como ellos?",
                    "¿En qué parte del proceso de venta estoy perdiendo oportunidades?",
                    "¿Mi publicidad le llega a las personas correctas?",
                ],
                "two": True,
            },
            {
                "type": "cards", "id": "como-la-aplicamos", "cls": "soft", "cols": "two",
                "eyebrow": "Cómo la aplicamos", "title": "Lo que hacemos en cliencIA",
                "sub": "De la pregunta correcta a la acción, en cuatro frentes.",
                "cards": [
                    {"icon": "i-search", "title": "Diagnóstico",
                     "text": "Investigamos a tus clientes, tu mercado y tu proceso de ventas para entender qué está pasando y qué corregir primero.",
                     "bullets": ["Mapa del Cliente", "Radar de Mercado", "Chequeo de Ventas"],
                     "link": ("/investigacion-de-mercado/", "Ver investigación de mercado")},
                    {"icon": "i-ai", "title": "Inteligencia continua con IA",
                     "text": "Monitoreamos la satisfacción y las opiniones en tiempo real y usamos agentes de IA para encontrar y contactar potenciales clientes.",
                     "bullets": ["Inteligencia en Vivo", "Prospección con IA"],
                     "link": ("/prospeccion-con-ia/", "Ver prospección con IA")},
                    {"icon": "i-megaphone", "title": "Estrategia de marketing y campañas",
                     "text": "Llevamos los hallazgos a una estrategia de marketing y a campañas en Meta, Google y TikTok, con seguimiento y reportes de resultados. La gestión de campañas es opcional y a pedido."},
                    {"icon": "i-teach", "title": "Capacitación",
                     "text": "Capacitamos a tu equipo en inteligencia artificial y estrategias de marketing aplicadas a la inteligencia comercial, con talleres prácticos pensados para tu empresa."},
                ],
            },
            {
                "type": "prose", "id": "beneficios", "eyebrow": "Para qué sirve",
                "title": "Qué gana tu empresa",
                "paras": ["Trabajar con inteligencia comercial no es tener más reportes: es tomar menos decisiones a ciegas."],
                "checks": [
                    "Decidís con evidencia, no con corazonadas.",
                    "Invertís en publicidad donde de verdad rinde.",
                    "Detectás a tiempo por qué se van los clientes.",
                    "Ordenás tu proceso comercial y sabés dónde mejorar.",
                    "Tu equipo aprende a usar datos e IA en el día a día.",
                    "Tenés indicadores claros para medir el avance.",
                ],
                "two": True,
            },
            {"type": "steps", "id": "metodo", "cls": "soft", "eyebrow": "Nuestro método",
             "title": "Cómo trabajamos", "sub": "Así convertimos datos en resultados.", "steps": PASOS},
        ],
        "faq": [
            ("¿En qué se diferencia de un estudio de mercado?",
             "Un estudio de mercado responde una pregunta en un momento puntual. La inteligencia comercial es un proceso continuo: usa estudios, datos de ventas y monitoreo de clientes para que las decisiones comerciales se apoyen siempre en evidencia."),
            ("¿Sirve para una pyme o solo para empresas grandes?",
             "Sirve para pymes, comercios y emprendedores. Adaptamos el alcance al tamaño de cada empresa. Si tenés pocos clientes, el diagnóstico te ayuda a entender mejor a quiénes apuntar y cómo llegar a ellos."),
            IA_PERSONAS,
            ("¿Trabajan con empresas de otras provincias?",
             "Sí. Nuestra base está en Misiones y trabajamos de forma remota con empresas de todo el país."),
            COMO_EMPEZAR,
        ],
    },
    {
        "slug": "investigacion-de-mercado",
        "crumb": "Investigación de mercado",
        "teaser": "Mapa del Cliente, Radar de Mercado y Chequeo de Ventas.",
        "title": "Investigación de mercado y análisis de clientes para pymes | cliencIA",
        "description": "Investigación de mercado a medida para pymes: análisis de clientes, segmentación, tendencias del sector y diagnóstico del proceso de ventas, con recomendaciones concretas. Desde Misiones para todo el país.",
        "service_name": "Investigación de mercado y análisis de clientes",
        "service_type": "Investigación de mercado",
        "eyebrow": "Diagnóstico",
        "h1": "Investigación de mercado y análisis de clientes para pymes",
        "lead": "Una investigación de mercado te dice quiénes son tus clientes, qué quieren, por qué te eligen o se van y dónde estás perdiendo ventas. En cliencIA la hacemos a medida de cada pyme, con metodología profesional, y la convertimos en un diagnóstico claro con recomendaciones concretas para aplicar.",
        "blocks": [
            {
                "type": "cards", "id": "servicios-diagnostico", "cls": "soft",
                "eyebrow": "Tres estudios", "title": "¿Qué querés entender de tu negocio?",
                "sub": "Elegimos el estudio según la pregunta que necesitás responder. También se pueden combinar.",
                "cards": [
                    {"icon": "i-users", "title": "Mapa del Cliente", "q": "¿Por qué se van o no se animan a comprar?",
                     "text": "Estudio del cliente, puntos de fricción y contenido clave, con recomendaciones concretas.",
                     "bullets": ["Cómo vive tu cliente la experiencia de compra", "Dónde se traba o se frustra", "Qué lo convence y qué lo hace dudar"]},
                    {"icon": "i-target", "title": "Radar de Mercado", "q": "¿Quiénes son mis clientes y qué quieren?",
                     "text": "Estudio de mercado, segmentación y tendencias del sector.",
                     "bullets": ["Segmentos de clientes y sus necesidades", "Qué hace tu competencia", "Tendencias que afectan a tu rubro"]},
                    {"icon": "i-chart", "title": "Chequeo de Ventas", "q": "¿Dónde estoy perdiendo ventas?",
                     "text": "Análisis de tu proceso comercial, comparado con los estándares del mercado.",
                     "bullets": ["Cada etapa del proceso de venta", "Dónde se caen las oportunidades", "Qué mejorar primero"]},
                ],
            },
            {
                "type": "prose", "id": "que-recibis", "eyebrow": "Entregables",
                "title": "Qué recibís al terminar",
                "paras": ["Un diagnóstico pensado para usarse, no para quedar en un cajón."],
                "checks": [
                    "Un informe claro, sin tecnicismos innecesarios.",
                    "Conclusiones sobre tus clientes, tu mercado y tus ventas.",
                    "Recomendaciones concretas y ordenadas por prioridad.",
                    "Los indicadores clave para seguir el avance.",
                    "Acompañamiento para implementar, si lo necesitás.",
                ],
            },
            {"type": "steps", "id": "metodo", "cls": "soft", "eyebrow": "Nuestro método",
             "title": "Cómo hacemos la investigación", "sub": "Seis pasos, de la primera charla al plan de acción.", "steps": PASOS},
            {
                "type": "prose", "id": "para-quien", "eyebrow": "Para quién es",
                "title": "¿Para quién es este diagnóstico?",
                "paras": ["Para empresas que venden, pero no tienen claro por qué les va bien o mal, o que están por tomar una decisión importante y quieren hacerlo con datos."],
                "checks": [
                    "Pymes y comercios",
                    "Empresas de servicios",
                    "Emprendedores en crecimiento",
                    "Instituciones",
                ],
                "two": True,
            },
        ],
        "faq": [
            ("¿Qué incluye el diagnóstico inicial?",
             "Una primera conversación para conocer tu negocio y tus objetivos, el análisis de tus clientes, tu mercado y tu proceso de ventas, y un informe claro con conclusiones y recomendaciones concretas para aplicar."),
            ("¿Cuánto dura?",
             "Depende del tamaño y la complejidad de cada empresa. En general, entre 2 y 4 semanas desde que definimos el alcance juntos."),
            ("¿Tiene costo?",
             "La primera charla para conocer tu caso es sin cargo. El diagnóstico se presupuesta a medida según el alcance, y te pasamos el valor antes de empezar, sin compromiso."),
            ("¿Necesito tener muchos clientes para hacerlo?",
             "No. Trabajamos con emprendedores, comercios y pymes de distintos tamaños. Si tenés pocos clientes, el diagnóstico te ayuda a entender mejor a quiénes apuntar y cómo llegar a ellos."),
            COMO_EMPEZAR,
        ],
    },
    {
        "slug": "prospeccion-con-ia",
        "crumb": "Prospección con IA",
        "teaser": "Agentes de IA que contactan clientes y monitorean opiniones.",
        "title": "Prospección con IA y agentes de inteligencia artificial para empresas | cliencIA",
        "description": "Agentes de inteligencia artificial que contactan potenciales clientes, detectan interés real y agendan reuniones, más monitoreo de satisfacción y opiniones en tiempo real. Desarrollo a medida para pymes.",
        "service_name": "Prospección con IA y agentes de inteligencia artificial",
        "service_type": "Agentes de inteligencia artificial para ventas",
        "eyebrow": "Inteligencia continua con IA",
        "h1": "Prospección con IA: agentes que encuentran y contactan a tus próximos clientes",
        "lead": "La prospección con inteligencia artificial usa un agente virtual que contacta a potenciales clientes, detecta quiénes tienen interés real y agenda reuniones con tu equipo. En cliencIA desarrollamos estos agentes a medida, junto con el monitoreo de la satisfacción y las opiniones en tiempo real, para que tu equipo dedique su tiempo a cerrar ventas.",
        "blocks": [
            {
                "type": "cards", "id": "servicios-ia", "cls": "soft", "cols": "two",
                "eyebrow": "Dos servicios", "title": "Inteligencia artificial al servicio de tus ventas",
                "cards": [
                    {"icon": "i-rocket", "title": "Prospección con IA",
                     "text": "Un agente virtual que contacta a potenciales clientes, detecta interés real y agenda reuniones con tu equipo.",
                     "bullets": ["Hace el primer contacto por vos", "Filtra a quienes tienen interés real", "Agenda reuniones y le pasa la información a tu equipo"]},
                    {"icon": "i-eye", "title": "Inteligencia en Vivo",
                     "text": "Monitoreo de la satisfacción y de las opiniones en tiempo real, con alertas y reportes automáticos.",
                     "bullets": ["Seguimiento continuo de lo que dicen tus clientes", "Alertas cuando algo necesita atención", "Reportes automáticos para decidir rápido"]},
                ],
            },
            {
                "type": "prose", "id": "automatizacion", "eyebrow": "Agentes a medida",
                "title": "Automatizar tareas para ganar tiempo y datos",
                "paras": [
                    "Desarrollamos agentes de inteligencia artificial que automatizan tareas, optimizan procesos y obtienen datos valiosos para mejorar tu empresa. Cada agente se diseña para tu negocio: tu cliente ideal, tu forma de vender y tu tono.",
                    "<strong>Algunos usos posibles:</strong>",
                ],
                "checks": [
                    "Dar seguimiento a consultas que quedaron sin respuesta.",
                    "Calificar contactos antes de que lleguen a tu equipo.",
                    "Pedir opiniones a tus clientes después de cada compra.",
                    "Avisarte cuando aparece una opinión negativa.",
                ],
                "two": True,
            },
            {
                "type": "steps", "id": "metodo", "cls": "soft", "eyebrow": "Cómo lo hacemos",
                "title": "De la idea al agente funcionando",
                "steps": [
                    ("Definimos el objetivo", "Qué tiene que lograr el agente y cómo vamos a medirlo."),
                    ("Diseñamos el agente", "Perfil de cliente ideal, mensajes y criterios para detectar interés."),
                    ("Lo ponemos a trabajar", "Lo probamos, lo ajustamos y lo integramos con tu equipo."),
                    ("Medimos y mejoramos", "Revisamos resultados y lo afinamos con datos reales."),
                ],
            },
            {
                "type": "prose", "id": "supervision", "eyebrow": "IA con criterio",
                "title": "La IA trabaja, las personas deciden",
                "paras": [
                    "La inteligencia artificial acelera tareas como procesar datos, monitorear opiniones y hacer el primer contacto con potenciales clientes. Las personas definimos las preguntas, interpretamos los resultados y armamos las recomendaciones: nada se entrega sin revisión profesional.",
                    "Usamos la IA como una herramienta útil, no como una moda, y te mostramos la realidad de los datos con honestidad.",
                ],
            },
        ],
        "faq": [
            ("¿El agente reemplaza a mi equipo de ventas?",
             "No. El agente hace el primer contacto y detecta quién tiene interés real; tu equipo se ocupa de las conversaciones que importan y de cerrar las ventas."),
            ("¿Necesito conocimientos técnicos?",
             "No. Nosotros diseñamos, desarrollamos y ajustamos el agente. Vos nos contás cómo es tu negocio y a qué clientes querés llegar."),
            ("¿Qué pasa con los datos de mis clientes?",
             "Los usamos solo para prestar el servicio, de acuerdo con la Ley 25.326 de Protección de los Datos Personales. No los vendemos ni los compartimos con terceros para fines comerciales."),
            IA_PERSONAS,
            COMO_EMPEZAR,
        ],
    },
    {
        "slug": "consultora-marketing-misiones",
        "crumb": "Consultora en Misiones",
        "teaser": "Inteligencia comercial y marketing para empresas de la provincia.",
        "title": "Consultora de marketing e inteligencia comercial en Misiones | cliencIA",
        "description": "cliencIA es una consultora y agencia de inteligencia comercial y marketing con base en Misiones: investigación de mercado, estrategia, publicidad digital e IA para pymes y comercios de la provincia.",
        "service_name": "Consultoría de marketing e inteligencia comercial en Misiones",
        "service_type": "Consultoría de marketing",
        "eyebrow": "Misiones, Argentina",
        "h1": "Consultora de marketing e inteligencia comercial en Misiones",
        "lead": "cliencIA es una consultora y agencia de inteligencia comercial con base en Misiones. Ayudamos a pymes, comercios, emprendedores e instituciones de la provincia a conocer a sus clientes, entender su mercado y vender más con datos reales, combinando investigación, estrategia de marketing, publicidad digital e inteligencia artificial.",
        "cta_title": "¿Tenés una empresa en Misiones? Hablemos.",
        "blocks": [
            {
                "type": "prose", "id": "por-que-local", "eyebrow": "Cerca tuyo",
                "title": "Una consultora que conoce la realidad de tu empresa",
                "paras": [
                    "En cliencIA unimos dos mundos que suelen estar separados: la profundidad analítica de una consultora y la agilidad de una agencia de marketing y tecnología. Y lo hacemos desde Misiones, con soluciones a la altura de cada empresa.",
                    "Nuestra visión es ser la consultora y agencia de referencia en inteligencia comercial, creciendo desde Misiones hacia el resto del país.",
                ],
                "checks": [
                    "Cercanía: trabajamos con vos, no con un formulario.",
                    "Rigor profesional: metodología, no intuición.",
                    "Acompañamiento antes, durante y después del diagnóstico.",
                    "Transparencia: te mostramos la realidad de los datos.",
                ],
                "two": True,
            },
            {
                "type": "cards", "id": "servicios-misiones", "cls": "soft", "cols": "two",
                "eyebrow": "Servicios", "title": "Todo lo que necesitás en un mismo lugar",
                "sub": "Estrategia, método, análisis y tecnología, con un equipo de cuatro perfiles complementarios.",
                "cards": [
                    {"icon": "i-search", "title": "Investigación de mercado",
                     "text": "Mapa del Cliente, Radar de Mercado y Chequeo de Ventas para entender a tus clientes y tu mercado.",
                     "link": ("/investigacion-de-mercado/", "Ver investigación de mercado")},
                    {"icon": "i-megaphone", "title": "Marketing y publicidad digital",
                     "text": "Estrategia de marketing y campañas en Meta, Google y TikTok, con contenido, seguimiento y reportes de resultados."},
                    {"icon": "i-ai", "title": "Inteligencia artificial",
                     "text": "Agentes de IA para prospección y monitoreo de opiniones en tiempo real.",
                     "link": ("/prospeccion-con-ia/", "Ver prospección con IA")},
                    {"icon": "i-teach", "title": "Capacitación para equipos",
                     "text": "Workshops prácticos en inteligencia artificial y marketing aplicados a la inteligencia comercial."},
                ],
            },
            {
                "type": "prose", "id": "para-quien", "eyebrow": "Con quién trabajamos",
                "title": "¿Para quién trabajamos?",
                "paras": ["Trabajamos con empresas de toda la provincia y, de forma remota, con empresas de todo el país."],
                "checks": [
                    "Pymes y comercios",
                    "Empresas de servicios",
                    "Emprendedores en crecimiento",
                    "Instituciones",
                    "Equipos que quieren capacitarse en inteligencia comercial",
                ],
                "two": True,
            },
        ],
        "faq": [
            ("¿Trabajan solo con empresas de Misiones?",
             "No. Nuestra base está en Misiones y trabajamos de forma remota con empresas de todo el país."),
            ("¿Hacen campañas en redes sociales?",
             "Sí. Diseñamos la estrategia y la publicidad en Meta, Google y TikTok, con contenido, seguimiento y reportes de resultados. La gestión de campañas es opcional y a pedido."),
            ("¿Dan capacitaciones o workshops para mi equipo?",
             "Sí. Capacitamos a tu equipo en inteligencia artificial y estrategias de marketing aplicadas a la inteligencia comercial, con talleres prácticos pensados para la realidad de cada empresa."),
            ("¿Tiene costo la primera reunión?",
             "No. La primera charla para conocer tu caso es sin cargo. Después te pasamos una propuesta a medida, sin compromiso."),
            COMO_EMPEZAR,
        ],
    },
]


if __name__ == "__main__":
    for page in PAGES:
        out = ROOT / page["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(render(page), encoding="utf8", newline="\n")
        print("generada:", out.relative_to(ROOT))
