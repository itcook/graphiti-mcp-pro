export function formatUsageValue(value: number) {
  if (value === null || Number.isNaN(value)) {
    return NaN
  }

  if (value >= 1e12) {
    return `${(value / 1e12).toFixed()}T`
  } else if (value >= 1e9) {
    return `${(value / 1e9).toFixed()}B`
  } else if (value >= 1e6) {
    return `${(value / 1e6).toFixed()}M`
  } else if (value >= 1e3) {
    return `${(value / 1e3).toFixed()}K`
  } else {
    return value.toString()
  }
}
