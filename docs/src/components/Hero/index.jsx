import React, {useRef, useState} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';

import styles from './styles.module.css';

const HERO_COPY = {
  en: {
    lede: 'The core machine of the review factory. It gathers evidence on a Gitee pull request; people keep the verdict and the merge.',
    install: 'Install on Gitee',
    github: 'Browse the tools',
    worksWith: 'Runs on',
    type: 'Type',
    enhancement: 'Enhancement',
    description: 'Description',
    retry: 'Retry failed webhook deliveries with exponential backoff',
    record: 'Record every attempt in the delivery log',
    walkthrough: 'File walkthrough',
    reviewGuide: 'PR 审查指南',
    effort: '预计审查工作量',
    effortLabel: '2 out of 5',
    tests: '拉取请求包含测试',
    security: '未发现安全问题',
    focus: '建议重点审查',
    unbounded: 'Unbounded backoff:',
    unboundedTail: 'has no cap, so the tenth retry waits more than eight minutes.',
    suggestions: 'PR 代码建议',
    capDelay: 'Cap the retry delay',
    possibleIssue: 'Possible issue',
    highImpact: 'Impact: High',
    delayExplanation: 'The delay doubles on every attempt with no upper bound. Clamp it so a long outage cannot stall the worker.',
    askAnswer: 'Each delivery is retried up to max_attempts (10) times, doubling the delay from one second. The attempts span about 17 minutes; after the last one the event is marked failed in the delivery log and is not retried again.',
    threadLabel: 'Example: running a PR-Agent command on a pull request',
    commandLabel: 'Command',
    howItWorks: 'How',
    works: 'works',
  },
  'zh-CN': {
    lede: '审核工厂的核心机。它在 Gitee 拉取请求上收集证据；判定和汇入仍由人完成。',
    install: '安装到 Gitee',
    github: '查看工具',
    worksWith: '运行于',
    type: '类型',
    enhancement: '功能增强',
    description: '描述',
    retry: '用指数退避重试失败的 Webhook 投递',
    record: '在投递日志中记录每一次尝试',
    walkthrough: '文件导览',
    reviewGuide: 'PR 审查指南',
    effort: '预计审查工作量',
    effortLabel: '5 分中的 2 分',
    tests: '拉取请求包含测试',
    security: '未发现安全问题',
    focus: '建议重点审查',
    unbounded: '退避没有上限：',
    unboundedTail: '没有上限，因此第十次重试会等待超过八分钟。',
    suggestions: 'PR 代码建议',
    capDelay: '限制重试延迟',
    possibleIssue: '可能的问题',
    highImpact: '影响：高',
    delayExplanation: '每次尝试都会让延迟翻倍，但没有上限。应限制最大值，避免长时间故障拖住工作进程。',
    askAnswer: '每次投递最多重试 max_attempts（10）次，延迟从一秒开始翻倍。全部尝试大约持续 17 分钟；最后一次之后，事件会在投递日志中标记为 failed，并且不再重试。',
    threadLabel: '示例：在拉取请求中运行 PR-Agent 命令',
    commandLabel: '命令',
    howItWorks: '',
    works: '的工作方式',
  },
};

function Mark({className}) {
  const src = useBaseUrl('/img/favicon.svg');
  return <img className={className} src={src} alt="" width={28} height={28} />;
}

function Describe({copy}) {
  return (
    <>
      <dl className={styles.fields}>
        <dt>{copy.type}</dt>
        <dd>{copy.enhancement}</dd>
        <dt>{copy.description}</dt>
        <dd>
          <ul className={styles.bullets}>
            <li>{copy.retry}</li>
            <li>{copy.record}</li>
          </ul>
        </dd>
      </dl>
      <p className={styles.sub}>{copy.walkthrough}</p>
      <ul className={styles.files}>
        <li><code>webhooks/retry.py</code><span className={styles.add}>+48</span><span className={styles.del}>−6</span></li>
        <li><code>webhooks/handler.py</code><span className={styles.add}>+12</span><span className={styles.del}>−3</span></li>
        <li><code>tests/test_retry.py</code><span className={styles.add}>+71</span><span className={styles.del}>−0</span></li>
      </ul>
    </>
  );
}

function Review({copy}) {
  return (
    <>
      <p className={styles.heading}>{copy.reviewGuide}</p>
      <ul className={styles.checks}>
        <li>
          <span>{copy.effort}</span>
          <span className={styles.meter} role="img" aria-label={copy.effortLabel}>
            {[1, 2, 3, 4, 5].map((n) => (
              <i key={n} className={n <= 2 ? styles.on : undefined} />
            ))}
          </span>
        </li>
        <li><span>{copy.tests}</span></li>
        <li><span>{copy.security}</span></li>
      </ul>
      <p className={styles.sub}>{copy.focus}</p>
      <div className={styles.finding}>
        <code>webhooks/retry.py</code> <span className={styles.lines}>L42–51</span>
        <p>
          {copy.unbounded} <code>base * 2 ** attempt</code> {copy.unboundedTail}
        </p>
      </div>
    </>
  );
}

