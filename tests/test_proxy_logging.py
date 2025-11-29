"""
测试 Proxy 日志系统

展示如何使用 $proxy 监控对象属性访问，用于逆向分析

注意: 此测试需要 legacy_polyfill 功能，在 v2.5.0+ 中已移除。
当前版本使用 deno_web_api 模式，不提供 Proxy logging 功能。
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore


def check_proxy_logging_available():
    """检查是否支持 Proxy logging"""
    ctx = never_jscore.Context()
    try:
        result = ctx.evaluate("typeof $clearProxyLogs")
        if result == "undefined":
            print("⚠️  跳过测试: 需要 legacy_polyfill 模式（当前为 deno_web_api 模式）")
            print("    v2.5.0+ 已移除 legacy_polyfill 功能")
            print("    要使用 Proxy logging 功能，请使用 v2.4.x 版本")
            return False
        return True
    except:
        return False


def test_basic_proxy_logging():
    """测试基本的 Proxy 日志功能"""
    ctx = never_jscore.Context()

    # 创建一个被代理的对象并监控访问
    result = ctx.evaluate("""
        // 清空日志
        $clearProxyLogs();

        // 创建测试对象
        const user = {
            name: 'Alice',
            age: 25,
            getInfo() {
                return `${this.name}, ${this.age}`;
            }
        };

        // 创建代理对象
        const proxiedUser = $proxy(user, { name: 'User' });

        // 访问属性
        const name = proxiedUser.name;
        const age = proxiedUser.age;
        const info = proxiedUser.getInfo();

        // 获取日志
        const logs = $getProxyLogs();

        ({
            name,
            age,
            info,
            logCount: logs.length,
            logs: logs
        })
    """)

    assert result['name'] == 'Alice', "应该能正确读取 name"
    assert result['age'] == 25, "应该能正确读取 age"
    assert result['logCount'] > 0, "应该有日志记录"

    print(f"✓ 记录了 {result['logCount']} 条日志")
    print(f"✓ 访问的属性: name={result['name']}, age={result['age']}")


def test_proxy_filter_logs():
    """测试过滤日志功能"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        $clearProxyLogs();

        const obj = { a: 1, b: 2, c: 3 };
        const proxied = $proxy(obj, { name: 'TestObj' });

        // 访问多个属性
        proxied.a;
        proxied.b;
        proxied.c;

        // 获取所有日志
        const allLogs = $getProxyLogs();

        // 只获取访问 'a' 属性的日志
        const aLogs = $getProxyLogs({ property: 'a' });

        // 只获取 'get' 类型的日志
        const getLogs = $getProxyLogs({ type: 'get' });

        ({
            totalLogs: allLogs.length,
            aLogs: aLogs.length,
            getLogs: getLogs.length
        })
    """)

    assert result['totalLogs'] >= 3, "应该至少有 3 条日志"
    assert result['aLogs'] >= 1, "应该有访问 'a' 的日志"
    assert result['getLogs'] >= 3, "应该有 get 类型的日志"

    print(f"✓ 总日志: {result['totalLogs']}")
    print(f"✓ 属性 'a' 的日志: {result['aLogs']}")
    print(f"✓ GET 类型日志: {result['getLogs']}")


def test_proxy_global_navigator():
    """测试代理全局对象 navigator"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        // 清空日志
        $clearProxyLogs();

        // 代理 navigator 对象
        $proxyGlobal('navigator', { name: 'Navigator' });

        // 访问 navigator 属性（模拟环境检测脚本）
        const ua = navigator.userAgent;
        const platform = navigator.platform;
        const language = navigator.language;
        const cookieEnabled = navigator.cookieEnabled;

        // 获取日志
        const logs = $getProxyLogs({ target: 'Navigator' });

        ({
            logCount: logs.length,
            accessedProperties: logs.map(log => log.property),
            userAgent: ua
        })
    """)

    print(f"\n✓ 拦截到 {result['logCount']} 次 navigator 访问")
    print(f"✓ 访问的属性: {result['accessedProperties']}")
    print(f"✓ User-Agent: {result['userAgent'][:50]}...")


def test_proxy_function_calls():
    """测试函数调用监控"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        $clearProxyLogs();

        // 创建包含方法的对象
        const crypto = {
            encrypt(data, key) {
                return `encrypted:${data}:${key}`;
            },
            decrypt(data, key) {
                return `decrypted:${data}:${key}`;
            }
        };

        // 代理对象
        const proxiedCrypto = $proxy(crypto, {
            name: 'Crypto',
            logCall: true
        });

        // 调用方法
        const encrypted = proxiedCrypto.encrypt('hello', 'secret');
        const decrypted = proxiedCrypto.decrypt('world', 'key123');

        // 获取调用日志
        const callLogs = $getProxyLogs({ type: 'call' });
        const returnLogs = $getProxyLogs({ type: 'return' });

        ({
            encrypted,
            decrypted,
            callCount: callLogs.length,
            returnCount: returnLogs.length,
            calls: callLogs.map(log => ({
                method: log.property,
                args: log.arguments
            })),
            returns: returnLogs.map(log => ({
                method: log.property,
                result: log.result
            }))
        })
    """)

    assert result['callCount'] >= 2, "应该记录到函数调用"
    assert result['returnCount'] >= 2, "应该记录到返回值"

    print(f"\n✓ 拦截到 {result['callCount']} 次函数调用")
    for call in result['calls']:
        print(f"  - {call['method']}({', '.join(map(str, call['args']))})")

    print(f"✓ 拦截到 {result['returnCount']} 个返回值")
    for ret in result['returns']:
        print(f"  - {ret['method']} => {ret['result']}")


def test_proxy_property_write():
    """测试属性写入监控"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        $clearProxyLogs();

        const config = { api: 'https://api.example.com', token: '' };
        const proxied = $proxy(config, { name: 'Config', logSet: true });

        // 写入属性
        proxied.token = 'abc123';
        proxied.api = 'https://new-api.example.com';

        // 获取 set 日志
        const setLogs = $getProxyLogs({ type: 'set' });

        ({
            setCount: setLogs.length,
            sets: setLogs.map(log => ({
                property: log.property,
                value: log.value
            })),
            finalToken: proxied.token,
            finalApi: proxied.api
        })
    """)

    assert result['setCount'] >= 2, "应该记录属性写入"
    assert result['finalToken'] == 'abc123', "token 应该被正确设置"

    print(f"\n✓ 拦截到 {result['setCount']} 次属性写入")
    for set_op in result['sets']:
        print(f"  - {set_op['property']} = {set_op['value']}")


def test_reverse_engineering_scenario():
    """逆向工程场景：监控加密函数的调用"""
    ctx = never_jscore.Context()

    # 模拟一个加密库
    ctx.compile("""
        // 模拟目标网站的加密库
        const CryptoLib = {
            generateKey() {
                return Math.random().toString(36).substring(7);
            },

            encrypt(data, key) {
                // 简化的加密逻辑
                return btoa(data + ':' + key);
            },

            sign(data, secret) {
                // 简化的签名逻辑
                return md5(data + secret);
            }
        };
    """)

    # 使用 Proxy 监控加密库的调用
    result = ctx.evaluate("""
        $clearProxyLogs();

        // 代理加密库
        const ProxiedCrypto = $proxy(CryptoLib, {
            name: 'CryptoLib',
            logCall: true
        });

        // 模拟目标脚本调用加密函数
        const key = ProxiedCrypto.generateKey();
        const encrypted = ProxiedCrypto.encrypt('user=admin&pass=123', key);
        const signature = ProxiedCrypto.sign(encrypted, 'SECRET_KEY');

        // 分析日志
        const calls = $getProxyLogs({ type: 'call' });
        const returns = $getProxyLogs({ type: 'return' });

        ({
            totalCalls: calls.length,
            callSequence: calls.map(log => log.property),
            encryptArgs: calls.find(log => log.property === 'encrypt')?.arguments,
            signArgs: calls.find(log => log.property === 'sign')?.arguments,
            results: {
                key,
                encrypted,
                signature
            }
        })
    """)

    print(f"\n=== 逆向分析：加密库调用监控 ===")
    print(f"✓ 捕获到 {result['totalCalls']} 次加密函数调用")
    print(f"✓ 调用序列: {' -> '.join(result['callSequence'])}")
    print(f"✓ encrypt() 参数: {result['encryptArgs']}")
    print(f"✓ sign() 参数: {result['signArgs']}")
    print(f"✓ 最终签名: {result['results']['signature']}")


def test_enable_disable_logging():
    """测试启用/禁用日志"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        $clearProxyLogs();

        const obj = { count: 0 };
        const proxied = $proxy(obj, { name: 'Counter' });

        // 启用日志时访问
        proxied.count;
        const logs1 = $getProxyLogs().length;

        // 禁用日志
        $setProxyLogging(false);
        proxied.count;
        proxied.count;
        const logs2 = $getProxyLogs().length;

        // 重新启用日志
        $setProxyLogging(true);
        proxied.count;
        const logs3 = $getProxyLogs().length;

        ({
            logsWithEnabled: logs1,
            logsAfterDisable: logs2,
            logsAfterReEnable: logs3
        })
    """)

    assert result['logsWithEnabled'] > 0, "启用时应该有日志"
    assert result['logsAfterDisable'] == result['logsWithEnabled'], "禁用时不应增加日志"
    assert result['logsAfterReEnable'] > result['logsAfterDisable'], "重新启用后应该增加日志"

    print(f"\n✓ 启用日志: {result['logsWithEnabled']} 条")
    print(f"✓ 禁用期间: {result['logsAfterDisable']} 条（未增加）")
    print(f"✓ 重新启用: {result['logsAfterReEnable']} 条（已增加）")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 Proxy 日志系统")
    print("=" * 60)

    # 检查是否支持 Proxy logging
    if not check_proxy_logging_available():
        print("\n" + "=" * 60)
        print("⚠️  测试已跳过（需要 legacy_polyfill 模式）")
        print("=" * 60)
        sys.exit(0)

    test_basic_proxy_logging()
    test_proxy_filter_logs()
    test_proxy_global_navigator()
    test_proxy_function_calls()
    test_proxy_property_write()
    test_reverse_engineering_scenario()
    test_enable_disable_logging()

    print("\n" + "=" * 60)
    print("✅ 所有 Proxy 日志测试通过！")
    print("=" * 60)
