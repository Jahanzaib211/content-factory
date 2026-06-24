import React, { useState, useEffect } from 'react';
import { Key, Eye, EyeOff, Check, Sparkles } from 'lucide-react';

export default function KeyInput({
    onKeySet,
    savedKey,
    title = 'Gemini API Key',
    iconClass = 'bg-accent/20 text-accent',
    placeholder = 'AIzaSy...',
    getKeyHref = 'https://aistudio.google.com/app/apikey',
    getKeyLabel = 'Get your free Gemini API Key here',
    storageKey: _storageKey = 'gemini_key',
}) {
    const [key, setKey] = useState(savedKey || '');
    const [isVisible, setIsVisible] = useState(false);
    const [isSaved, setIsSaved] = useState(!!savedKey);

    useEffect(() => {
        if (savedKey) setKey(savedKey);
    }, [savedKey]);

    const handleSave = () => {
        if (key.trim().length > 0) {
            onKeySet(key);
            setIsSaved(true);
        }
    };

    return (
        <div className="bg-surface border border-white/5 rounded-2xl p-6 mb-8 animate-[fadeIn_0.5s_ease-out]">
            <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg ${iconClass}`}>
                    <Key size={20} />
                </div>
                <h2 className="text-lg font-semibold">{title}</h2>
            </div>

            <div className="flex gap-3">
                <div className="relative flex-1">
                    <input
                        type={isVisible ? 'text' : 'password'}
                        value={key}
                        onChange={(e) => {
                            setKey(e.target.value);
                            setIsSaved(false);
                        }}
                        placeholder={placeholder}
                        className="input-field pr-12 font-mono"
                    />
                    <button
                        onClick={() => setIsVisible(!isVisible)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white transition-colors"
                    >
                        {isVisible ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                </div>
                <button
                    onClick={handleSave}
                    disabled={!key || isSaved}
                    className={`px-6 rounded-xl font-medium transition-all flex items-center gap-2 ${
                        isSaved
                            ? 'bg-green-500/20 text-green-400 cursor-default'
                            : 'bg-primary hover:bg-blue-600 text-white shadow-lg shadow-primary/20'
                    }`}
                >
                    {isSaved ? (
                        <>
                            <Check size={18} /> Ready
                        </>
                    ) : (
                        'Set Key'
                    )}
                </button>
            </div>
            <p className="mt-3 text-xs text-zinc-500">
                Your key is stored locally in your browser for convenience.
                <br />
                <a
                    href={getKeyHref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline mt-1 inline-block"
                >
                    {getKeyLabel} →
                </a>
            </p>
        </div>
    );
}

export function MiniMaxKeyInput({ onKeySet, savedKey }) {
    return (
        <KeyInput
            onKeySet={onKeySet}
            savedKey={savedKey}
            title="MiniMax API Key"
            iconClass="bg-violet-500/20 text-violet-300"
            placeholder="sk-cp-..."
            getKeyHref="https://api.MiniMax.io"
            getKeyLabel="Get your MiniMax API Key"
            storageKey="minimax_key_v1"
        />
    );
}