/* =========================================================
   CONFIGURACIÓN: completar con los datos reales
   ========================================================= */
var CONFIG = {
  whatsapp: "5493764511106",            // Código país + área + número, sin + ni espacios
  whatsappMsg: "Hola, quiero mi diagnóstico inicial",
  email: "cliencia.consultora@gmail.com", // Email de contacto que se muestra en la página
  formEndpoint: "https://formsubmit.co/ajax/cliencia.consultora@gmail.com", // FormSubmit: reenvía cada consulta a ese email
  socials: { instagram: "", linkedin: "", facebook: "" }
};

(function(){
  document.body.classList.remove('no-js');
  document.getElementById('year').textContent = new Date().getFullYear();

  /* Eventos de conversión (GA4 + píxel de Meta, si están cargados) */
  function track(name, params){
    try{ if(typeof gtag==='function') gtag('event', name, params||{}); }catch(e){}
    try{
      if(typeof fbq==='function'){
        if(name==='generate_lead') fbq('track','Lead');
        else if(name.indexOf('whatsapp')===0) fbq('track','Contact');
      }
    }catch(e){}
  }

  /* Enlaces de WhatsApp, email y redes */
  var waUrl = 'https://wa.me/' + CONFIG.whatsapp + '?text=' + encodeURIComponent(CONFIG.whatsappMsg);
  document.querySelectorAll('.js-wa').forEach(function(a){
    a.href = waUrl;
    a.addEventListener('click', function(){ track('whatsapp_click', {ubicacion: a.dataset.track || 'whatsapp'}); });
  });
  document.querySelectorAll('.js-mail').forEach(function(a){ a.href='mailto:'+CONFIG.email; a.textContent=CONFIG.email; });
  document.querySelectorAll('.js-social').forEach(function(a){
    var u = CONFIG.socials[a.dataset.net];
    if(u) a.href = u; else a.style.display = 'none';
  });
  document.querySelectorAll('[data-track^="cta_"]').forEach(function(a){
    a.addEventListener('click', function(){ track('cta_click', {ubicacion: a.dataset.track}); });
  });

  /* Header: sombra al hacer scroll + menú móvil */
  var header = document.getElementById('header');
  var toggle = header.querySelector('.menu-toggle');
  function onScroll(){ header.classList.toggle('scrolled', window.scrollY > 10); }
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  function setMenu(open){
    header.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', open);
    toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
  }
  toggle.addEventListener('click', function(){ setMenu(!header.classList.contains('menu-open')); });
  header.querySelectorAll('.mobile-menu a, .nav-cta, .brand').forEach(function(a){ a.addEventListener('click', function(){ setMenu(false); }); });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') setMenu(false); });
  window.addEventListener('resize', function(){ if(window.innerWidth >= 1080) setMenu(false); });

  /* Resaltar sección activa en el menú */
  var links = document.querySelectorAll('.nav-links a, .mobile-menu a');
  var ids = ['quienes-somos','servicios','como-trabajamos','por-que-elegirnos','preguntas','contacto'];
  var sections = ids.map(function(id){ return document.getElementById(id); });
  function setActive(){
    var y = window.scrollY + window.innerHeight * 0.35, current = '';
    sections.forEach(function(s){ if(s && s.offsetTop <= y) current = s.id; });
    links.forEach(function(a){ a.classList.toggle('active', a.getAttribute('href') === '#'+current); });
  }
  if(sections.some(Boolean)){ window.addEventListener('scroll', setActive, {passive:true}); setActive(); }

  /* Animación de aparición */
  if('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add('in'); io.unobserve(en.target); } });
    }, {rootMargin:'0px 0px -8% 0px', threshold:.08});
    document.querySelectorAll('.reveal').forEach(function(el){ io.observe(el); });
  } else {
    document.querySelectorAll('.reveal').forEach(function(el){ el.classList.add('in'); });
  }

  /* Política de privacidad */
  var dlg = document.getElementById('privacy');
  document.querySelectorAll('.js-privacy').forEach(function(b){
    b.addEventListener('click', function(){ if(dlg.showModal) dlg.showModal(); else dlg.setAttribute('open',''); });
  });
  dlg.querySelector('.dlg-close').addEventListener('click', function(){ dlg.close ? dlg.close() : dlg.removeAttribute('open'); });
  dlg.addEventListener('click', function(e){ if(e.target === dlg) dlg.close(); });

  /* Formulario: validación y envío */
  var form = document.getElementById('form-diagnostico');
  if(!form) return;
  var status = document.getElementById('form-status');
  var submit = document.getElementById('f-submit');
  var rules = {
    nombre: function(v){ return v.trim().length >= 3; },
    empresa: function(v){ return v.trim().length >= 2; },
    rubro: function(v){ return v.trim().length >= 2; },
    email: function(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()); },
    telefono: function(v){ return v.replace(/\D/g,'').length >= 8; }
  };
  function validateField(name){
    var input = form.elements[name], ok = rules[name](input.value);
    input.closest('.field').classList.toggle('invalid', !ok);
    input.setAttribute('aria-invalid', !ok);
    return ok;
  }
  Object.keys(rules).forEach(function(name){
    var input = form.elements[name];
    input.addEventListener('blur', function(){ if(input.value) validateField(name); });
    input.addEventListener('input', function(){ if(input.closest('.field').classList.contains('invalid')) validateField(name); });
  });
  var priv = form.elements.privacidad, privBox = document.getElementById('check-priv');
  priv.addEventListener('change', function(){ privBox.classList.toggle('invalid', !priv.checked); });

  form.addEventListener('submit', function(e){
    e.preventDefault();
    status.className = 'form-status'; status.textContent = '';
    var firstBad = null;
    Object.keys(rules).forEach(function(name){ if(!validateField(name) && !firstBad) firstBad = form.elements[name]; });
    privBox.classList.toggle('invalid', !priv.checked);
    if(!priv.checked && !firstBad) firstBad = priv;
    if(firstBad){ firstBad.focus(); return; }
    if(form.elements._gotcha.value) return; // spam

    var data = {
      nombre: form.elements.nombre.value.trim(),
      empresa: form.elements.empresa.value.trim(),
      rubro: form.elements.rubro.value.trim(),
      email: form.elements.email.value.trim(),
      telefono: form.elements.telefono.value.trim(),
      mensaje: form.elements.mensaje.value.trim(),
      _subject: 'Nuevo pedido de diagnóstico inicial - cliencIA',
      _template: 'table',
      _replyto: form.elements.email.value.trim()
    };

    function done(){
      status.className = 'form-status ok';
      status.textContent = '¡Gracias, ' + data.nombre.split(' ')[0] + '! Recibimos tu pedido de diagnóstico. Te vamos a contactar a la brevedad.';
      form.reset();
      track('generate_lead', {form: 'diagnostico_inicial'});
    }
    function fail(){
      status.className = 'form-status fail';
      status.innerHTML = 'No pudimos enviar el formulario. Probá de nuevo o escribinos por <a href="' + waUrl + '" target="_blank" rel="noopener">WhatsApp</a>.';
    }

    if(!CONFIG.formEndpoint){
      // Sin endpoint configurado: se abre el cliente de correo con los datos cargados.
      var body = Object.keys(data).filter(function(k){ return k.charAt(0) !== '_'; })
        .map(function(k){ return k.charAt(0).toUpperCase() + k.slice(1) + ': ' + (data[k] || '-'); }).join('\n');
      window.location.href = 'mailto:' + CONFIG.email + '?subject=' + encodeURIComponent(data._subject) + '&body=' + encodeURIComponent(body);
      done();
      return;
    }

    submit.disabled = true; submit.textContent = 'Enviando…';
    fetch(CONFIG.formEndpoint, {
      method: 'POST',
      headers: {'Content-Type':'application/json','Accept':'application/json'},
      body: JSON.stringify(data)
    }).then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(res){ if(res && String(res.success) === 'false') throw new Error(res.message); done(); })
      .catch(fail)
      .finally(function(){ submit.disabled = false; submit.textContent = 'Quiero mi diagnóstico'; });
  });
})();
