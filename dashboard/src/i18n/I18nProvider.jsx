"""
Lightweight React i18n hook for Content Factory.

Use:  const t = useT();  <h1>{t('nav.factory')}</h1>

Lang is stored in localStorage('cf_lang') and reactive. A top-level
<LangPicker /> in the Multilingual settings card writes to the same
key, so all components re-render on language change.
"""
import React, { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';
import { MESSAGES, SUPPORTED, DEFAULT_LANG } from './messages';

const STORAGE_KEY = 'cf_lang';

const I18nContext = createContext({
  lang: DEFAULT_LANG,
  setLang: () => {},
  t: (key) => key,
  SUPPORTED,
});

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && SUPPORTED.includes(stored)) return stored;
    } catch (_) {}
    return DEFAULT_LANG;
  });

  const setLang = useCallback((newLang) => {
    if (!SUPPORTED.includes(newLang)) return;
    try { localStorage.setItem(STORAGE_KEY, newLang); } catch (_) {}
    setLangState(newLang);
    // Reflect in <html lang="..."> for accessibility / SEO
    if (typeof document !== 'undefined') {
      document.documentElement.lang = newLang;
    }
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang;
    }
  }, [lang]);

  const t = useCallback((key) => {
    const msgs = MESSAGES[lang] || MESSAGES[DEFAULT_LANG];
    if (msgs[key] != null) return msgs[key];
    const en = MESSAGES[DEFAULT_LANG];
    return (en && en[key] != null) ? en[key] : key;
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, t, SUPPORTED }), [lang, setLang, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT() {
  return useContext(I18nContext);
}

export function useLang() {
  return useContext(I18nContext).lang;
}
