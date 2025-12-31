import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import no from './locales/no.json'
import sv from './locales/sv.json'
import da from './locales/da.json'
import fi from './locales/fi.json'
import fr from './locales/fr.json'
import de from './locales/de.json'

const resources = {
  en: { translation: en },
  no: { translation: no },
  sv: { translation: sv },
  da: { translation: da },
  fi: { translation: fi },
  fr: { translation: fr },
  de: { translation: de },
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('language') || 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n

