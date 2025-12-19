"""
Internationalization module for DataGuardian.
Provides multilingual support for the application UI.
"""
import os
import json
from typing import Dict, Any, Optional
import streamlit as st

# Available languages
LANGUAGES = {
    'en': 'English',
    'nl': 'Nederlands'
}

# Global variable to hold translations
_translations = {}
_current_language = 'en'

def load_translations(lang_code: str) -> Dict[str, Any]:
    """
    Load translation strings for the specified language.
    
    Args:
        lang_code: The language code (e.g., 'en', 'nl')
        
    Returns:
        Dictionary of translation strings
    """
    global _translations, _current_language
    
    # Ensure lang_code is a string
    lang_code = str(lang_code) if lang_code is not None else 'en'
    
    # Default to English if the language is not supported
    if lang_code not in LANGUAGES:
        lang_code = 'en'
    
    # Set current language
    _current_language = lang_code
    
    # If translations already loaded, return them
    if lang_code in _translations:
        return _translations[lang_code]
    
    # Define path to translation file
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    translation_file = os.path.join(base_dir, 'translations', f'{lang_code}.json')
    
    # Check if translation file exists
    if not os.path.exists(translation_file):
        # Create empty translation file for language
        if lang_code != 'en':
            # First load English as fallback
            english_file = os.path.join(base_dir, 'translations', 'en.json')
            if os.path.exists(english_file):
                with open(english_file, 'r', encoding='utf-8') as f:
                    _translations['en'] = json.load(f)
            else:
                _translations['en'] = {}
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(translation_file), exist_ok=True)
            
            # Create empty file with same keys as English
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(_translations['en'], f, ensure_ascii=False, indent=2)
            
            # Return English translations as fallback
            return _translations['en']
        else:
            # Create empty English translation file
            os.makedirs(os.path.dirname(translation_file), exist_ok=True)
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            _translations[lang_code] = {}
            return {}
    
    # Load translations from file
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            _translations[lang_code] = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        _translations[lang_code] = {}
    
    # Ensure the translation dictionary exists
    if lang_code not in _translations:
        _translations[lang_code] = {}
    
    return _translations[lang_code]

def set_language(lang_code: Optional[str] = None) -> None:
    """
    Set the current language for the application.
    Simplified with single source of truth.
    
    Args:
        lang_code: The language code (e.g., 'en', 'nl')
    """
    global _current_language
    
    if not lang_code:
        # Single source of truth for language preference
        lang_code = st.session_state.get('language', 'en')
    
    # Ensure lang_code is a string and valid
    lang_code_str = str(lang_code)
    
    # Validate language is supported
    if lang_code_str not in LANGUAGES:
        print(f"SET_LANGUAGE - Invalid language: {lang_code_str}, falling back to 'en'")
        lang_code_str = 'en'
    
    # Log the set operation for debugging
    print(f"SET_LANGUAGE - Setting language to: {lang_code_str}")
    
    # Update module-level global variable
    _current_language = lang_code_str
    
    # Load translations for the language
    load_translations(lang_code_str)
    
    # Single source of truth for language preference
    st.session_state['language'] = lang_code_str

def get_text(key: str, default: Optional[str] = None) -> str:
    """
    Get the translated text for a key.
    
    Args:
        key: The translation key (e.g., 'app.title')
        default: Default text if translation is not found
        
    Returns:
        Translated text
    """
    global _translations, _current_language
    
    # Always use session state as the source of truth for current language
    current_lang = st.session_state.get('language', 'en')
    
    # If translations are not loaded for the current language, load them
    if current_lang not in _translations:
        load_translations(current_lang)
    
    # Update the global variable to match session state
    _current_language = current_lang
    
    # Split the key into parts (e.g., 'app.title' -> ['app', 'title'])
    parts = key.split('.')
    
    # Get the translation dictionary for current language
    lang_dict = _translations.get(current_lang, {})
    
    # Navigate through nested dictionaries based on key parts
    text = None
    current_dict = lang_dict
    for i, part in enumerate(parts):
        # If we're at the last part, get the value
        if i == len(parts) - 1:
            text = current_dict.get(part)
            break
            
        # Navigate to next level if it exists
        if part in current_dict and isinstance(current_dict[part], dict):
            current_dict = current_dict[part]
        else:
            # Break if we can't navigate further
            break
    
    # If not found, try English as fallback
    if text is None and current_lang != 'en':
        if 'en' not in _translations:
            load_translations('en')
            
        # Try to find translation in English
        current_dict = _translations.get('en', {})
        for i, part in enumerate(parts):
            # If we're at the last part, get the value
            if i == len(parts) - 1:
                text = current_dict.get(part)
                break
                
            # Navigate to next level if it exists
            if part in current_dict and isinstance(current_dict[part], dict):
                current_dict = current_dict[part]
            else:
                # Break if we can't navigate further
                break
    
    # If still not found, use default or key itself
    if text is None:
        text = default if default is not None else key
    
    return text

