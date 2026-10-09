const PREVIOUS_SELECTOR = '.pagination-nav__link--prev';
const NEXT_SELECTOR = '.pagination-nav__link--next';

function isTypingTarget(target) {
  if (!(target instanceof Element)) {
    return false;
  }
  const field = target.closest('input, textarea, select, [contenteditable="true"]');
  return Boolean(field) || target.getAttribute('role') === 'textbox';
}

function openPaginationLink(selector) {
  const link = document.querySelector(selector);
  if (!(link instanceof HTMLAnchorElement) || !link.href) {
    return;
  }
  link.click();
}

function onKeyDown(event) {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
    return;
  }
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') {
    return;
  }
  if (isTypingTarget(event.target)) {
    return;
  }
  const selector = event.key === 'ArrowLeft' ? PREVIOUS_SELECTOR : NEXT_SELECTOR;
  if (!document.querySelector(selector)) {
    return;
  }
  event.preventDefault();
  openPaginationLink(selector);
}

if (typeof window !== 'undefined') {
  window.addEventListener('keydown', onKeyDown);
}
