import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date, language: string) {
  return date.toLocaleDateString(language, { year: 'numeric', month: '2-digit', day: '2-digit' })
}

export const toastConfig: {
  duration?: number
  position:
    | 'top-left'
    | 'top-center'
    | 'top-right'
    | 'bottom-left'
    | 'bottom-center'
    | 'bottom-right'
} = {
  position: 'top-center',
}
