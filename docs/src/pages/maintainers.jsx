import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

import {avatarUrl, maintainers, roleLabel} from '@site/src/data/maintainers';
import styles from './maintainers.module.css';

const PAGE_COPY = {
  en: {
    title: 'Maintainers',
    description: 'The people who maintain Gitee PR-Agent.',
    ledeBefore: 'PR-Agent was started at ',
    ledeMiddle: ' in July 2023. In April 2026 Qodo donated it to the open-source community, and it now lives in the ',
    ledeAfter: ', maintained by the people below.',
    organization: 'PR-Agent organization on GitHub',
    join: 'The project is open to new contributors and maintainers. ',
    guide: 'Read the contributing guide',
  },
  'zh-CN': {
    title: '维护者',
    description: '维护 Gitee PR-Agent 的人们。',
    ledeBefore: 'PR-Agent 于 2023 年 7 月在 ',
    ledeMiddle: ' 创立。2026 年 4 月，Qodo 将其捐赠给开源社区。项目现由 ',
    ledeAfter: ' 托管，并由以下人员维护。',
    organization: 'GitHub 上的 PR-Agent 组织',
    join: '项目欢迎新的贡献者和维护者。',
    guide: '阅读贡献指南',
  },
};

function MaintainerCard({login, name, role}) {
  const label = roleLabel(role, 'zh-CN');
  return (
    <li className={styles.card}>
      <img
        className={styles.avatar}
        src={avatarUrl(login, 160)}
        alt=""
        width="80"
        height="80"
        loading="lazy"
      />
      <Link className={styles.name} to={`https://github.com/${login}`}>
        {name}
      </Link>
      <span className={styles.role}>{label}</span>
      <span className={styles.handle}>
        <span className="pra-logo pra-logo--github" aria-hidden="true" />@{login}
      </span>
    </li>
  );
}

export default function Maintainers() {
  const copy = PAGE_COPY['zh-CN'];
  return (
    <Layout title={copy.title} description={copy.description}>
      <main className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>{copy.title}</h1>
          <p className={styles.lede}>
            {copy.ledeBefore}<Link to="https://www.qodo.ai/">Qodo</Link>{copy.ledeMiddle}
            <Link to="https://github.com/the-pr-agent">{copy.organization}</Link>{copy.ledeAfter}
          </p>
          <p className={styles.join}>
            {copy.join}{' '}
            <Link to="https://github.com/the-pr-agent/pr-agent/blob/main/CONTRIBUTING.md">
              {copy.guide}
            </Link>
          </p>
        </header>
        <ul className={styles.grid}>
          {maintainers.map((maintainer) => (
            <MaintainerCard key={maintainer.login} {...maintainer} />
          ))}
        </ul>
      </main>
    </Layout>
  );
}
