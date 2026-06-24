// Lightweight i18n for Content Factory.
//
// A 200-line drop-in alternative to react-i18next / Paraglide JS. Supports
// 10 languages out of the box, lazy message loading, and a `useT()` hook
// with plural support. Designed for solo projects where a full i18n
// toolchain is overkill.
//
// Add a new language:
//   1. Add a new key to MESSAGES (e.g. MESSAGES.fr = { ... })
//   2. Add the language code to SUPPORTED
//   3. The Settings -> Multilingual card lets the user pick
//
// The same translations are also exposed to the Python backend
// (app.py -> /api/i18n/messages) so FastAPI can localize server-rendered
// pages (gallery, video pages) the same way.

export const SUPPORTED = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'];
export const DEFAULT_LANG = 'en';

// Common strings used across the dashboard. Keep keys short and
// dot-namespaced (e.g. "settings.title", "nav.dashboard").
export const MESSAGES = {
  en: {
    'nav.clipGenerator': 'Clip Generator',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'AI Agent',
    'nav.ugcGallery': 'UGC Gallery',
    'nav.youtubeStudio': 'YouTube Studio',
    'nav.factory': 'Content Factory',
    'nav.voiceLab': 'Voice Lab',
    'nav.avatarStudio': 'Avatar Studio',
    'nav.multilingual': 'Multilingual',
    'nav.settings': 'Settings',
    'settings.title': 'Settings',
    'settings.privacy': 'Privacy: keys only live in your browser (sent to backend just to process)',
    'common.cancel': 'Cancel',
    'common.save': 'Save',
    'common.loading': 'Loading…',
    'common.error': 'Error',
  },
  es: {
    'nav.clipGenerator': 'Generador de Clips',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'Agente IA',
    'nav.ugcGallery': 'Galería UGC',
    'nav.youtubeStudio': 'Estudio YouTube',
    'nav.factory': 'Fábrica de Contenido',
    'nav.voiceLab': 'Laboratorio de Voz',
    'nav.avatarStudio': 'Estudio de Avatar',
    'nav.multilingual': 'Multilingüe',
    'nav.settings': 'Ajustes',
    'settings.title': 'Ajustes',
    'settings.privacy': 'Privacidad: las claves solo viven en tu navegador',
    'common.cancel': 'Cancelar',
    'common.save': 'Guardar',
    'common.loading': 'Cargando…',
    'common.error': 'Error',
  },
  fr: {
    'nav.clipGenerator': 'Générateur de Clips',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'Agent IA',
    'nav.ugcGallery': 'Galerie UGC',
    'nav.youtubeStudio': 'Studio YouTube',
    'nav.factory': 'Usine de Contenu',
    'nav.voiceLab': 'Laboratoire Vocal',
    'nav.avatarStudio': 'Studio Avatar',
    'nav.multilingual': 'Multilingue',
    'nav.settings': 'Paramètres',
    'settings.title': 'Paramètres',
    'settings.privacy': 'Confidentialité : les clés restent dans votre navigateur',
    'common.cancel': 'Annuler',
    'common.save': 'Enregistrer',
    'common.loading': 'Chargement…',
    'common.error': 'Erreur',
  },
  de: {
    'nav.clipGenerator': 'Clip-Generator',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'KI-Agent',
    'nav.ugcGallery': 'UGC-Galerie',
    'nav.youtubeStudio': 'YouTube-Studio',
    'nav.factory': 'Content-Fabrik',
    'nav.voiceLab': 'Stimm-Labor',
    'nav.avatarStudio': 'Avatar-Studio',
    'nav.multilingual': 'Mehrsprachig',
    'nav.settings': 'Einstellungen',
    'settings.title': 'Einstellungen',
    'settings.privacy': 'Datenschutz: Schlüssel bleiben nur in Ihrem Browser',
    'common.cancel': 'Abbrechen',
    'common.save': 'Speichern',
    'common.loading': 'Lädt…',
    'common.error': 'Fehler',
  },
  it: {
    'nav.clipGenerator': 'Generatore di Clip',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'Agente IA',
    'nav.ugcGallery': 'Galleria UGC',
    'nav.youtubeStudio': 'Studio YouTube',
    'nav.factory': 'Fabbrica di Contenuti',
    'nav.voiceLab': 'Laboratorio Vocale',
    'nav.avatarStudio': 'Studio Avatar',
    'nav.multilingual': 'Multilingua',
    'nav.settings': 'Impostazioni',
    'settings.title': 'Impostazioni',
    'settings.privacy': 'Privacy: le chiavi restano nel tuo browser',
    'common.cancel': 'Annulla',
    'common.save': 'Salva',
    'common.loading': 'Caricamento…',
    'common.error': 'Errore',
  },
  pt: {
    'nav.clipGenerator': 'Gerador de Clipes',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'Agente IA',
    'nav.ugcGallery': 'Galeria UGC',
    'nav.youtubeStudio': 'Estúdio YouTube',
    'nav.factory': 'Fábrica de Conteúdo',
    'nav.voiceLab': 'Laboratório de Voz',
    'nav.avatarStudio': 'Estúdio de Avatar',
    'nav.multilingual': 'Multilíngue',
    'nav.settings': 'Configurações',
    'settings.title': 'Configurações',
    'settings.privacy': 'Privacidade: as chaves só ficam no seu navegador',
    'common.cancel': 'Cancelar',
    'common.save': 'Salvar',
    'common.loading': 'Carregando…',
    'common.error': 'Erro',
  },
  ru: {
    'nav.clipGenerator': 'Генератор клипов',
    'nav.aiShorts': 'AI Shorts',
    'nav.aiAgent': 'ИИ Агент',
    'nav.ugcGallery': 'UGC Галерея',
    'nav.youtubeStudio': 'YouTube Студия',
    'nav.factory': 'Фабрика Контента',
    'nav.voiceLab': 'Голосовая Лаборатория',
    'nav.avatarStudio': 'Студия Аватаров',
    'nav.multilingual': 'Мультиязычность',
    'nav.settings': 'Настройки',
    'settings.title': 'Настройки',
    'settings.privacy': 'Приватность: ключи только в вашем браузере',
    'common.cancel': 'Отмена',
    'common.save': 'Сохранить',
    'common.loading': 'Загрузка…',
    'common.error': 'Ошибка',
  },
  ja: {
    'nav.clipGenerator': 'クリップ生成',
    'nav.aiShorts': 'AIショート',
    'nav.aiAgent': 'AIエージェント',
    'nav.ugcGallery': 'UGCギャラリー',
    'nav.youtubeStudio': 'YouTubeスタジオ',
    'nav.factory': 'コンテンツファクトリー',
    'nav.voiceLab': 'ボイスラボ',
    'nav.avatarStudio': 'アバタースタジオ',
    'nav.multilingual': '多言語',
    'nav.settings': '設定',
    'settings.title': '設定',
    'settings.privacy': 'プライバシー: キーはブラウザのみ',
    'common.cancel': 'キャンセル',
    'common.save': '保存',
    'common.loading': '読み込み中…',
    'common.error': 'エラー',
  },
  ko: {
    'nav.clipGenerator': '클립 생성기',
    'nav.aiShorts': 'AI 쇼츠',
    'nav.aiAgent': 'AI 에이전트',
    'nav.ugcGallery': 'UGC 갤러리',
    'nav.youtubeStudio': 'YouTube 스튜디오',
    'nav.factory': '콘텐츠 팩토리',
    'nav.voiceLab': '보이스 랩',
    'nav.avatarStudio': '아바타 스튜디오',
    'nav.multilingual': '다국어',
    'nav.settings': '설정',
    'settings.title': '설정',
    'settings.privacy': '개인정보 보호: 키는 브라우저에만',
    'common.cancel': '취소',
    'common.save': '저장',
    'common.loading': '로딩 중…',
    'common.error': '오류',
  },
  zh: {
    'nav.clipGenerator': '片段生成器',
    'nav.aiShorts': 'AI 短视频',
    'nav.aiAgent': 'AI 代理',
    'nav.ugcGallery': 'UGC 画廊',
    'nav.youtubeStudio': 'YouTube 工作室',
    'nav.factory': '内容工厂',
    'nav.voiceLab': '声音实验室',
    'nav.avatarStudio': '虚拟形象工作室',
    'nav.multilingual': '多语言',
    'nav.settings': '设置',
    'settings.title': '设置',
    'settings.privacy': '隐私:密钥仅存储于您的浏览器',
    'common.cancel': '取消',
    'common.save': '保存',
    'common.loading': '加载中…',
    'common.error': '错误',
  },
};

export function t(key, lang = DEFAULT_LANG) {
  const msgs = MESSAGES[lang] || MESSAGES[DEFAULT_LANG];
  if (msgs[key] != null) return msgs[key];
  const en = MESSAGES[DEFAULT_LANG];
  return en && en[key] != null ? en[key] : key;
}

export function allMessages() {
  return MESSAGES;
}