# Shorthand function for get_text
def _(key: str, default: Optional[str] = None) -> str:
    """
    Shorthand function for get_text.
    
    Args:
        key: The translation key (e.g., 'app.title')
        default: Default text if translation is not found
        
    Returns:
        Translated text
    """
    return get_text(key, default)

def language_selector(key_suffix: str = None) -> None:
    """
    Display a language selector in the Streamlit UI.
    Updates the language when changed immediately.
    Now with enhanced refresh mechanism to ensure all translations are applied.
    
    Args:
        key_suffix: A suffix to ensure unique keys for multiple language selectors
                   If None, a random suffix will be generated
    """
    # Use a consistent session-based key to avoid duplicates on re-renders
    if key_suffix is None:
        key_suffix = "default"
    
    # Clean up any old session keys from previous implementation
    old_keys_to_remove = [k for k in st.session_state.keys() if k.startswith('_lang_selector_key_') or k.startswith('_lang_selector_rendered_')]
    for old_key in old_keys_to_remove:
        del st.session_state[old_key]
    
    # Use a simple consistent key based on suffix (no random UUIDs)
    selector_key = f"lang_sel_{key_suffix}"
    current_lang = st.session_state.get('language', 'en')
    
    # Define callback for language change - without st.rerun() to avoid no-op warning
    def on_language_change():
        new_lang = st.session_state[selector_key]
        if new_lang != current_lang:
            print(f"LANGUAGE CHANGE: {current_lang} -> {new_lang}")
            
            # Store language in ALL possible locations for redundant persistence
            st.session_state['language'] = new_lang
            st.session_state['_persistent_language'] = new_lang
            st.session_state['pre_login_language'] = new_lang
            st.session_state['backup_language'] = new_lang
            st.session_state['force_language_after_login'] = new_lang
            
            # Also log the language change for debugging
            print(f"LANGUAGE SELECTOR - Changed language to: {new_lang}")
            
            # Set reload translations flag to force full reinitialization
            st.session_state['reload_translations'] = True
            
            # Reset translations cache completely
            global _translations
            _translations = {}
            
            # Load translations for new language immediately
            set_language(new_lang)
            
            # Force complete reinitialization
            initialize()
            
            # Set a flag to trigger rerun on next app cycle
            st.session_state['_trigger_rerun'] = True
    
    # Create a compact container for the language selector
    with st.container():
        # Use the selectbox with on_change parameter to trigger immediate update
        selected_lang = st.selectbox(
            "🌐 Language / Taal",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES.get(x, x),
            index=list(LANGUAGES.keys()).index(current_lang) if current_lang in LANGUAGES else 0,
            key=selector_key,
            on_change=on_language_change
        )
        
        # Language change will be handled automatically by the selectbox callback
        # No additional button needed since the callback handles the state change

# Initialize translations - COMPLETELY FIXED VERSION
def detect_browser_language() -> str:
    """
    Detect user's preferred language from browser or IP location.
    Returns 'nl' for Netherlands users, 'en' for others.
    """
    try:
        # Try to get user's IP-based location for Netherlands detection
        # This is a simplified implementation - in production, use proper geolocation
        import requests
        
        # Simple IP-based detection (fallback to 'en' on any error)
        try:
            response = requests.get('https://ipapi.co/json/', timeout=2)
            if response.status_code == 200:
                data = response.json()
                country_code = data.get('country_code', '').upper()
                if country_code == 'NL':
                    return 'nl'
        except:
            pass
        
        # Default to English if detection fails
        return 'en'
    except:
        return 'en'

def initialize() -> None:
    """
    Initialize the internationalization module.
    Load translations for the current language.
    Handles both initial app load and language switching.
    """
    global _translations, _current_language
    
    # Simplified language detection and initialization
    current_lang = st.session_state.get('language', 'en')
    
    # Validate the language is supported
    if current_lang not in LANGUAGES:
        print(f"INIT - Invalid language: {current_lang}, falling back to 'en'")
        current_lang = 'en'
    
    # Single source of truth for language preference
    st.session_state['language'] = current_lang
    
    # Completely reset all translations to force reload
    # This is critical for proper translation after auth changes
    _translations = {}  
    
    # Set the current language module variable
    _current_language = current_lang
    
    # Load primary language translations
    load_translations(current_lang)
    
    # Always load English as fallback for missing keys
    if current_lang != 'en':
        load_translations('en')
    
    # Log initialization for debugging
    print(f"INIT - Successfully initialized translations for: {current_lang}")