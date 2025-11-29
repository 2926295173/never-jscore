#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步测试 jsdom 的依赖加载
"""

import sys
import io
import never_jscore
import time


print("=" * 60)
print("Test: jsdom dependencies loading step by step")
print("=" * 60)

ctx = never_jscore.Context(enable_node_compat=True)

# 测试每个依赖
dependencies = [
    ("path", "const path = require('path'); 'ok'"),
    ("fs", "const fs = require('fs'); 'ok'"),
    ("fs.promises", "const fs = require('fs'); typeof fs.promises"),
    ("vm", "const vm = require('vm'); 'ok'"),
    ("tough-cookie", "const tc = require('tough-cookie'); 'ok'"),
    ("html-encoding-sniffer", "const hes = require('html-encoding-sniffer'); 'ok'"),
    ("whatwg-url", "const wu = require('whatwg-url'); 'ok'"),
    ("whatwg-encoding", "const we = require('whatwg-encoding'); 'ok'"),
    ("whatwg-mimetype", "const wm = require('whatwg-mimetype'); 'ok'"),
]

for name, code in dependencies:
    print(f"\nTesting: {name}")
    start = time.time()

    try:
        result = ctx.evaluate(code)
        elapsed = time.time() - start
        print(f"  ✓ SUCCESS in {elapsed:.3f}s - result: {result}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ✗ FAILED after {elapsed:.3f}s")
        print(f"  Error: {e}")
        break

print("\n" + "=" * 60)
print("Now testing jsdom main entry:")
print("=" * 60)

code_jsdom = """
try {
    // Add detailed logging
    console.log('[DEBUG] Starting jsdom require...');

    const startTime = Date.now();

    // Require jsdom
    const jsdomModule = require('jsdom');

    const elapsed = Date.now() - startTime;
    console.log(`[DEBUG] jsdom required in ${elapsed}ms`);

    ({
        success: true,
        elapsed: elapsed,
        hasJSDOM: typeof jsdomModule.JSDOM !== 'undefined',
        keys: Object.keys(jsdomModule)
    })
} catch (e) {
    ({
        success: false,
        error: e.message,
        stack: e.stack
    })
}
"""

start = time.time()
try:
    result = ctx.evaluate(code_jsdom)
    elapsed = time.time() - start

    if result.get('success'):
        print(f"✓ jsdom loaded in {elapsed:.3f}s (JS: {result.get('elapsed')}ms)")
        print(f"  Has JSDOM: {result.get('hasJSDOM')}")
        print(f"  Exports: {result.get('keys')}")
    else:
        print(f"✗ jsdom failed after {elapsed:.3f}s")
        print(f"  Error: {result.get('error')}")
        if result.get('stack'):
            print(f"  Stack: {result.get('stack')[:500]}")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Exception after {elapsed:.3f}s")
    print(f"  Error: {e}")

print("=" * 60)
