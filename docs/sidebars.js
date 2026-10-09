/**
 * Four sidebars, one per navbar tab. Groups are non-collapsible so every page in
 * a tab stays visible; each group answers one question a reader arrives with.
 *
 * The Overview (`index`) is the landing page at `/`, reached from the navbar logo,
 * so it is deliberately not listed here. Each tab opens its first entry.
 */

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // How do I start using it?
  getStarted: [
    {type: 'doc', id: 'usage-guide/introduction', label: '简介'},
    {type: 'doc', id: 'overview/review_factory', label: '审核工厂'},
    {type: 'doc', id: 'overview/supported_platforms', label: '支持的平台'},
    {
      type: 'category',
      label: '安装',
      collapsible: false,
      link: {type: 'doc', id: 'installation/index'},
      // `className` draws the provider's logo before the label (provider-logos.css).
      items: [
        {type: 'doc', id: 'installation/locally', label: '本地', className: 'pra-side-provider pra-side-terminal'},
        {type: 'doc', id: 'installation/gitee', label: 'Gitee'},
      ],
    },
    {type: 'doc', id: 'overview/data_privacy', label: '数据隐私'},
    {type: 'doc', id: 'faq/index', label: '常见问题'},
  ],

  // How do I run and configure it day to day?
  guides: [
    {type: 'doc', id: 'usage-guide/index', label: '概览'},
    {
      type: 'category',
      label: '运行',
      collapsible: false,
      items: [
        {type: 'doc', id: 'usage-guide/automations_and_usage', label: '用法与自动化'},
        {type: 'doc', id: 'usage-guide/push_outputs', label: '推送输出'},
        {type: 'doc', id: 'usage-guide/mail_notifications', label: '邮件通知'},
      ],
    },
    {
      type: 'category',
      label: '配置',
      collapsible: false,
      items: [
        {type: 'doc', id: 'usage-guide/configuration_options', label: '配置文件'},
        {type: 'doc', id: 'usage-guide/changing_a_model', label: '更换模型'},
        {type: 'doc', id: 'usage-guide/additional_configurations', label: '其他配置'},
        {type: 'doc', id: 'usage-guide/custom_ca_and_self_signed_certificates', label: '自定义 CA 证书'},
        {type: 'doc', id: 'usage-guide/configuration_reference', label: '配置参考'},
      ],
    },
    {
      type: 'category',
      label: '参与贡献',
      collapsible: false,
      items: [{type: 'doc', id: 'usage-guide/extending_pr_agent', label: '扩展 PR-Agent'}],
    },
  ],

  // What does each command do?
  tools: [
    {type: 'doc', id: 'tools/index', label: '概览'},
    {
      // The commands that run on a pull request by default or are used most.
      type: 'category',
      label: '主要工具',
      collapsible: false,
      items: [
        {type: 'doc', id: 'tools/describe', label: '描述'},
        {type: 'doc', id: 'tools/review', label: '审查'},
        {type: 'doc', id: 'tools/improve', label: '改进'},
        {type: 'doc', id: 'tools/ask', label: '提问'},
      ],
    },
    {
      type: 'category',
      label: '更多工具',
      collapsible: false,
      items: [
        {type: 'doc', id: 'tools/add_docs', label: '补充文档'},
        {type: 'doc', id: 'tools/generate_labels', label: '生成标签'},
        {type: 'doc', id: 'tools/update_changelog', label: '更新变更日志'},
        {type: 'doc', id: 'tools/similar_issues', label: '相似问题'},
      ],
    },
    {
      type: 'category',
      label: '帮助',
      collapsible: false,
      items: [
        {type: 'doc', id: 'tools/help', label: '帮助'},
      ],
    },
  ],

  // How does it work under the hood?
  coreAbilities: [
    {type: 'doc', id: 'core-abilities/index', label: '概览'},
    {type: 'doc', id: 'core-abilities/agent_skills', label: '代理技能'},
    {type: 'doc', id: 'core-abilities/compression_strategy', label: '压缩策略'},
    {type: 'doc', id: 'core-abilities/dynamic_context', label: '动态上下文'},
    {type: 'doc', id: 'core-abilities/fetching_ticket_context', label: '获取工单上下文'},
    {type: 'doc', id: 'core-abilities/metadata', label: '本地与全局元数据'},
    {type: 'doc', id: 'core-abilities/self_reflection', label: '自我反思'},
  ],
};

module.exports = sidebars;
