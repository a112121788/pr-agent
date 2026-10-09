import React from 'react';
import DocPaginator from '@theme-original/DocPaginator';

/** Replace the theme's English pager words while keeping its links and layout. */
export default function ChineseDocPaginator(props) {
  return (
    <div className="chinese-doc-paginator">
      <DocPaginator {...props} />
    </div>
  );
}
