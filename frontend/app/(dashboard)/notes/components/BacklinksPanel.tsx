"use client";
import { useQuery } from "@tanstack/react-query";
import { notesApi } from "@/lib/api/notes";
import Link from "next/link";
import { LinkIcon, TagIcon } from "lucide-react";

export function BacklinksPanel({ date }: { date: string }) {
  const { data: backlinks = [] } = useQuery({
    queryKey: ["backlinks", date],
    queryFn: () => notesApi.getBacklinks(date),
    enabled: !!date,
  });

  const { data: tags = [] } = useQuery({
    queryKey: ["note_tags", date],
    queryFn: () => notesApi.getTags(date),
    enabled: !!date,
  });

  return (
    <div className="space-y-5">
      {/* 标签云 */}
      {tags.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-text-muted mb-2">
            <TagIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
            标签
          </div>
          <div className="flex flex-wrap gap-1.5">
            {tags.map(({ tag, count }) => (
              <span
                key={tag}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-macaron-lilac/40 text-text-main"
              >
                #{tag}
                {count > 1 && (
                  <span className="ml-1 text-text-muted">{count}</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 反向链接 */}
      <div>
        <div className="flex items-center gap-1.5 text-xs font-semibold text-text-muted mb-2">
          <LinkIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
          反向链接
          {backlinks.length > 0 && (
            <span className="text-text-muted/60">({backlinks.length})</span>
          )}
        </div>
        {backlinks.length === 0 ? (
          <p className="text-text-muted text-xs">暂无其他笔记引用此页</p>
        ) : (
          <ul className="space-y-2">
            {backlinks.map((bl) => (
              <li key={bl.source_date}>
                <Link
                  href={`/notes/${bl.source_date}`}
                  className="block p-2 rounded-md hover:bg-macaron-pink/10 transition-colors"
                >
                  <p className="text-xs font-medium text-text-main">
                    {bl.source_title}
                  </p>
                  <p className="text-xs text-text-muted mt-0.5 line-clamp-2">
                    {bl.excerpt}
                  </p>
                  <p className="text-xs text-text-muted/60 mt-0.5">
                    {bl.source_date}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
