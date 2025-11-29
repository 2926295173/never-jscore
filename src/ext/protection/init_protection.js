// Unified Browser Protection for never-jscore
// Makes all Web APIs appear as native browser implementations
// This is the ONLY protection file - all protection logic is centralized here

(() => {
    'use strict';

    // ========================================================================
    // Step 1: Store original functions before any modification
    // ========================================================================
    const OriginalFunction = Function;
    const originalFunctionToString = Function.prototype.toString;
    const originalObjectKeys = Object.keys;
    const originalGetOwnPropertyNames = Object.getOwnPropertyNames;
    const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
    const originalGetOwnPropertyDescriptors = Object.getOwnPropertyDescriptors;
    const originalReflectOwnKeys = Reflect.ownKeys;
    const originalGetPrototypeOf = Object.getPrototypeOf;
    const originalDefineProperty = Object.defineProperty;

    // ========================================================================
    // Step 2: Hide Deno internals (keep internal reference for ops)
    // ========================================================================
    if (typeof Deno !== 'undefined') {
        const __realDeno__ = Deno;

        // Store real Deno for internal ops (non-enumerable, hidden name)
        try {
            originalDefineProperty(globalThis, '__deno_internal__', {
                value: __realDeno__,
                writable: false,
                enumerable: false,
                configurable: false
            });
        } catch (e) {
            // Already exists
        }

        // Hide Deno from enumeration
        try {
            originalDefineProperty(globalThis, 'Deno', {
                enumerable: false,
                configurable: false
            });
        } catch (e) {
            // Can't modify
        }
    }

    // ========================================================================
    // Step 3: Native code protection - Unified implementation
    // ========================================================================
    const protectedFunctions = new WeakSet();
    const nativeCodeString = (name) => `function ${name || ''}() { [native code] }`;

    /**
     * Make a function appear as native code
     * Uses defineProperty approach (more reliable than Proxy)
     */
    function makeNative(fn, name) {
        if (!fn || typeof fn !== 'function') return fn;
        if (protectedFunctions.has(fn)) return fn;

        const targetName = name || fn.name || 'anonymous';

        try {
            // Override toString
            originalDefineProperty(fn, 'toString', {
                value: function() {
                    return nativeCodeString(targetName);
                },
                writable: false,
                enumerable: false,
                configurable: true
            });

            // Fix name if needed
            if (name && fn.name !== name) {
                originalDefineProperty(fn, 'name', {
                    value: name,
                    writable: false,
                    enumerable: false,
                    configurable: true
                });
            }

            protectedFunctions.add(fn);
        } catch (e) {
            // Some built-in functions can't be modified
        }

        return fn;
    }

    /**
     * Protect a class constructor and all its prototype methods
     */
    function protectClass(ClassConstructor, className) {
        if (!ClassConstructor || typeof ClassConstructor !== 'function') return ClassConstructor;

        // Protect constructor
        makeNative(ClassConstructor, className);

        // Protect prototype methods
        if (ClassConstructor.prototype) {
            const proto = ClassConstructor.prototype;

            // Make constructor property non-enumerable
            try {
                originalDefineProperty(proto, 'constructor', {
                    value: ClassConstructor,
                    writable: true,
                    enumerable: false,
                    configurable: true
                });
            } catch (e) {}

            // Protect all methods
            const methodNames = originalGetOwnPropertyNames(proto);
            for (const methodName of methodNames) {
                if (methodName === 'constructor') continue;

                try {
                    const descriptor = originalGetOwnPropertyDescriptor(proto, methodName);
                    if (descriptor && typeof descriptor.value === 'function') {
                        makeNative(descriptor.value, methodName);
                    }
                    // Also protect getters/setters
                    if (descriptor && typeof descriptor.get === 'function') {
                        makeNative(descriptor.get, `get ${methodName}`);
                    }
                    if (descriptor && typeof descriptor.set === 'function') {
                        makeNative(descriptor.set, `set ${methodName}`);
                    }
                } catch (e) {}
            }
        }

        // Protect static methods
        const staticNames = originalGetOwnPropertyNames(ClassConstructor);
        for (const name of staticNames) {
            if (['prototype', 'length', 'name', 'toString'].includes(name)) continue;
            try {
                const descriptor = originalGetOwnPropertyDescriptor(ClassConstructor, name);
                if (descriptor && typeof descriptor.value === 'function') {
                    makeNative(descriptor.value, name);
                }
            } catch (e) {}
        }

        return ClassConstructor;
    }

    // ========================================================================
    // Step 4: Override Function.prototype.toString globally
    // ========================================================================
    Function.prototype.toString = function() {
        // If this function is protected, return native code string
        if (protectedFunctions.has(this)) {
            return nativeCodeString(this.name);
        }
        // Otherwise use original toString
        return originalFunctionToString.call(this);
    };
    protectedFunctions.add(Function.prototype.toString);

    // ========================================================================
    // Step 5: Protect all Web APIs
    // ========================================================================

    // Complete list of all global APIs to protect
    const globalClasses = [
        // Encoding
        'TextEncoder', 'TextDecoder', 'TextEncoderStream', 'TextDecoderStream',

        // URL
        'URL', 'URLSearchParams', 'URLPattern',

        // Events
        'Event', 'EventTarget', 'CustomEvent', 'ErrorEvent', 'CloseEvent',
        'MessageEvent', 'PromiseRejectionEvent', 'ProgressEvent',

        // Abort
        'AbortController', 'AbortSignal',

        // Fetch API
        'Headers', 'Request', 'Response', 'FormData',

        // File API
        'Blob', 'File', 'FileReader',

        // Streams
        'ReadableStream', 'WritableStream', 'TransformStream',
        'ReadableStreamDefaultReader', 'WritableStreamDefaultWriter',
        'ReadableByteStreamController', 'ReadableStreamBYOBReader',
        'ReadableStreamBYOBRequest', 'ReadableStreamDefaultController',
        'TransformStreamDefaultController', 'WritableStreamDefaultController',
        'ByteLengthQueuingStrategy', 'CountQueuingStrategy',

        // Compression
        'CompressionStream', 'DecompressionStream',

        // Crypto
        'Crypto', 'CryptoKey', 'SubtleCrypto',

        // Performance
        'Performance', 'PerformanceEntry', 'PerformanceMark', 'PerformanceMeasure',

        // Storage
        'Storage',

        // Message
        'MessageChannel', 'MessagePort', 'BroadcastChannel',

        // Image
        'ImageData',

        // Exception
        'DOMException',

        // XMLHttpRequest
        'XMLHttpRequest',

        // Console
        'Console',
    ];

    const globalFunctions = [
        // Base64
        'atob', 'btoa',

        // Timers
        'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval',
        'queueMicrotask',

        // Fetch
        'fetch',

        // Events
        'addEventListener', 'removeEventListener', 'dispatchEvent', 'reportError',

        // Structured Clone
        'structuredClone',

        // never_jscore hooks (make them look native too)
        '$return', '$exit', '$terminate', '$storeResult',
        '__neverjscore_return__', '__saveAndTerminate__', '__getDeno',
    ];

    // Protect classes
    for (const className of globalClasses) {
        if (typeof globalThis[className] === 'function') {
            try {
                protectClass(globalThis[className], className);
            } catch (e) {}
        }
    }

    // Protect functions
    for (const funcName of globalFunctions) {
        if (typeof globalThis[funcName] === 'function') {
            try {
                makeNative(globalThis[funcName], funcName);
            } catch (e) {}
        }
    }

    // Protect crypto object methods
    if (typeof crypto !== 'undefined') {
        makeNative(crypto.getRandomValues, 'getRandomValues');
        makeNative(crypto.randomUUID, 'randomUUID');
        if (crypto.subtle) {
            const subtleMethods = ['encrypt', 'decrypt', 'sign', 'verify', 'digest',
                'generateKey', 'deriveKey', 'deriveBits', 'importKey', 'exportKey',
                'wrapKey', 'unwrapKey'];
            for (const method of subtleMethods) {
                if (typeof crypto.subtle[method] === 'function') {
                    makeNative(crypto.subtle[method], method);
                }
            }
        }
    }

    // Protect console methods
    if (typeof console !== 'undefined') {
        const consoleMethods = ['log', 'info', 'warn', 'error', 'debug', 'trace',
            'dir', 'dirxml', 'table', 'count', 'countReset', 'group', 'groupCollapsed',
            'groupEnd', 'time', 'timeEnd', 'timeLog', 'assert', 'clear', 'profile',
            'profileEnd', 'timeStamp'];
        for (const method of consoleMethods) {
            if (typeof console[method] === 'function') {
                makeNative(console[method], method);
            }
        }
    }

    // Protect performance methods
    if (typeof performance !== 'undefined') {
        const perfMethods = ['now', 'mark', 'measure', 'clearMarks', 'clearMeasures',
            'getEntries', 'getEntriesByName', 'getEntriesByType', 'toJSON'];
        for (const method of perfMethods) {
            if (typeof performance[method] === 'function') {
                makeNative(performance[method], method);
            }
        }
    }

    // ========================================================================
    // Step 6: Protect reflection APIs
    // ========================================================================

    // Hidden properties that should not be exposed
    const hiddenGlobalProps = ['Deno', '__deno_core__', '__deno_internal__',
        '__NEVER_JSCORE_LOGGING__'];

    // Object.keys - hide Deno-related properties
    Object.keys = function(obj) {
        const keys = originalObjectKeys(obj);
        if (obj === globalThis) {
            return keys.filter(key => !hiddenGlobalProps.includes(key));
        }
        return keys;
    };
    makeNative(Object.keys, 'keys');

    // Object.getOwnPropertyNames - hide Deno-related properties
    Object.getOwnPropertyNames = function(obj) {
        const names = originalGetOwnPropertyNames(obj);
        if (obj === globalThis) {
            return names.filter(name => !hiddenGlobalProps.includes(name));
        }
        return names;
    };
    makeNative(Object.getOwnPropertyNames, 'getOwnPropertyNames');

    // Object.getOwnPropertyDescriptors - hide Deno-related properties
    Object.getOwnPropertyDescriptors = function(obj) {
        const descriptors = originalGetOwnPropertyDescriptors(obj);
        if (obj === globalThis) {
            for (const prop of hiddenGlobalProps) {
                delete descriptors[prop];
            }
        }
        return descriptors;
    };
    makeNative(Object.getOwnPropertyDescriptors, 'getOwnPropertyDescriptors');

    // Reflect.ownKeys - hide Deno-related properties
    Reflect.ownKeys = function(obj) {
        const keys = originalReflectOwnKeys(obj);
        if (obj === globalThis) {
            return keys.filter(key =>
                typeof key !== 'string' || !hiddenGlobalProps.includes(key)
            );
        }
        return keys;
    };
    makeNative(Reflect.ownKeys, 'ownKeys');

    // ========================================================================
    // Step 7: Error.stack cleanup
    // ========================================================================
    const originalErrorConstructor = Error;
    const stackCleanPatterns = [
        /\s+at\s+.*ext:.*\n?/g,
        /\s+at\s+.*deno:.*\n?/g,
        /\s+at\s+.*deno_.*\n?/g,
        /\s+at\s+.*__deno.*\n?/g,
        /\s+at\s+.*never_jscore.*\n?/g,
    ];

    function cleanStack(stack) {
        if (!stack) return stack;
        let cleaned = stack;
        for (const pattern of stackCleanPatterns) {
            cleaned = cleaned.replace(pattern, '');
        }
        // Remove multiple consecutive newlines
        cleaned = cleaned.replace(/\n{3,}/g, '\n\n');
        return cleaned;
    }

    // Override Error.prepareStackTrace if available (V8)
    if (typeof Error.captureStackTrace === 'function') {
        const originalCaptureStackTrace = Error.captureStackTrace;
        Error.captureStackTrace = function(targetObject, constructorOpt) {
            originalCaptureStackTrace.call(this, targetObject, constructorOpt);
            if (targetObject.stack) {
                targetObject.stack = cleanStack(targetObject.stack);
            }
        };
        makeNative(Error.captureStackTrace, 'captureStackTrace');
    }

    // Override stack property on Error.prototype
    const originalStackDescriptor = originalGetOwnPropertyDescriptor(Error.prototype, 'stack');
    if (originalStackDescriptor) {
        originalDefineProperty(Error.prototype, 'stack', {
            get: function() {
                const stack = originalStackDescriptor.get ?
                    originalStackDescriptor.get.call(this) :
                    this._stack;
                return cleanStack(stack);
            },
            set: function(value) {
                if (originalStackDescriptor.set) {
                    originalStackDescriptor.set.call(this, value);
                } else {
                    this._stack = value;
                }
            },
            enumerable: false,
            configurable: true
        });
    }

    // ========================================================================
    // Step 8: Symbol.toStringTag protection
    // ========================================================================

    // Ensure objects have correct toStringTag
    const toStringTagMap = {
        'crypto': 'Crypto',
        'performance': 'Performance',
        'console': 'console',
        'localStorage': 'Storage',
        'sessionStorage': 'Storage',
    };

    for (const [objName, tag] of Object.entries(toStringTagMap)) {
        const obj = globalThis[objName];
        if (obj && typeof obj === 'object') {
            try {
                originalDefineProperty(obj, Symbol.toStringTag, {
                    value: tag,
                    writable: false,
                    enumerable: false,
                    configurable: true
                });
            } catch (e) {}
        }
    }

    // ========================================================================
    // Step 9: Freeze critical protections
    // ========================================================================
    Object.freeze(Object.keys);
    Object.freeze(Object.getOwnPropertyNames);
    Object.freeze(Object.getOwnPropertyDescriptors);
    Object.freeze(Reflect.ownKeys);
    Object.freeze(Function.prototype.toString);

})();
