type UniStorage = {
  getStorageSync?: (key: string) => unknown;
  setStorageSync?: (key: string, value: unknown) => void;
  removeStorageSync?: (key: string) => void;
};

const getUniStorage = (): UniStorage | null => {
  const candidate = globalThis as typeof globalThis & {uni?: UniStorage};
  return candidate.uni ?? null;
};

export const canUseStorage = () => {
  const uni = getUniStorage();
  if (uni?.getStorageSync && uni?.setStorageSync) return true;

  return typeof globalThis.localStorage !== 'undefined';
};

export const getStorageItem = (key: string) => {
  const uni = getUniStorage();
  if (uni?.getStorageSync) {
    const value = uni.getStorageSync(key);
    return typeof value === 'string' ? value : null;
  }

  if (typeof globalThis.localStorage !== 'undefined') {
    return globalThis.localStorage.getItem(key);
  }

  return null;
};

export const setStorageItem = (key: string, value: string) => {
  const uni = getUniStorage();
  if (uni?.setStorageSync) {
    uni.setStorageSync(key, value);
    return;
  }

  if (typeof globalThis.localStorage !== 'undefined') {
    globalThis.localStorage.setItem(key, value);
  }
};

export const removeStorageItem = (key: string) => {
  const uni = getUniStorage();
  if (uni?.removeStorageSync) {
    uni.removeStorageSync(key);
    return;
  }

  if (typeof globalThis.localStorage !== 'undefined') {
    globalThis.localStorage.removeItem(key);
  }
};
