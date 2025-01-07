export function withTimeout(asyncFunc, timeout = 20000) {
    return async function (...args) {
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('请求超时，请稍后再试')), timeout)
        );
        return await Promise.race([asyncFunc(...args), timeoutPromise]);
    };
}