(() => {
  const area = document.getElementById('office-panorama');
  const links = Array.from(document.querySelectorAll('.tour-scenes a'));
  const hint = document.querySelector('.tour-hint');
  if (!window.pannellum) return;
  const still = area.firstElementChild.cloneNode();
  const dir = new URL('.', document.currentScript.src);
  const photo = name => new URL(name + '.webp', dir).href;
  const names = Object.fromEntries(links.map(link => [link.dataset.scene, link.textContent]));
  const scenes = {};
  function scene(id, yaw, pitch, target, direction, height) {
    scenes[id] = {
      type: 'equirectangular', panorama: photo(id), yaw, pitch, hfov: 105,
      hotSpots: [{ type: 'scene', sceneId: target, text: names[target], yaw: direction, pitch: height }]
    };
  }
  scene('reception', -6, -3, 'lounge', -45, -13);
  scene('lounge', 37, -5, 'reception', 151, -3);
  let viewer;
  let ready = false;
  function select(current) {
    for (const link of links) {
      if (link.dataset.scene === current) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    }
  }
  function fallback() {
    const id = viewer?.getScene() || 'reception';
    ready = false;
    viewer?.destroy();
    const link = links.find(link => link.dataset.scene === id) || links[0];
    still.src = link.href;
    still.alt = names[id] || names.reception;
    area.replaceChildren(still);
    select(id);
    hint.textContent = 'Круговой просмотр недоступен. Выберите точку, чтобы открыть фото.';
  }
  try {
    area.replaceChildren();
    viewer = window.pannellum.viewer(area, {
      default: { firstScene: 'reception', autoLoad: true, mouseZoom: 'fullscreenonly',
        sceneFadeDuration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 220,
        strings: { loadingLabel: 'Загрузка панорамы…' } },
      scenes
    });
    viewer.on('load', () => {
      ready = true;
      hint.textContent = 'Поворачивайте обзор пальцем или мышью. Стрелка ведёт к соседней точке.';
    });
    viewer.on('scenechange', select);
    viewer.on('error', fallback);
    for (const link of links) link.addEventListener('click', event => {
      if (!ready || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (viewer.getScene() !== link.dataset.scene) viewer.loadScene(link.dataset.scene);
    });
  } catch {
    fallback();
  }
})();
