"use client";
import { useEffect, useRef, useCallback } from "react";
import { Editor, rootCtx, defaultValueCtx, editorViewCtx } from "@milkdown/core";
import { commonmark } from "@milkdown/preset-commonmark";
import { history } from "@milkdown/plugin-history";
import { listener, listenerCtx } from "@milkdown/plugin-listener";
import { useDebouncedCallback } from "use-debounce";

interface MilkdownEditorProps {
  content: string;
  onChange: (markdown: string) => void;
  placeholder?: string;
}

export function MilkdownEditor({
  content,
  onChange,
  placeholder = "开始记录今天的学习…",
}: MilkdownEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<Editor | null>(null);
  const isMounted = useRef(false);

  const debouncedOnChange = useDebouncedCallback(onChange, 500);

  const initEditor = useCallback(async () => {
    if (!containerRef.current || isMounted.current) return;
    isMounted.current = true;

    const editor = await Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, containerRef.current!);
        ctx.set(defaultValueCtx, content || `# 今日学习\n\n${placeholder}`);
        ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
          debouncedOnChange(markdown);
        });
      })
      .use(commonmark)
      .use(history)
      .use(listener)
      .create();

    editorRef.current = editor;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    initEditor();
    return () => {
      editorRef.current?.destroy();
      isMounted.current = false;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      ref={containerRef}
      className="milkdown-editor min-h-[60vh] focus-within:outline-none prose prose-sm max-w-none text-text-main"
      style={{ lineHeight: "1.8" }}
    />
  );
}
