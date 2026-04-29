/// <reference types="vite/client" />

declare module '*.vue' {
  import type {DefineComponent} from 'vue';

  const component: DefineComponent<Record<string, never>, Record<string, never>, unknown>;
  export default component;
}

declare global {
  const uni:
    | {
        getStorageSync: (key: string) => unknown;
        setStorageSync: (key: string, value: unknown) => void;
        removeStorageSync?: (key: string) => void;
      }
    | undefined;
}
