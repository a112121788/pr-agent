import React from 'react';

import {avatarUrl, maintainers, roleLabel} from '@site/src/data/maintainers';
import styles from './styles.module.css';

/** Render the maintainers' avatars in a row, for the landing page. */
export default function MaintainerAvatars() {
  const locale = 'zh-CN';
  return (
    <ul className={styles.row}>
      {maintainers.map(({login, name, role}) => {
        const label = roleLabel(role, locale);
        return (
        <li key={login} className={styles.item}>
          <img
            // `no-frame` opts out of the doc-image frame and click-to-zoom.
            className={`no-frame ${styles.avatar}`}
            src={avatarUrl(login, 112)}
            alt={`${name}, ${label}`}
            title={`${name} · ${label}`}
            width="56"
            height="56"
            loading="lazy"
          />
        </li>
        );
      })}
    </ul>
  );
}
