import type zhCN from "@/lib/i18n/zh-CN";

type Messages = typeof zhCN;

declare global {
  interface IntlMessages extends Messages {}
}
