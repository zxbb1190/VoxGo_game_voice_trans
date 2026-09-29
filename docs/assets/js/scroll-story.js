/* The text remains in HTML. This only changes the accompanying HUD scene. */
(function () {
  var shell = document.querySelector('.story-shell');
  if (!shell || !('IntersectionObserver' in window) ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var steps = shell.querySelectorAll('.story-step');
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) shell.dataset.active = entry.target.dataset.scene;
    });
  }, { rootMargin: '-38% 0px -42% 0px', threshold: 0 });

  steps.forEach(function (step) { observer.observe(step); });
})();
