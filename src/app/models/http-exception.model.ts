class HttpException extends Error {
  errorCode: number;
  constructor(
    errorCode: number,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    public readonly message: string | any,
  ) {
    super(message);
    this.errorCode = errorCode;
  }
}

export default HttpException;
