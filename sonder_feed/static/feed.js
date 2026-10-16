// Only playback disclosure needs JavaScript. Votes and follows use Flask forms.
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-player-toggle]");
  if (!button) return;
  const panel = document.getElementById(button.dataset.playerToggle);
  const opening = panel.hidden;
  if (opening) {
    const player = panel.querySelector("iframe");
    if (!player.getAttribute("src")) player.src = player.dataset.src;
  }
  panel.hidden = !opening;
  button.setAttribute("aria-expanded", String(opening));
});
