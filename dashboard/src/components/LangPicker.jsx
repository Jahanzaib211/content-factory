import React from 'react';
import { useT } from '../i18n/I18nProvider';

export default function LangPicker() {
  const { lang, setLang, SUPPORTED } = useT();
  return (
    <select
      value={lang}
      onChange={(e) => setLang(e.target.value)}
      className="bg-black/50 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500"
    >
      {SUPPORTED.map((l) => (
        <option key={l} value={l}>{l.toUpperCase()}</option>
      ))}
    </select>
  );
}
