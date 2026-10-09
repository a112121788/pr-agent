/**
 * List the people shown on /maintainers/, in display order.
 *
 * Set `login` to the GitHub username; it drives the avatar and the profile link.
 * Set `name` to the login when the maintainer has no public display name.
 */
export const maintainers = [
  {login: 'naorpeled', name: 'Naor Peled', role: 'Lead Maintainer'},
  {login: 'ofir-frd', name: 'ofir-frd', role: 'Maintainer'},
  {login: 'IsmaelMartinez', name: 'IsmaelMartinez', role: 'Maintainer'},
  {login: 'DanaFineTLV', name: 'Dana Fine', role: 'Community Manager'},
];

const ROLE_LABELS = {
  'zh-CN': {
    'Lead Maintainer': '主要维护者',
    Maintainer: '维护者',
    'Community Manager': '社区经理',
  },
};

/** Return the role in the current locale. Names and logins stay unchanged. */
export function roleLabel(role, locale) {
  return ROLE_LABELS[locale]?.[role] || role;
}

/** Return the GitHub avatar URL for `login` at `size` pixels. */
export function avatarUrl(login, size) {
  return `https://avatars.githubusercontent.com/${login}?s=${size}`;
}
