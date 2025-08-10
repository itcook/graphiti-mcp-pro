class Logger {
  private isDev: boolean

  constructor() {
    this.isDev = import.meta.env.DEV
  }

  public log(...message: any) {
    if (this.isDev) {
      console.log(...message)
    }
  }

  public debug(...message: any) {
    if (this.isDev) {
      console.debug(...message)
    }
  }

  public info(...message: any) {
    if (this.isDev) {
      console.info(...message)
    }
  }

  public warn(...message: any) {
    if (this.isDev) {
      console.warn(...message)
    }
  }

  public error(...message: any) {
    if (this.isDev) {
      console.error(...message)
    }
  }
}

export const logger = new Logger()