function Improve() {
  return (
    <>
      <p className={styles.heading}>{copy.suggestions}</p>
      <div className={styles.suggestion}>
        <div className={styles.suggestionHead}>
          <span>{copy.capDelay}</span>
          <span className={styles.tags}>
            <span>{copy.possibleIssue}</span>
            <span>{copy.highImpact}</span>
          </span>
        </div>
        <p>{copy.delayExplanation}</p>
        <pre className={styles.diff}>
          <span className={styles.diffFile}>webhooks/retry.py</span>
          <span className={styles.diffDel}>- delay = base * 2 ** attempt</span>
          <span className={styles.diffAdd}>+ delay = min(base * 2 ** attempt, MAX_DELAY)</span>
        </pre>
      </div>
    </>
  );
}

function Ask({copy}) {
  return <p className={styles.answer}>{copy.askAnswer}</p>;
}

const COMMANDS = [
  {id: 'describe', typed: '/describe', Reply: Describe, to: '/tools/describe/'},
  {id: 'review', typed: '/review', Reply: Review, to: '/tools/review/'},
  {id: 'improve', typed: '/improve', Reply: Improve, to: '/tools/improve/'},
  {id: 'ask', typed: '/ask "What happens if the endpoint is down for an hour?"', Reply: Ask, to: '/tools/ask/'},
];

const PROVIDERS = [
  {slug: 'gitee', name: 'Gitee'},
];

function Thread({copy}) {
  const [active, setActive] = useState(1);
  const tabs = useRef([]);
  const {typed, Reply, to, id} = COMMANDS[active];

  const onKeyDown = (event) => {
    const step = {ArrowRight: 1, ArrowLeft: -1}[event.key];
    if (!step) return;
    event.preventDefault();
    const next = (active + step + COMMANDS.length) % COMMANDS.length;
    setActive(next);
    tabs.current[next]?.focus();
  };

  return (
    <figure className={styles.thread} aria-label={copy.threadLabel}>
      <div className={styles.threadHead}>
        <span className={styles.prTitle}>feat: retry failed webhook deliveries</span>
        <span className={styles.prNumber}>#482</span>
      </div>

      <div className={styles.tabs} role="tablist" aria-label={copy.commandLabel} onKeyDown={onKeyDown}>
        {COMMANDS.map((command, index) => (
          <button
            key={command.id}
            ref={(el) => (tabs.current[index] = el)}
            type="button"
            role="tab"
            id={`pra-tab-${command.id}`}
            aria-selected={index === active}
            aria-controls="pra-thread-panel"
            tabIndex={index === active ? 0 : -1}
            className={styles.tab}
            onClick={() => setActive(index)}>
            /{command.id}
          </button>
        ))}
      </div>

      <div
        className={styles.panel}
        role="tabpanel"
        id="pra-thread-panel"
        aria-labelledby={`pra-tab-${id}`}>
        <div className={styles.comment} key={`${id}-typed`}>
          <span className={styles.avatar} aria-hidden="true">M</span>
          <div className={styles.commentBody}>
            <span className={styles.author}>maya</span>
            <code className={styles.typed}>{typed}</code>
          </div>
        </div>

        <div className={`${styles.comment} ${styles.reply}`} key={`${id}-reply`}>
          <span className={`${styles.avatar} ${styles.botAvatar}`} aria-hidden="true">
            <Mark className={styles.botMark} />
          </span>
          <div className={styles.commentBody}>
            <span className={styles.author}>
              pr-agent <span className={styles.bot}>bot</span>
            </span>
            <div className={styles.output}>
              <Reply copy={copy} />
            </div>
          </div>
        </div>
      </div>

      <Link className={styles.threadFoot} to={to}>
        {copy.howItWorks} /{id} {copy.works} →
      </Link>
    </figure>
  );
}

export default function Hero() {
  const copy = HERO_COPY['zh-CN'];
  return (
    <header className={styles.hero}>
      <div className={styles.intro}>
        <h1 className={styles.title}>Gitee PR-Agent</h1>
        <p className={styles.lede}>{copy.lede}</p>
        <div className={styles.actions}>
          <Link className={styles.primary} to="/installation/gitee/">
            {copy.install}
          </Link>
          <Link className={styles.secondary} to="/tools/">
            {copy.github}
          </Link>
        </div>
        <div className={styles.providers}>
          <span className={styles.providersLabel}>{copy.worksWith}</span>
          <ul className={styles.providerList}>
            {PROVIDERS.map(({slug, name}) => (
              <li key={slug} className="pra-provider">
                <span className={`pra-logo pra-logo--${slug}`} aria-hidden="true" />
                {name}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <Thread copy={copy} />
    </header>
  );
}
