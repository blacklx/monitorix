/**
 * Copyright 2024 Monitorix Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { format, formatDistanceToNow, formatRelative } from 'date-fns'
import { enUS, nb, sv, da, fi, fr, de } from 'date-fns/locale'

// Map language codes to date-fns locales
const localeMap = {
  en: enUS,
  no: nb,
  sv: sv,
  da: da,
  fi: fi,
  fr: fr,
  de: de,
}

/**
 * Get the current locale based on i18n language
 */
const getLocale = () => {
  const language = localStorage.getItem('language') || 'en'
  return localeMap[language] || enUS
}

/**
 * Format a date string to a localized date and time string
 * @param {string|Date} dateString - Date string or Date object
 * @param {string} formatStr - Format string (default: 'PPpp' - date and time)
 * @returns {string} Formatted date string
 */
export const formatDateTime = (dateString, formatStr = 'PPpp') => {
  if (!dateString) return ''
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString
    if (isNaN(date.getTime())) return ''
    return format(date, formatStr, { locale: getLocale() })
  } catch (error) {
    console.error('Error formatting date:', error)
    return ''
  }
}

/**
 * Format a date string to a localized date string (without time)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString) => {
  return formatDateTime(dateString, 'PP')
}

/**
 * Format a date string to a localized time string (without date)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted time string
 */
export const formatTime = (dateString) => {
  return formatDateTime(dateString, 'p')
}

/**
 * Format a date string to a localized short date string
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted short date string
 */
export const formatShortDate = (dateString) => {
  return formatDateTime(dateString, 'P')
}

/**
 * Format a date string to a localized short date and time string
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted short date and time string
 */
export const formatShortDateTime = (dateString) => {
  return formatDateTime(dateString, 'Pp')
}

/**
 * Format a date string to a relative time string (e.g., "2 hours ago")
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return ''
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString
    if (isNaN(date.getTime())) return ''
    return formatDistanceToNow(date, { addSuffix: true, locale: getLocale() })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return ''
  }
}

/**
 * Format a date string to a relative date string (e.g., "today at 2:30 PM")
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Relative date string
 */
export const formatRelativeDate = (dateString) => {
  if (!dateString) return ''
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString
    if (isNaN(date.getTime())) return ''
    return formatRelative(date, new Date(), { locale: getLocale() })
  } catch (error) {
    console.error('Error formatting relative date:', error)
    return ''
  }
}

/**
 * Format a date string for use in filenames (ISO format)
 * @param {string|Date} dateString - Date string or Date object (optional, defaults to now)
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export const formatDateForFilename = (dateString = null) => {
  const date = dateString ? (typeof dateString === 'string' ? new Date(dateString) : dateString) : new Date()
  return format(date, 'yyyy-MM-dd')
}

