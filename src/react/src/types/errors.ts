class HttpError extends Error {
  code: number;
  constructor(message: string, code: number) {
    super(message);
    Object.setPrototypeOf(this, HttpError.prototype);
    this.code = code;
  }
}

export default HttpError;