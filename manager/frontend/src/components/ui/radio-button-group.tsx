import * as React from 'react'
import { cn } from '@/lib/utils'

export type RadioButtonGroupOption = {
  label: string
  value: any
}

export interface RadioButtonGroupProps {
  id?: string
  value?: any
  onChange?: (value: any) => void
  options: RadioButtonGroupOption[]
  className?: string
}

export default function RadioButtonGroup({
  id,
  value,
  onChange,
  options,
  className,
}: RadioButtonGroupProps) {
  const randomId = Math.random().toString(36).substring(2, 9)
  const [selectedValue, setSelectedValue] = React.useState(value)

  const handleChange = (option: RadioButtonGroupOption) => {
    setSelectedValue(option.value)
    onChange?.(option.value)
  }
  return (
    <div
      id={id}
      className={cn(
        'flex items-center w-fit bg-transparent dark:bg-input/30 text-sm shadow-xs transition-[color,box-shadow] outline-none',
        className
      )}>
      {options.map((option) => (
        <label
          key={option.value}
          className={cn(
            'relative inline-block m-0 h-9 px-4 py-1 border border-input mr-[-1px] bg-muted text-muted-foreground',
            'first:rounded-l-md',
            'last:rounded-r-md',
            'dark:border-gray-500/30',
            {
              'bg-background text-foreground z-10 dark:border-gray-500/75':
                selectedValue === option.value,
            }
          )}
          onClick={() => handleChange(option)}>
          <span className='absolute -z-10'>
            <input
              type='radio'
              name={`radio-group-${randomId}`}
              value={option.value}
              checked={selectedValue === option.value}
              onChange={() => handleChange(option)}
              className='w-0 h-0 opacity-0 pointer-events-none'
            />
          </span>
          <div className='inline-flex items-center justify-center w-full h-full'>
            <span>{option.label}</span>
          </div>
        </label>
      ))}
    </div>
  )
}
