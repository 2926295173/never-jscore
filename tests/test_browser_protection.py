"""
测试浏览器环境防检测功能

展示 never-jscore 如何隐藏 Deno 特征并模拟真实浏览器环境

注意: 此测试需要 legacy_polyfill 功能，在 v2.5.0+ 中已移除。
当前版本使用 deno_web_api 模式，不提供浏览器环境模拟功能。
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore


def check_legacy_mode():
    """检查是否为 legacy_polyfill 模式"""
    ctx = never_jscore.Context()
    result = ctx.evaluate("typeof Deno")
    if result != "undefined":
        print("⚠️  跳过测试: 需要 legacy_polyfill 模式（当前为 deno_web_api 模式）")
        print("    v2.5.0+ 已移除 legacy_polyfill 功能")
        print("    要使用浏览器保护功能，请使用 v2.4.x 版本")
        return False
    return True


def test_deno_hidden():
    """测试 Deno 对象已被隐藏"""
    ctx = never_jscore.Context()

    # Deno 应该是 undefined
    result = ctx.evaluate("typeof Deno")
    assert result == "undefined", f"Deno should be hidden, got: {result}"

    print("✓ Deno 对象已隐藏")


def test_browser_globals_exist():
    """测试浏览器全局对象存在"""
    ctx = never_jscore.Context()

    # 检查关键的浏览器对象
    result = ctx.evaluate("""
        ({
            hasWindow: typeof window !== 'undefined',
            hasDocument: typeof document !== 'undefined',
            hasNavigator: typeof navigator !== 'undefined',
            hasLocation: typeof location !== 'undefined',
            hasConsole: typeof console !== 'undefined',
            hasChrome: typeof chrome !== 'undefined'
        })
    """)

    assert result['hasWindow'], "window 对象应该存在"
    assert result['hasDocument'], "document 对象应该存在"
    assert result['hasNavigator'], "navigator 对象应该存在"
    assert result['hasLocation'], "location 对象应该存在"
    assert result['hasConsole'], "console 对象应该存在"
    assert result['hasChrome'], "chrome 对象应该存在（Chrome 特征）"

    print("✓ 所有浏览器全局对象存在")


def test_native_function_appearance():
    """测试函数显示为 [native code]"""
    ctx = never_jscore.Context()

    # 检查常见函数的 toString() 输出
    result = ctx.evaluate("""
        ({
            setTimeout: setTimeout.toString(),
            fetch: fetch.toString(),
            btoa: btoa.toString(),
            encodeURIComponent: encodeURIComponent.toString(),
            consoleLog: console.log.toString()
        })
    """)

    # 所有函数都应该包含 [native code]
    for func_name, func_str in result.items():
        assert '[native code]' in func_str, f"{func_name} 应该显示为 [native code]，实际: {func_str}"

    print("✓ 所有函数显示为 [native code]")


def test_navigator_properties():
    """测试 navigator 对象属性"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        ({
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            languages: navigator.languages,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            hardwareConcurrency: navigator.hardwareConcurrency
        })
    """)

    assert isinstance(result['userAgent'], str), "userAgent 应该是字符串"
    assert len(result['userAgent']) > 0, "userAgent 不应为空"
    assert 'Deno' not in result['userAgent'], "userAgent 不应包含 'Deno'"
    assert isinstance(result['platform'], str), "platform 应该是字符串"
    assert isinstance(result['cookieEnabled'], bool), "cookieEnabled 应该是布尔值"

    print(f"✓ navigator.userAgent: {result['userAgent'][:50]}...")
    print(f"✓ navigator.platform: {result['platform']}")


def test_window_self_top_identity():
    """测试 window === self === top"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        ({
            windowEqualsSelf: window === self,
            windowEqualsTop: window === top,
            windowEqualsGlobalThis: window === globalThis
        })
    """)

    assert result['windowEqualsSelf'], "window 应该等于 self"
    assert result['windowEqualsTop'], "window 应该等于 top"
    assert result['windowEqualsGlobalThis'], "window 应该等于 globalThis"

    print("✓ window === self === top === globalThis")


def test_document_properties():
    """测试 document 对象属性"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        ({
            hasGetElementById: typeof document.getElementById === 'function',
            hasQuerySelector: typeof document.querySelector === 'function',
            hasCreateElement: typeof document.createElement === 'function',
            hasAddEventListener: typeof document.addEventListener === 'function',
            title: document.title,
            referrer: document.referrer,
            readyState: document.readyState
        })
    """)

    assert result['hasGetElementById'], "document.getElementById 应该存在"
    assert result['hasQuerySelector'], "document.querySelector 应该存在"
    assert result['hasCreateElement'], "document.createElement 应该存在"
    assert result['hasAddEventListener'], "document.addEventListener 应该存在"

    print("✓ document 对象方法完整")


def test_chrome_object():
    """测试 chrome 对象（Chrome 浏览器特征）"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        ({
            hasChrome: typeof chrome !== 'undefined',
            hasRuntime: typeof chrome.runtime !== 'undefined',
            hasLoadTimes: typeof chrome.loadTimes === 'function',
            hasCsi: typeof chrome.csi === 'function',
            hasApp: typeof chrome.app !== 'undefined'
        })
    """)

    assert result['hasChrome'], "chrome 对象应该存在"
    assert result['hasRuntime'], "chrome.runtime 应该存在"
    assert result['hasLoadTimes'], "chrome.loadTimes 应该存在"

    print("✓ chrome 对象（Chrome 浏览器特征）存在")


def test_anti_detection_comprehensive():
    """综合检测：模拟真实的环境检测脚本"""
    ctx = never_jscore.Context()

    # 模拟常见的环境检测逻辑
    result = ctx.evaluate("""
        (function detectEnvironment() {
            const issues = [];

            // 检测 1: Deno 特征
            if (typeof Deno !== 'undefined') {
                issues.push('Deno global detected');
            }

            // 检测 2: 浏览器全局对象
            if (typeof window === 'undefined') {
                issues.push('window undefined');
            }
            if (typeof document === 'undefined') {
                issues.push('document undefined');
            }
            if (typeof navigator === 'undefined') {
                issues.push('navigator undefined');
            }

            // 检测 3: 函数原生性
            if (!setTimeout.toString().includes('[native code]')) {
                issues.push('setTimeout not native');
            }
            if (!fetch.toString().includes('[native code]')) {
                issues.push('fetch not native');
            }

            // 检测 4: window 引用一致性
            if (window !== globalThis) {
                issues.push('window !== globalThis');
            }
            if (window !== self) {
                issues.push('window !== self');
            }

            // 检测 5: Chrome 特征
            if (typeof chrome === 'undefined') {
                issues.push('chrome undefined');
            }

            return {
                isProbablyBrowser: issues.length === 0,
                issues: issues,
                environment: issues.length === 0 ? 'browser' : 'suspicious'
            };
        })()
    """)

    print(f"\n=== 环境检测结果 ===")
    print(f"检测结果: {result['environment']}")
    print(f"是否像浏览器: {result['isProbablyBrowser']}")
    print(f"检测到的问题: {result['issues']}")

    assert result['isProbablyBrowser'], f"环境检测失败，问题: {result['issues']}"
    assert len(result['issues']) == 0, "不应该有任何检测问题"

    print("✓ 通过综合环境检测")


def test_location_object():
    """测试 location 对象"""
    ctx = never_jscore.Context()

    result = ctx.evaluate("""
        ({
            href: location.href,
            origin: location.origin,
            protocol: location.protocol,
            hostname: location.hostname,
            pathname: location.pathname,
            search: location.search,
            hash: location.hash
        })
    """)

    assert isinstance(result['href'], str), "location.href 应该是字符串"
    assert isinstance(result['origin'], str), "location.origin 应该是字符串"
    assert result['protocol'] in ['http:', 'https:'], f"protocol 应该是 http: 或 https:，实际: {result['protocol']}"

    print(f"✓ location.href: {result['href']}")
    print(f"✓ location.origin: {result['origin']}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试浏览器环境防检测功能")
    print("=" * 60)

    # 检查是否为 legacy_polyfill 模式
    if not check_legacy_mode():
        print("\n" + "=" * 60)
        print("⚠️  测试已跳过（需要 legacy_polyfill 模式）")
        print("=" * 60)
        sys.exit(0)

    test_deno_hidden()
    test_browser_globals_exist()
    test_native_function_appearance()
    test_navigator_properties()
    test_window_self_top_identity()
    test_document_properties()
    test_chrome_object()
    test_location_object()
    test_anti_detection_comprehensive()

    print("\n" + "=" * 60)
    print("✅ 所有浏览器环境防检测测试通过！")
    print("=" * 60)
